"""WebSocket manager for streaming home page sections to frontend."""

import logging
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger("nile.websocket")


class HomePageWebSocketManager:
    """
    Manages WebSocket connections for streaming home page sections.

    Each user has one active connection. When the agent calls stream_section,
    the section is immediately pushed to the user's WebSocket.
    """

    def __init__(self):
        # Map user_id -> WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}
        logger.info("HomePageWebSocketManager initialized")

    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept and register a WebSocket connection for a user."""
        await websocket.accept()

        # Close existing connection if any
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except Exception:
                pass  # Connection might already be closed

        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: int):
        """Remove a user's WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")

    def is_connected(self, user_id: int) -> bool:
        """Check if a user has an active WebSocket connection."""
        return user_id in self.active_connections

    async def stream_section(self, user_id: int, section_data: dict) -> bool:
        """
        Stream a single section to the user's WebSocket.

        Args:
            user_id: The user to send to
            section_data: Hydrated section data (with full product objects)

        Returns:
            True if sent successfully, False if no connection
        """
        websocket = self.active_connections.get(user_id)
        if not websocket:
            logger.warning(f"No WebSocket connection for user {user_id}")
            return False

        try:
            message = {
                "type": "section",
                "data": section_data,
            }
            await websocket.send_json(message)
            logger.info(f"Streamed section '{section_data.get('component_type')}' to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stream section to user {user_id}: {e}")
            self.disconnect(user_id)
            return False

    async def stream_complete(self, user_id: int):
        """Signal that all sections have been streamed."""
        websocket = self.active_connections.get(user_id)
        if not websocket:
            return

        try:
            message = {
                "type": "complete",
                "data": {"is_personalized": True},
            }
            await websocket.send_json(message)
            logger.info(f"Sent completion signal to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send completion to user {user_id}: {e}")

    async def stream_error(self, user_id: int, error_message: str):
        """Send an error message to the user."""
        websocket = self.active_connections.get(user_id)
        if not websocket:
            return

        try:
            message = {
                "type": "error",
                "data": {"message": error_message},
            }
            await websocket.send_json(message)
            logger.error(f"Sent error to user {user_id}: {error_message}")
        except Exception as e:
            logger.error(f"Failed to send error to user {user_id}: {e}")


# Global instance - imported by agent_expert.py and main.py
home_ws_manager = HomePageWebSocketManager()
