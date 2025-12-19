#!/usr/bin/env python3
"""
IntelliCenter Demo Launcher - Single-command demo runner for all scenarios

Provides both live and fallback modes for rehearsing demo scenarios with
comprehensive reporting and CI-friendly timing constraints.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from intellicenter.core.event_bus import EventBus
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator, ScenarioType
from dev_tools.demo_fallback import FallbackDemoRunner, WebSocketServerManager


class DemoLauncher:
    """Main demo launcher coordinating both live and fallback modes."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.scenario_orchestrator = ScenarioOrchestrator(self.event_bus)
        self.fallback_runner = None
        self.ws_manager = None
        self.start_time = None
        self.event_counts = {
            "lifecycle_events": 0,
            "agent_events": 0,
            "coordination_events": 0
        }
        
        # Setup event counting
        self._setup_event_counters()
    
    def _setup_event_counters(self):
        """Setup event counters for monitoring scenario execution."""
        lifecycle_topics = [
            "demo.scenario.start", "demo.scenario.initialized", "demo.scenario.completed",
            "demo.scenario.failed", "demo.scenario.reset", "demo.scenario.paused",
            "demo.scenario.resumed", "demo.scenario.stopped"
        ]
        
        agent_topics = [
            "hvac.cooling.decision", "power.optimization.decision", 
            "security.assessment.decision", "network.assessment.decision"
        ]
        
        coordination_topics = [
            "facility.coordination.directive", "facility.coordination.scenario_orchestration",
            "facility.coordination.scenario"
        ]
        
        async def event_counter(message: str):
            try:
                data = json.loads(message) if isinstance(message, str) else message
                topic = data.get("topic", data.get("type", ""))
                
                if any(topic.startswith(prefix) for prefix in lifecycle_topics):
                    self.event_counts["lifecycle_events"] += 1
                elif any(topic.startswith(prefix) for prefix in agent_topics):
                    self.event_counts["agent_events"] += 1
                elif any(topic.startswith(prefix) for prefix in coordination_topics):
                    self.event_counts["coordination_events"] += 1
                    
            except Exception as e:
                logging.debug(f"Error counting event: {e}")
        
        # Subscribe to all events for counting
        for topic in lifecycle_topics + agent_topics + coordination_topics:
            self.event_bus.subscribe(topic, event_counter)
    
    async def start_event_bus(self):
        """Start the event bus if not already running."""
        if not self.event_bus.is_running:
            await self.event_bus.start()
            logging.info("Event bus started")
    
    async def stop_event_bus(self):
        """Stop the event bus."""
        if self.event_bus.is_running:
            await self.event_bus.stop()
            logging.info("Event bus stopped")
    
    async def start_websocket_server(self, host: str, port: int) -> bool:
        """Start WebSocket server if not already running."""
        try:
            self.ws_manager = WebSocketServerManager(host=host, port=port)
            success = await self.ws_manager.start_server()
            if success:
                logging.info(f"WebSocket server started on {host}:{port}")
            else:
                logging.warning(f"Failed to start WebSocket server on {host}:{port}")
            return success
        except Exception as e:
            logging.error(f"Error starting WebSocket server: {e}")
            return False
    
    async def stop_websocket_server(self):
        """Stop WebSocket server."""
        if self.ws_manager:
            await self.ws_manager.stop_server()
            logging.info("WebSocket server stopped")
    
    async def run_live_mode(self, scenarios: List[ScenarioType], timeout_s: int, 
                          host: str, ws_port: Optional[int]) -> Dict[str, Any]:
        """Run scenarios in live mode using scenario orchestrator."""
        results = {}
        
        # Start WebSocket server if requested
        if ws_port:
            await self.start_websocket_server(host, ws_port)
        
        # Start event bus
        await self.start_event_bus()
        
        try:
            for scenario_type in scenarios:
                logging.info(f"Starting live scenario: {scenario_type.value}")
                
                scenario_start_time = time.time()
                scenario_result = await self.scenario_orchestrator.trigger_scenario(scenario_type)
                scenario_duration = time.time() - scenario_start_time
                
                # Check timing constraints
                timing_constraints = {
                    ScenarioType.COOLING_CRISIS: 120,
                    ScenarioType.SECURITY_BREACH: 90,
                    ScenarioType.ENERGY_OPTIMIZATION: 180,
                    ScenarioType.ROUTINE_MAINTENANCE: 60
                }
                
                expected_max_time = timing_constraints.get(scenario_type, timeout_s)
                timing_met = scenario_duration <= expected_max_time
                
                # Create result summary
                results[scenario_type.value] = {
                    "status": "success" if scenario_result.success else "failed",
                    "duration_seconds": scenario_duration,
                    "timing_constraint_met": timing_met,
                    "expected_max_time": expected_max_time,
                    "steps_completed": scenario_result.steps_completed,
                    "total_steps": scenario_result.total_steps,
                    "lifecycle_events": self.event_counts["lifecycle_events"],
                    "agent_events": self.event_counts["agent_events"],
                    "coordination_events": self.event_counts["coordination_events"],
                    "error_message": scenario_result.error_message,
                    "performance_metrics": scenario_result.performance_metrics
                }
                
                # Reset counters for next scenario
                for key in self.event_counts:
                    self.event_counts[key] = 0
                
                # Reset scenario orchestrator
                await self.scenario_orchestrator.reset_scenario()
                
                logging.info(f"Live scenario {scenario_type.value} completed: {scenario_result.success}")
                
        except Exception as e:
            logging.error(f"Error in live mode: {e}")
            raise
        
        finally:
            # Cleanup
            await self.stop_websocket_server()
            await self.stop_event_bus()
        
        return results
    
    async def run_fallback_mode(self, scenarios: List[str], speed: float, repeat: int,
                              host: str, ws_port: Optional[int]) -> Dict[str, Any]:
        """Run scenarios in fallback mode using pre-recorded responses."""
        results = {}
        
        # Start WebSocket server if requested
        if ws_port:
            await self.start_websocket_server(host, ws_port)
        
        # Start event bus
        await self.start_event_bus()
        
        try:
            for scenario in scenarios:
                logging.info(f"Starting fallback scenario: {scenario}")
                
                scenario_start_time = time.time()
                
                # Create and run fallback demo
                self.fallback_runner = FallbackDemoRunner(
                    event_bus=self.event_bus,
                    scenario=scenario,
                    speed=speed,
                    repeat=repeat
                )
                
                await self.fallback_runner.run()
                scenario_duration = time.time() - scenario_start_time
                
                # Create result summary
                results[scenario] = {
                    "status": "success",
                    "duration_seconds": scenario_duration,
                    "timing_constraint_met": True,  # Fallback mode doesn't enforce strict timing
                    "events_published": self.fallback_runner.published_events,
                    "speed_multiplier": speed,
                    "repeats": repeat,
                    "lifecycle_events": self.event_counts["lifecycle_events"],
                    "agent_events": self.event_counts["agent_events"],
                    "coordination_events": self.event_counts["coordination_events"]
                }
                
                # Reset counters for next scenario
                for key in self.event_counts:
                    self.event_counts[key] = 0
                
                logging.info(f"Fallback scenario {scenario} completed")
                
        except Exception as e:
            logging.error(f"Error in fallback mode: {e}")
            raise
        
        finally:
            # Cleanup
            await self.stop_websocket_server()
            await self.stop_event_bus()
        
        return results
    
    def generate_report(self, results: Dict[str, Any], report_path: str) -> str:
        """Generate JSON report for scenario execution results."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(results),
            "successful_scenarios": sum(1 for r in results.values() if r["status"] == "success"),
            "failed_scenarios": sum(1 for r in results.values() if r["status"] == "failed"),
            "scenarios": results,
            "summary": self._generate_summary(results)
        }
        
        # Ensure report directory exists
        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"Report saved to: {report_path}")
        return report_path
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution summary."""
        total_duration = sum(r.get("duration_seconds", 0) for r in results.values())
        total_events = sum(r.get("lifecycle_events", 0) + r.get("agent_events", 0) + 
                          r.get("coordination_events", 0) for r in results.values())
        
        return {
            "total_duration_seconds": total_duration,
            "total_events": total_events,
            "average_scenario_duration": total_duration / len(results) if results else 0,
            "success_rate": sum(1 for r in results.values() if r["status"] == "success") / len(results) if results else 0,
            "timing_constraints_met": sum(1 for r in results.values() if r.get("timing_constraint_met", False)),
            "failed_scenarios": [name for name, result in results.items() if result["status"] == "failed"]
        }


