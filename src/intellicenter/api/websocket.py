"""
WebSocket server for real-time communication with the frontend dashboard.
Provides agent status updates, event streaming, and manual override capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from intellicenter.shared.event_bus import EventBus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_times: Dict[WebSocket, datetime] = {}

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept a WebSocket connection and track connection time."""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.connection_times[websocket] = datetime.now(timezone.utc)
            logger.info(
                f"WebSocket connected. Total connections: {len(self.active_connections)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return False

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_times:
                connection_duration = datetime.now(timezone.utc) - self.connection_times[websocket]
                logger.info(
                    f"WebSocket disconnected after {connection_duration.total_seconds():.2f}s"
                )
                del self.connection_times[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


class WebSocketServer:
    """FastAPI WebSocket server for IntelliCenter dashboard communication."""

    def __init__(
        self, event_bus: EventBus = None, host: str = "localhost", port: int = 8000
    ):
        self.app = FastAPI(title="IntelliCenter WebSocket API")
        self.host = host
        self.port = port
        self.event_bus = event_bus or EventBus()
        self.manager = WebSocketManager()
        self.agent_status = {
            "hvac": {"status": "offline", "last_update": None},
            "power": {"status": "offline", "last_update": None},
            "security": {"status": "offline", "last_update": None},
            "network": {"status": "offline", "last_update": None},
            "coordinator": {"status": "offline", "last_update": None},
        }

        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()
        self._setup_event_handlers()

    def _setup_routes(self):
        """Setup WebSocket and HTTP routes."""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Main WebSocket endpoint for dashboard communication."""
            connected = await self.manager.connect(websocket)
            if not connected:
                return

            try:
                # Send initial agent status
                await self.manager.send_personal_message(
                    {
                        "type": "agent_status",
                        "data": self.agent_status,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )

                # Listen for incoming messages
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_websocket_message(message, websocket)

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.manager.disconnect(websocket)

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "connections": len(self.manager.active_connections),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        @self.app.get("/agents/status")
        async def get_agent_status():
            """Get current agent status."""
            return {
                "agents": self.agent_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _setup_event_handlers(self):
        """Setup event bus handlers for agent updates."""
        if self.event_bus:
            # Start the event bus if not already running
            if not self.event_bus.is_running:
                asyncio.create_task(self.event_bus.start())

            # Subscribe to agent decision events
            self.event_bus.subscribe("hvac.cooling.decision", self._handle_hvac_event)
            self.event_bus.subscribe(
                "power.optimization.decision", self._handle_power_event
            )
            self.event_bus.subscribe(
                "security.assessment.decision", self._handle_security_event
            )
            self.event_bus.subscribe(
                "network.assessment.decision", self._handle_network_event
            )
            self.event_bus.subscribe(
                "facility.coordination.directive", self._handle_coordination_event
            )

            # Subscribe to agent status events (if they exist)
            self.event_bus.subscribe(
                "agent.status.update", self._handle_agent_status_event
            )

            # Start listening for events
            asyncio.create_task(self._listen_for_agent_events())

    async def _listen_for_agent_events(self):
        """Listen for agent events and broadcast to WebSocket clients."""
        try:
            logger.info("WebSocket server started listening for agent events")

            # Keep the listener alive while the event bus is running
            while self.event_bus and self.event_bus.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in agent event listener: {e}")
            # Attempt to restart event bus connection after a delay
            await asyncio.sleep(5)
            if self.event_bus and not self.event_bus.is_running:
                try:
                    await self.event_bus.start()
                    logger.info("Event bus connection restarted")
                except Exception as restart_error:
                    logger.error(f"Failed to restart event bus: {restart_error}")

    async def _handle_hvac_event(self, message: str):
        """Handle HVAC agent events."""
        try:
            data = json.loads(message)
            agent_name = "hvac"

            # Update agent status based on event data
            status = "online" if data.get("status") == "success" else "error"
            self.agent_status[agent_name] = {
                "status": status,
                "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "last_decision": data.get("cooling_level", "unknown"),
                "response_time": data.get("response_time", 0),
            }

            # Broadcast agent status update
            await self.manager.broadcast(
                {
                    "type": "agent_status_update",
                    "data": {
                        "agent": agent_name,
                        "status": status,
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "details": {
                            "decision": data.get("cooling_level"),
                            "reasoning": data.get("reasoning", ""),
                            "confidence": data.get("confidence", 0),
                        },
                    },
                }
            )

            # Broadcast event log entry
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "agent": agent_name,
                        "event": f"HVAC decision: {data.get('cooling_level', 'unknown')}",
                        "details": data.get("reasoning", ""),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling HVAC event: {e}")

    async def _handle_power_event(self, message: str):
        """Handle Power agent events."""
        try:
            data = json.loads(message)
            agent_name = "power"

            # Update agent status based on event data
            status = "online" if data.get("status") == "success" else "error"
            self.agent_status[agent_name] = {
                "status": status,
                "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "last_decision": data.get("optimization_level", "unknown"),
                "response_time": data.get("response_time", 0),
            }

            # Broadcast agent status update
            await self.manager.broadcast(
                {
                    "type": "agent_status_update",
                    "data": {
                        "agent": agent_name,
                        "status": status,
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "details": {
                            "decision": data.get("optimization_level"),
                            "reasoning": data.get("reasoning", ""),
                            "confidence": data.get("confidence", 0),
                        },
                    },
                }
            )

            # Broadcast event log entry
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "agent": agent_name,
                        "event": f"Power optimization: {data.get('optimization_level', 'unknown')}",
                        "details": data.get("reasoning", ""),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling Power event: {e}")

    async def _handle_security_event(self, message: str):
        """Handle Security agent events."""
        try:
            data = json.loads(message)
            agent_name = "security"

            # Update agent status based on event data
            status = "online" if data.get("status") == "success" else "error"
            self.agent_status[agent_name] = {
                "status": status,
                "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "last_decision": data.get("security_level", "unknown"),
                "response_time": data.get("response_time", 0),
            }

            # Broadcast agent status update
            await self.manager.broadcast(
                {
                    "type": "agent_status_update",
                    "data": {
                        "agent": agent_name,
                        "status": status,
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "details": {
                            "decision": data.get("security_level"),
                            "reasoning": data.get("reasoning", ""),
                            "confidence": data.get("confidence", 0),
                        },
                    },
                }
            )

            # Broadcast event log entry
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "agent": agent_name,
                        "event": f"Security assessment: {data.get('security_level', 'unknown')}",
                        "details": data.get("reasoning", ""),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling Security event: {e}")

    async def _handle_network_event(self, message: str):
        """Handle Network agent events."""
        try:
            data = json.loads(message)
            agent_name = "network"

            # Update agent status based on event data
            status = "online" if data.get("status") == "success" else "error"
            self.agent_status[agent_name] = {
                "status": status,
                "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "last_decision": data.get("network_action", "unknown"),
                "response_time": data.get("response_time", 0),
            }

            # Broadcast agent status update
            await self.manager.broadcast(
                {
                    "type": "agent_status_update",
                    "data": {
                        "agent": agent_name,
                        "status": status,
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "details": {
                            "decision": data.get("network_action"),
                            "reasoning": data.get("reasoning", ""),
                            "confidence": data.get("confidence", 0),
                        },
                    },
                }
            )

            # Broadcast event log entry
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "agent": agent_name,
                        "event": f"Network action: {data.get('network_action', 'unknown')}",
                        "details": data.get("reasoning", ""),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling Network event: {e}")

    async def _handle_coordination_event(self, message: str):
        """Handle Coordinator agent events."""
        try:
            data = json.loads(message)
            agent_name = "coordinator"

            # Update agent status based on event data
            status = "online" if data.get("status") == "success" else "error"
            self.agent_status[agent_name] = {
                "status": status,
                "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "last_decision": data.get("overall_status", "unknown"),
                "response_time": data.get("response_time", 0),
            }

            # Broadcast agent status update
            await self.manager.broadcast(
                {
                    "type": "agent_status_update",
                    "data": {
                        "agent": agent_name,
                        "status": status,
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "details": {
                            "decision": data.get("overall_status"),
                            "reasoning": data.get("reasoning", ""),
                            "confidence": data.get("confidence", 0),
                        },
                    },
                }
            )

            # Broadcast coordination directive
            await self.manager.broadcast(
                {
                    "type": "coordination_directive",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "directive": data.get("directive", ""),
                        "priority_event": data.get("priority_event", ""),
                        "coordinated_plan": data.get("coordinated_plan", []),
                    },
                }
            )

            # Broadcast event log entry
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": self.agent_status[agent_name]["last_update"],
                        "agent": agent_name,
                        "event": f"Coordination: {data.get('overall_status', 'unknown')}",
                        "details": data.get("directive", ""),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling Coordination event: {e}")

    async def _handle_agent_status_event(self, message: str):
        """Handle generic agent status events."""
        try:
            data = json.loads(message)
            agent_name = data.get("agent", "unknown")

            if agent_name in self.agent_status:
                # Update agent status
                self.agent_status[agent_name] = {
                    "status": data.get("status", "unknown"),
                    "last_update": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                }

                # Broadcast status update
                await self.manager.broadcast(
                    {
                        "type": "agent_status_update",
                        "data": {
                            "agent": agent_name,
                            "status": data.get("status", "unknown"),
                            "timestamp": self.agent_status[agent_name]["last_update"],
                        },
                    }
                )

        except Exception as e:
            logger.error(f"Error handling agent status event: {e}")

    async def _handle_websocket_message(self, message: dict, websocket: WebSocket):
        """Handle incoming WebSocket messages from clients."""
        try:
            message_type = message.get("type")

            if message_type == "manual_override":
                await self._handle_manual_override(message.get("data", {}), websocket)
            elif message_type == "ping":
                await self.manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}, websocket
                )
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def _handle_manual_override(self, data: dict, websocket: WebSocket):
        """Handle manual override commands from the dashboard."""
        agent = data.get("agent")
        command = data.get("command")

        if not agent or not command:
            await self.manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Invalid manual override request",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                websocket,
            )
            return

        try:
            # Publish manual override event to the event bus
            override_event = {
                "agent": agent,
                "command": command,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "dashboard_override",
            }

            if self.event_bus and self.event_bus.is_running:
                await self.event_bus.publish(
                    f"{agent}.manual.override", json.dumps(override_event)
                )
                logger.info(f"Published manual override for {agent}: {command}")

            # Send response to requesting client
            response = {
                "type": "manual_override_response",
                "data": {
                    "agent": agent,
                    "command": command,
                    "status": (
                        "published"
                        if self.event_bus and self.event_bus.is_running
                        else "event_bus_unavailable"
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            await self.manager.send_personal_message(response, websocket)

            # Broadcast override status to all clients
            await self.manager.broadcast(
                {
                    "type": "agent_override",
                    "data": {
                        "agent": agent,
                        "override_active": True,
                        "command": command,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            )

            # Log the override event
            await self.manager.broadcast(
                {
                    "type": "event_log",
                    "data": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": agent,
                        "event": f"Manual override: {command}",
                        "details": "Override command sent via dashboard",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error handling manual override: {e}")
            await self.manager.send_personal_message(
                {
                    "type": "error",
                    "message": f"Failed to process manual override: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                websocket,
            )

    async def start(self):
        """Start the WebSocket server."""
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self):
        """Stop the WebSocket server and clean up resources."""
        try:
            # Stop the event bus
            if self.event_bus and self.event_bus.is_running:
                await self.event_bus.stop()
                logger.info("Event bus stopped")

            # Disconnect all WebSocket connections
            for connection in list(self.manager.active_connections):
                try:
                    await connection.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket connection: {e}")

            logger.info("WebSocket server stopped")

        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")

    def run(self):
        """Run the WebSocket server (blocking)."""
        uvicorn.run(self.app, host=self.host, port=self.port)


async def main():
    """Main function to run the WebSocket server."""
    server = WebSocketServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
