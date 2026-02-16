#!/usr/bin/env python3
"""
WebSocket Manager Module
Handles WebSocket connections and event broadcasting for real-time updates
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import WebSocket

from .logger import get_logger

logger = get_logger()


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events to all connected clients
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accept a new WebSocket connection and register it
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # Store metadata
        client_id = client_id or f"client_{len(self.active_connections)}"
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now().isoformat(),
        }

        logger.success(
            f"WebSocket client connected: {client_id} | "
            f"Total connections: {len(self.active_connections)}"
        )

        # Send welcome message
        await self.send_to_client(
            websocket,
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to Orchestrator Backend",
            },
        )

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active list
        """
        if websocket in self.active_connections:
            metadata = self.connection_metadata.get(websocket, {})
            client_id = metadata.get("client_id", "unknown")

            self.active_connections.remove(websocket)
            self.connection_metadata.pop(websocket, None)

            logger.warning(
                f"WebSocket client disconnected: {client_id} | "
                f"Total connections: {len(self.active_connections)}"
            )

    async def send_to_client(self, websocket: WebSocket, data: dict):
        """
        Send JSON data to a specific client
        """
        try:
            await websocket.send_json(data)
            logger.debug(f"📤 Sent to client: {data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, data: dict, exclude: WebSocket = None):
        """
        Broadcast JSON data to all connected clients (except optionally one)
        """
        if not self.active_connections:
            logger.debug(
                f"No active connections, skipping broadcast: {data.get('type')}"
            )
            return

        event_type = data.get("type", "unknown")
        logger.websocket_event(
            event_type, {k: v for k, v in data.items() if k != "type"}
        )

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        disconnected = []

        for connection in self.active_connections:
            if connection == exclude:
                continue

            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

        logger.debug(
            f"📡 Broadcast complete: {event_type} → {len(self.active_connections) - len(disconnected)} clients"
        )

    # ========================================================================
    # Event Broadcasting Methods
    # ========================================================================

    async def broadcast_agent_created(self, agent_data: dict):
        """Broadcast agent creation event"""
        await self.broadcast({"type": "agent_created", "agent": agent_data})

    async def broadcast_agent_updated(self, agent_id: str, agent_data: dict):
        """Broadcast agent update event"""
        await self.broadcast(
            {"type": "agent_updated", "agent_id": agent_id, "agent": agent_data}
        )

    async def broadcast_agent_deleted(self, agent_id: str):
        """Broadcast agent deletion event"""
        await self.broadcast({"type": "agent_deleted", "agent_id": agent_id})

    async def broadcast_agent_status_change(
        self, agent_id: str, old_status: str, new_status: str
    ):
        """Broadcast agent status change"""
        await self.broadcast(
            {
                "type": "agent_status_changed",
                "agent_id": agent_id,
                "old_status": old_status,
                "new_status": new_status,
            }
        )

    async def broadcast_agent_log(self, log_data: dict):
        """Broadcast agent log entry"""
        await self.broadcast({"type": "agent_log", "log": log_data})

    async def broadcast_agent_summary_update(self, agent_id: str, summary: str):
        """Broadcast agent summary update (latest log summary for an agent)"""
        await self.broadcast(
            {"type": "agent_summary_update", "agent_id": agent_id, "summary": summary}
        )

    async def broadcast_orchestrator_updated(self, orchestrator_data: dict):
        """Broadcast orchestrator update (cost, tokens, status, etc.)"""
        await self.broadcast(
            {"type": "orchestrator_updated", "orchestrator": orchestrator_data}
        )

    async def broadcast_system_log(self, log_data: dict):
        """Broadcast system log entry"""
        await self.broadcast({"type": "system_log", "log": log_data})

    async def broadcast_chat_message(self, message_data: dict):
        """Broadcast chat message"""
        await self.broadcast({"type": "chat_message", "message": message_data})

    async def broadcast_orchestrator_chat(self, chat_data: dict):
        """Broadcast orchestrator chat message"""
        await self.broadcast({"type": "orchestrator_chat", "chat": chat_data})

    async def broadcast_error(self, error_message: str, details: dict = None):
        """Broadcast error event"""
        await self.broadcast(
            {
                "type": "error",
                "message": error_message,
                "details": details or {},
            }
        )

    async def broadcast_chat_stream(
        self, orchestrator_agent_id: str, chunk: str, is_complete: bool = False
    ):
        """
        Broadcast chat response chunk for real-time streaming.

        Args:
            orchestrator_agent_id: UUID of orchestrator agent
            chunk: Text chunk to stream
            is_complete: True if this is the final chunk
        """
        await self.broadcast(
            {
                "type": "chat_stream",
                "orchestrator_agent_id": orchestrator_agent_id,
                "chunk": chunk,
                "is_complete": is_complete,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def set_typing_indicator(self, orchestrator_agent_id: str, is_typing: bool):
        """
        Broadcast typing indicator state.

        Args:
            orchestrator_agent_id: UUID of orchestrator agent
            is_typing: True if orchestrator is typing, False if stopped
        """
        await self.broadcast(
            {
                "type": "chat_typing",
                "orchestrator_agent_id": orchestrator_agent_id,
                "is_typing": is_typing,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # ========================================================================
    # ADW (AI Developer Workflow) Broadcasting
    # ========================================================================

    async def broadcast_adw_created(self, adw_data: dict):
        """Broadcast ADW creation event"""
        await self.broadcast({"type": "adw_created", "adw": adw_data})

    async def broadcast_adw_updated(self, adw_id: str, adw_data: dict):
        """Broadcast ADW update event (status change, step progress)"""
        await self.broadcast(
            {"type": "adw_updated", "adw_id": adw_id, "adw": adw_data}
        )

    async def broadcast_adw_event(self, adw_id: str, event_data: dict):
        """Broadcast ADW event (agent_log entry for swimlane square)"""
        await self.broadcast(
            {"type": "adw_event", "adw_id": adw_id, "event": event_data}
        )

    async def broadcast_adw_step_change(
        self, adw_id: str, step: str, event_type: str, payload: dict = None
    ):
        """Broadcast ADW step lifecycle event (StepStart/StepEnd)"""
        await self.broadcast(
            {
                "type": "adw_step_change",
                "adw_id": adw_id,
                "step": step,
                "event_type": event_type,
                "payload": payload or {},
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def broadcast_adw_event_summary_update(
        self, adw_id: str, event_id: str, summary: str
    ):
        """Broadcast ADW event summary update (when AI summary is generated)"""
        await self.broadcast(
            {
                "type": "adw_event_summary_update",
                "adw_id": adw_id,
                "event_id": event_id,
                "summary": summary,
            }
        )

    # ========================================================================
    # Connection Management
    # ========================================================================

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_all_client_ids(self) -> List[str]:
        """Get list of all connected client IDs"""
        return [
            metadata.get("client_id", "unknown")
            for metadata in self.connection_metadata.values()
        ]

    async def send_heartbeat(self):
        """Send heartbeat to all connected clients"""
        await self.broadcast(
            {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_connections": self.get_connection_count(),
            }
        )


# Global WebSocket manager instance
ws_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    return ws_manager