def parse_scenarios(scenario_arg: str) -> Union[List[ScenarioType], List[str]]:
    """Parse scenario argument into appropriate type list."""
    if scenario_arg == "all":
        # For live mode, return all ScenarioType enums
        return list(ScenarioType)
    else:
        # For fallback mode, return string list
        return [scenario_arg]


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


def get_default_report_path() -> str:
    """Generate default report path with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"./demo-results/report_{timestamp}.json"


def print_summary(results: Dict[str, Any], report_path: str):
    """Print concise summary of execution results."""
    print("\n" + "="*60)
    print("🎯 DEMO EXECUTION SUMMARY")
    print("="*60)
    
    summary = results.get("summary", {})
    successful = summary.get("successful_scenarios", 0)
    total = summary.get("total_scenarios", 0)
    failed_scenarios = summary.get("failed_scenarios", [])
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"⏱️  Total Duration: {summary.get('total_duration_seconds', 0):.2f}s")
    print(f"📊 Average Duration: {summary.get('average_scenario_duration', 0):.2f}s")
    print(f"🎯 Timing Constraints Met: {summary.get('timing_constraints_met', 0)}/{total}")
    
    if failed_scenarios:
        print(f"❌ Failed Scenarios: {', '.join(failed_scenarios)}")
    
    print(f"📄 Full Report: {report_path}")
    print("="*60)
    
    # Print per-scenario details
    for scenario_name, result in results.get("scenarios", {}).items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {scenario_name}: {result['status']} ({result['duration_seconds']:.2f}s)")


async def main():
    """Main entry point for the demo launcher."""
    parser = argparse.ArgumentParser(
        description="IntelliCenter Demo Launcher - Single-command demo runner for all scenarios"
    )
    
    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["live", "fallback"],
        default="live",
        help="Execution mode: live (real scenario orchestrator) or fallback (pre-recorded)"
    )
    
    # Scenario selection
    parser.add_argument(
        "--scenario",
        choices=["all", "cooling_crisis", "security_breach", "energy_optimization", "routine_maintenance"],
        default="all",
        help="Scenario to run (default: all)"
    )
    
    # Network configuration
    parser.add_argument(
        "--ws-port",
        type=int,
        help="Start WebSocket server on provided port (if not already running)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="WebSocket server host (default: 127.0.0.1)"
    )
    
    # Fallback mode specific options
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed multiplier for fallback mode timing (default: 1.0)"
    )
    
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat scenario in fallback mode (default: 1)"
    )
    
    # General options
    parser.add_argument(
        "--report",
        help="JSON report path (default: ./demo-results/report_YYYYmmdd_HHMMSS.json)"
    )
    
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=30,
        help="Per-scenario timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    if args.mode == "fallback" and args.speed <= 0:
        logger.error("Speed must be greater than 0 in fallback mode")
        sys.exit(1)
    
    if args.mode == "fallback" and args.repeat < 1:
        logger.error("Repeat must be at least 1 in fallback mode")
        sys.exit(1)
    
    # Parse scenarios
    try:
        scenarios = parse_scenarios(args.scenario)
    except ValueError as e:
        logger.error(f"Invalid scenario: {e}")
        sys.exit(1)
    
    # Determine report path
    report_path = args.report or get_default_report_path()
    
    # Create demo launcher
    launcher = DemoLauncher()
    
    try:
        logger.info(f"Starting demo launcher in {args.mode} mode")
        logger.info(f"Scenarios: {args.scenario}")
        logger.info(f"Report will be saved to: {report_path}")
        
        # Execute scenarios based on mode
        if args.mode == "live":
            results = await launcher.run_live_mode(
                scenarios=scenarios,
                timeout_s=args.timeout_s,
                host=args.host,
                ws_port=args.ws_port
            )
        else:  # fallback mode
            # Convert ScenarioType to string names for fallback mode
            scenario_names = [s.value if hasattr(s, 'value') else str(s) for s in scenarios]
            results = await launcher.run_fallback_mode(
                scenarios=scenario_names,
                speed=args.speed,
                repeat=args.repeat,
                host=args.host,
                ws_port=args.ws_port
            )
        
        # Generate and save report
        report_file = launcher.generate_report(results, report_path)
        
        # Print summary
        print_summary(results, report_file)
        
        # Exit with non-zero code if any scenario failed
        failed_scenarios = [name for name, result in results.get("scenarios", {}).items() 
                          if result["status"] == "failed"]
        
        if failed_scenarios:
            logger.error(f"Failed scenarios: {', '.join(failed_scenarios)}")
            sys.exit(1)
        else:
            logger.info("All scenarios completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())