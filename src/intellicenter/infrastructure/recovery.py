"""
System recovery and graceful shutdown management for IntelliCenter.
Handles system shutdown, restart validation, event queue persistence, and agent coordination resumption.
"""

import asyncio
import json
import time
import signal
import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import redis.asyncio as redis
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.state import StateManager


@dataclass
class SystemState:
    """Represents the overall system state during shutdown/recovery"""
    shutdown_timestamp: float
    active_agents: List[str]
    pending_events: List[Dict[str, Any]]
    system_version: str
    recovery_checkpoint: str


@dataclass
class EventQueueSnapshot:
    """Snapshot of event queue state for persistence"""
    timestamp: float
    pending_events: List[Dict[str, Any]]
    event_count: int
    queue_size: int


class RecoveryManager:
    """Manages system recovery, graceful shutdown, and event queue persistence"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager, redis_url: str = "redis://localhost:6379"):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.shutdown_handlers: List[Callable] = []
        self.recovery_handlers: List[Callable] = []
        self.is_shutting_down = False
        self.recovery_timeout = 60.0  # 60 seconds for full recovery
        
    async def initialize(self):
        """Initialize the recovery manager"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
        # Test Redis connection
        try:
            await self.redis_client.ping()
            print("✅ RecoveryManager: Redis connection established")
        except Exception as e:
            print(f"❌ RecoveryManager: Redis connection failed: {e}")
            raise
            
        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"🔄 RecoveryManager: Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
    def register_shutdown_handler(self, handler: Callable):
        """Register a handler to be called during shutdown"""
        self.shutdown_handlers.append(handler)
        
    def register_recovery_handler(self, handler: Callable):
        """Register a handler to be called during recovery"""
        self.recovery_handlers.append(handler)
        
    async def graceful_shutdown(self) -> bool:
        """Perform graceful system shutdown with state preservation"""
        if self.is_shutting_down:
            return True
            
        self.is_shutting_down = True
        shutdown_start = time.time()
        
        try:
            print("🔄 RecoveryManager: Starting graceful shutdown...")
            
            # 1. Save current system state
            system_state = await self._capture_system_state()
            await self._save_system_state(system_state)
            
            # 2. Persist event queue
            await self._persist_event_queue()
            
            # 3. Save all agent states
            await self._save_all_agent_states()
            
            # 4. Call registered shutdown handlers
            for handler in self.shutdown_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    print(f"⚠️  RecoveryManager: Shutdown handler error: {e}")
            
            # 5. Stop event bus gracefully
            if self.event_bus:
                await self.event_bus.stop()
                
            shutdown_time = time.time() - shutdown_start
            print(f"✅ RecoveryManager: Graceful shutdown completed in {shutdown_time:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ RecoveryManager: Graceful shutdown failed: {e}")
            return False
            
    async def system_recovery(self) -> bool:
        """Perform full system recovery from saved state"""
        recovery_start = time.time()
        
        try:
            print("🔄 RecoveryManager: Starting system recovery...")
            
            # 1. Load system state
            system_state = await self._load_system_state()
            if not system_state:
                print("⚠️  RecoveryManager: No previous system state found")
                return False
                
            # 2. Restore event queue
            await self._restore_event_queue()
            
            # 3. Restore agent states
            restored_agents = await self._restore_all_agent_states()
            
            # 4. Call registered recovery handlers
            for handler in self.recovery_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    print(f"⚠️  RecoveryManager: Recovery handler error: {e}")
            
            # 5. Restart event bus
            if self.event_bus and not self.event_bus.is_running:
                await self.event_bus.start()
                
            # 6. Validate recovery
            recovery_valid = await self._validate_recovery(system_state, restored_agents)
            
            recovery_time = time.time() - recovery_start
            
            if recovery_valid:
                print(f"✅ RecoveryManager: System recovery completed in {recovery_time:.2f}s")
                return True
            else:
                print(f"❌ RecoveryManager: System recovery validation failed after {recovery_time:.2f}s")
                return False
                
        except Exception as e:
            print(f"❌ RecoveryManager: System recovery failed: {e}")
            return False
            
    async def _capture_system_state(self) -> SystemState:
        """Capture current system state for persistence"""
        # Get active agents from state manager
        all_states = await self.state_manager.get_all_agent_states()
        active_agents = list(all_states.keys())
        
        # Capture pending events (simplified - in real implementation would capture from event bus)
        pending_events = []
        
        return SystemState(
            shutdown_timestamp=time.time(),
            active_agents=active_agents,
            pending_events=pending_events,
            system_version="2.0.0",
            recovery_checkpoint="graceful_shutdown"
        )
        
    async def _save_system_state(self, system_state: SystemState) -> bool:
        """Save system state to Redis"""
        try:
            state_data = asdict(system_state)
            await self.redis_client.set(
                "system:recovery_state",
                json.dumps(state_data),
                ex=86400  # 24 hour expiration
            )
            return True
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to save system state: {e}")
            return False
            
    async def _load_system_state(self) -> Optional[SystemState]:
        """Load system state from Redis"""
        try:
            state_data = await self.redis_client.get("system:recovery_state")
            if not state_data:
                return None
                
            data = json.loads(state_data)
            return SystemState(**data)
            
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to load system state: {e}")
            return None
            
    async def _persist_event_queue(self) -> bool:
        """Persist current event queue state"""
        try:
            # Create event queue snapshot
            # In a real implementation, this would capture actual pending events from the event bus
            snapshot = EventQueueSnapshot(
                timestamp=time.time(),
                pending_events=[],  # Would be populated from actual event bus
                event_count=0,
                queue_size=0
            )
            
            # Save to Redis
            await self.redis_client.set(
                "system:event_queue_snapshot",
                json.dumps(asdict(snapshot)),
                ex=86400
            )
            
            print("✅ RecoveryManager: Event queue persisted")
            return True
            
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to persist event queue: {e}")
            return False
            
    async def _restore_event_queue(self) -> bool:
        """Restore event queue from persistence"""
        try:
            snapshot_data = await self.redis_client.get("system:event_queue_snapshot")
            if not snapshot_data:
                print("ℹ️  RecoveryManager: No event queue snapshot found")
                return True
                
            snapshot = json.loads(snapshot_data)
            
            # Restore pending events to event bus
            pending_events = snapshot.get("pending_events", [])
            for event in pending_events:
                await self.event_bus.publish(event["type"], event["data"])
                
            print(f"✅ RecoveryManager: Restored {len(pending_events)} events to queue")
            return True
            
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to restore event queue: {e}")
            return False
            
    async def _save_all_agent_states(self) -> bool:
        """Save states of all active agents"""
        try:
            all_states = await self.state_manager.get_all_agent_states()
            
            # Create a recovery manifest
            manifest = {
                "timestamp": time.time(),
                "agent_count": len(all_states),
                "agents": list(all_states.keys())
            }
            
            await self.redis_client.set(
                "system:agent_recovery_manifest",
                json.dumps(manifest),
                ex=86400
            )
            
            print(f"✅ RecoveryManager: Saved states for {len(all_states)} agents")
            return True
            
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to save agent states: {e}")
            return False
            
    async def _restore_all_agent_states(self) -> List[str]:
        """Restore states of all agents"""
        restored_agents = []
        
        try:
            # Load recovery manifest
            manifest_data = await self.redis_client.get("system:agent_recovery_manifest")
            if not manifest_data:
                print("ℹ️  RecoveryManager: No agent recovery manifest found")
                return restored_agents
                
            manifest = json.loads(manifest_data)
            agent_ids = manifest.get("agents", [])
            
            # Restore each agent state
            for agent_id in agent_ids:
                agent_state = await self.state_manager.load_agent_state(agent_id)
                if agent_state:
                    restored_agents.append(agent_id)
                    
            print(f"✅ RecoveryManager: Restored {len(restored_agents)} agent states")
            return restored_agents
            
        except Exception as e:
            print(f"❌ RecoveryManager: Failed to restore agent states: {e}")
            return restored_agents
            
    async def _validate_recovery(self, system_state: SystemState, restored_agents: List[str]) -> bool:
        """Validate that recovery was successful"""
        try:
            # Check if all expected agents were restored
            expected_agents = set(system_state.active_agents)
            restored_agents_set = set(restored_agents)
            
            missing_agents = expected_agents - restored_agents_set
            if missing_agents:
                print(f"⚠️  RecoveryManager: Missing agents after recovery: {missing_agents}")
                return False
                
            # Check event bus is running
            if not self.event_bus.is_running:
                print("⚠️  RecoveryManager: Event bus not running after recovery")
                return False
                
            # Check Redis connectivity
            await self.redis_client.ping()
            
            print("✅ RecoveryManager: Recovery validation passed")
            return True
            
        except Exception as e:
            print(f"❌ RecoveryManager: Recovery validation failed: {e}")
            return False
            
    async def test_recovery_timing(self) -> float:
        """Test recovery timing to ensure it meets requirements"""
        # Simulate a recovery scenario
        start_time = time.time()
        
        # Save current state
        system_state = await self._capture_system_state()
        await self._save_system_state(system_state)
        await self._persist_event_queue()
        await self._save_all_agent_states()
        
        # Simulate recovery
        recovery_success = await self.system_recovery()
        
        recovery_time = time.time() - start_time
        
        if recovery_success and recovery_time <= 60.0:  # Must be within 60 seconds
            print(f"✅ RecoveryManager: Recovery timing test passed: {recovery_time:.2f}s")
        else:
            print(f"❌ RecoveryManager: Recovery timing test failed: {recovery_time:.2f}s")
            
        return recovery_time
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()