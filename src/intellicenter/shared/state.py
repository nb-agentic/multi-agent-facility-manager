"""
State persistence and recovery management for IntelliCenter agents.
Provides centralized state management with Redis backend for agent state persistence.
"""

import json
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import redis.asyncio as redis
from intellicenter.shared.logger import logger
from intellicenter.shared.schema import AgentState, AgentType


class StateManager:
    """Manages agent state persistence and recovery using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.state_cache: Dict[str, AgentState] = {}
        self.event_bus: Optional[EventBus] = None
        
    async def initialize(self, event_bus: EventBus):
        """Initialize the state manager with Redis connection and event bus"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.event_bus = event_bus
        
        # Test Redis connection
        try:
            await self.redis_client.ping()
            logger.info("state_manager_redis_connected", url=self.redis_url)
        except Exception as e:
            logger.error("state_manager_redis_connection_failed", url=self.redis_url, error=str(e))
            raise
            
        # Subscribe to state change events
        if self.event_bus:
            self.event_bus.subscribe("agent.state.changed", self._handle_state_change)
            
    async def save_agent_state(self, agent_id: str, agent_type: str, state_data: Dict[str, Any]) -> bool:
        """Save agent state to Redis with versioning and checksums"""
        try:
            # Generate checksum for integrity validation
            state_json = json.dumps(state_data, sort_keys=True)
            checksum = str(hash(state_json))

            # Get current version or start at 1
            current_version = await self._get_state_version(agent_id)
            new_version = current_version + 1

            # Create agent state object using Pydantic model
            agent_state = AgentState(
                agent_id=agent_id,
                agent_type=AgentType(agent_type),
                state_data=state_data,
                last_updated=datetime.now(timezone.utc),
                version=new_version,
                checksum=checksum,
            )

            # Save to Redis
            state_key = f"agent_state:{agent_id}"
            await self.redis_client.hset(
                state_key,
                mapping={
                    "agent_type": agent_type,
                    "state_data": json.dumps(state_data),
                    "last_updated": agent_state.last_updated.isoformat(),
                    "version": str(new_version),
                    "checksum": checksum,
                },
            )

            # Update cache
            self.state_cache[agent_id] = agent_state

            # Set expiration (24 hours)
            await self.redis_client.expire(state_key, 86400)

            logger.debug("agent_state_saved", agent_id=agent_id, version=new_version)
            return True

        except Exception as e:
            logger.error("agent_state_save_failed", agent_id=agent_id, error=str(e))
            return False
            
    async def load_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state from Redis with integrity validation"""
        try:
            state_key = f"agent_state:{agent_id}"
            state_data = await self.redis_client.hgetall(state_key)

            if not state_data:
                return None

            # Reconstruct AgentState object
            agent_state = AgentState(
                agent_id=agent_id,
                agent_type=AgentType(state_data["agent_type"]),
                state_data=json.loads(state_data["state_data"]),
                last_updated=datetime.fromisoformat(state_data["last_updated"]),
                version=int(state_data["version"]),
                checksum=state_data["checksum"],
            )

            # Validate checksum
            state_json = json.dumps(agent_state.state_data, sort_keys=True)
            expected_checksum = str(hash(state_json))

            if expected_checksum != agent_state.checksum:
                logger.warning("agent_state_checksum_mismatch", agent_id=agent_id)
                return None

            # Update cache
            self.state_cache[agent_id] = agent_state
            return agent_state

        except Exception as e:
            logger.error("agent_state_load_failed", agent_id=agent_id, error=str(e))
            return None

    async def recover_agent_state(
        self, agent_id: str, timeout: float = 30.0
    ) -> Optional[dict[str, Any]]:
        """Recover agent state within specified timeout"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            agent_state = await self.load_agent_state(agent_id)
            if agent_state:
                return agent_state.state_data
            await asyncio.sleep(0.1)

        return None
        
    async def get_all_agent_states(self) -> dict[str, AgentState]:
        """Get all agent states from Redis"""
        try:
            pattern = "agent_state:*"
            keys = await self.redis_client.keys(pattern)
            
            states = {}
            for key in keys:
                agent_id = key.split(":", 1)[1]
                agent_state = await self.load_agent_state(agent_id)
                if agent_state:
                    states[agent_id] = agent_state
                    
            return states
            
        except Exception as e:
            logger.error("get_all_agent_states_failed", error=str(e))
            return {}
            
    async def delete_agent_state(self, agent_id: str) -> bool:
        """Delete agent state from Redis"""
        try:
            state_key = f"agent_state:{agent_id}"
            result = await self.redis_client.delete(state_key)
            
            # Remove from cache
            if agent_id in self.state_cache:
                del self.state_cache[agent_id]
                
            return result > 0
            
        except Exception as e:
            logger.error("delete_agent_state_failed", agent_id=agent_id, error=str(e))
            return False
            
    async def _get_state_version(self, agent_id: str) -> int:
        """Get current version number for agent state"""
        try:
            state_key = f"agent_state:{agent_id}"
            version = await self.redis_client.hget(state_key, "version")
            return int(version) if version else 0
        except:
            return 0
            
    async def _handle_state_change(self, message: str):
        """Handle state change events from event bus"""
        try:
            data = json.loads(message)
            agent_id = data.get("agent_id")
            agent_type = data.get("agent_type")
            state_data = data.get("state_data")
            
            if agent_id and agent_type and state_data:
                await self.save_agent_state(agent_id, agent_type, state_data)
                
        except Exception as e:
            logger.error("handle_state_change_failed", error=str(e))
            
    async def validate_state_integrity(self, agent_id: str) -> bool:
        """Validate the integrity of stored agent state"""
        agent_state = await self.load_agent_state(agent_id)
        if not agent_state:
            return False
            
        # Recalculate checksum
        state_json = json.dumps(agent_state.state_data, sort_keys=True)
        calculated_checksum = str(hash(state_json))
        
        return calculated_checksum == agent_state.checksum
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()