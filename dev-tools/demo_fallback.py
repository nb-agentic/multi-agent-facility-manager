#!/usr/bin/env python3
"""
IntelliCenter Fallback Demo Mode
Emergency demo mode that plays pre-recorded, deterministic responses without requiring LLMs.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from intellicenter.core.event_bus import EventBus


class FallbackDemoRunner:
    """Fallback demo runner that publishes pre-recorded event sequences."""
    
    def __init__(self, event_bus: EventBus, scenario: str, script_path: Optional[str] = None, 
                 speed: float = 1.0, repeat: int = 1):
        self.event_bus = event_bus
        self.scenario = scenario
        self.script_path = script_path
        self.speed = speed
        self.repeat = repeat
        self.event_sequence = []
        self.published_events = 0
        self.start_time = None
        self.logger = logging.getLogger(__name__)
        
        # Default script directory
        self.script_dir = Path(__file__).parent / "responses"
        
    async def load_script(self) -> List[Dict[str, Any]]:
        """Load the event sequence from script file."""
        if self.script_path:
            script_file = Path(self.script_path)
        else:
            script_file = self.script_dir / f"{self.scenario}.json"
        
        if not script_file.exists():
            raise FileNotFoundError(f"Script file not found: {script_file}")
        
        try:
            with open(script_file, 'r') as f:
                sequence = json.load(f)
            self.logger.info(f"Loaded script from {script_file}")
            return sequence
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in script file {script_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading script: {e}")
    
    async def run(self):
        """Execute the fallback demo scenario."""
        self.start_time = time.time()
        
        try:
            # Load event sequence
            self.event_sequence = await self.load_script()
            
            self.logger.info(f"Starting fallback demo: {self.scenario}")
            self.logger.info(f"Speed multiplier: {self.speed}x, Repeat: {self.repeat}")
            
            # Run the scenario multiple times if requested
            for run_num in range(1, self.repeat + 1):
                if run_num > 1:
                    self.logger.info(f"Starting repeat run #{run_num}")
                
                await self._execute_run(run_num)
                
                if run_num < self.repeat:
                    # Small delay between runs
                    await asyncio.sleep(1.0)
            
            # Print summary
            total_duration = time.time() - self.start_time
            self.logger.info(f"Demo completed: {self.published_events} events published in {total_duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Demo execution failed: {e}")
            raise
    
    async def _execute_run(self, run_num: int):
        """Execute a single run of the event sequence."""
        for i, event in enumerate(self.event_sequence):
            delay_ms = event.get("delay_ms", 0)
            topic = event.get("topic")
            payload = event.get("payload", {})
            
            if not topic:
                self.logger.warning(f"Skipping event without topic: {event}")
                continue
            
            # Apply speed multiplier to delay
            adjusted_delay = delay_ms / self.speed if self.speed > 0 else 0
            
            # Wait for the adjusted delay
            if adjusted_delay > 0:
                await asyncio.sleep(adjusted_delay / 1000.0)
            
            # Publish the event
            try:
                await self.event_bus.publish(topic, json.dumps(payload))
                self.published_events += 1
                
                # Log important events
                if topic.startswith("scenario."):
                    self.logger.info(f"Scenario event: {topic} - {payload}")
                elif any(topic.startswith(prefix) for prefix in ["hvac.", "power.", "security.", "network.", "facility."]):
                    self.logger.info(f"Agent event: {topic}")
                
            except Exception as e:
                self.logger.error(f"Failed to publish event {topic}: {e}")


class WebSocketServerManager:
    """Manages WebSocket server startup and shutdown."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.server_task = None
        self.server = None
        
    async def start_server(self) -> bool:
        """Start WebSocket server in background if not already running."""
        try:
            from intellicenter.api.websocket_server import WebSocketServer
            
            # Check if server is already running on this port
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{self.host}:{self.port}/health") as response:
                        if response.status == 200:
                            self.logger.info(f"WebSocket server already running on {self.host}:{self.port}")
                            return True
            except:
                pass
            
            # Start server in background
            self.server = WebSocketServer(
                event_bus=EventBus(),
                host=self.host,
                port=self.port
            )
            
            self.server_task = asyncio.create_task(self._run_server())
            self.logger.info(f"Started WebSocket server on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def _run_server(self):
        """Run the WebSocket server."""
        try:
            await self.server.start()
        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            self.server_task = None


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_available_scenarios() -> List[str]:
    """Get list of available scenarios."""
    script_dir = Path(__file__).parent / "responses"
    if not script_dir.exists():
        return []
    
    return [f.stem for f in script_dir.glob("*.json")]


async def main():
    """Main entry point for the fallback demo."""
    parser = argparse.ArgumentParser(
        description="IntelliCenter Fallback Demo Mode - Pre-recorded demo without LLMs"
    )
    
    parser.add_argument(
        "--scenario", 
        required=True,
        choices=["cooling_crisis", "security_breach", "energy_optimization", "routine_maintenance"],
        help="Scenario to run"
    )
    
    parser.add_argument(
        "--script",
        help="Path to custom script file (JSON format)"
    )
    
    parser.add_argument(
        "--ws-port",
        type=int,
        default=8000,
        help="WebSocket server port (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="WebSocket server host (default: localhost)"
    )
    
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed multiplier for demo timing (default: 1.0)"
    )
    
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat the scenario (default: 1)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Handle list scenarios
    if args.list_scenarios:
        scenarios = get_available_scenarios()
        print("Available scenarios:")
        for scenario in scenarios:
            print(f"  - {scenario}")
        return
    
    # Validate arguments
    if args.speed <= 0:
        logger.error("Speed must be greater than 0")
        sys.exit(1)
    
    if args.repeat < 1:
        logger.error("Repeat must be at least 1")
        sys.exit(1)
    
    # Initialize event bus
    event_bus = EventBus()
    await event_bus.start()
    
    # WebSocket server manager
    ws_manager = WebSocketServerManager(host=args.host, port=args.ws_port)
    
    try:
        # Start WebSocket server if requested
        if args.ws_port:
            success = await ws_manager.start_server()
            if not success:
                logger.warning("Failed to start WebSocket server, continuing without it")
        
        # Create and run demo
        runner = FallbackDemoRunner(
            event_bus=event_bus,
            scenario=args.scenario,
            script_path=args.script,
            speed=args.speed,
            repeat=args.repeat
        )
        
        await runner.run()
        
        # Print final summary
        total_duration = time.time() - runner.start_time
        print(f"\n🎯 Fallback Demo Summary:")
        print(f"   Scenario: {args.scenario}")
        print(f"   Events Published: {runner.published_events}")
        print(f"   Duration: {total_duration:.2f}s")
        print(f"   Speed: {args.speed}x")
        print(f"   Repeats: {args.repeat}")
        print(f"   Status: ✅ Success")
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        await event_bus.stop()
        await ws_manager.stop_server()


if __name__ == "__main__":
    asyncio.run(main())