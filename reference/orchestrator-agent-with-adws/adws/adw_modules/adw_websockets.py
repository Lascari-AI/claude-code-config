# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "websockets>=12.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
ADW WebSocket Client Module - Real-time event broadcasting for AI Developer Workflows.

This module provides a WebSocket client that connects to the orchestrator backend
and broadcasts ADW events in real-time. Events are relayed to all connected frontends.

Architecture:
    ADW Process --ws--> Backend --broadcast--> Frontend(s)

Usage:
    from adw_modules.adw_websockets import AdwWebSocketClient

    async with AdwWebSocketClient() as ws:
        await ws.broadcast_adw_created(adw_data)
        await ws.broadcast_adw_event(adw_id, event_data)
        await ws.broadcast_adw_step_change(adw_id, step, "StepStart")
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import websockets
from dotenv import load_dotenv
from websockets.client import WebSocketClientProtocol

# Load environment variables
_env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # Root .env
    Path(__file__).parent.parent.parent / "apps" / "orchestrator_3_stream" / ".env",
]
for env_path in _env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

# Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "9403"))
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws")

# Connection settings
RECONNECT_DELAY = 1.0  # seconds
MAX_RECONNECT_ATTEMPTS = 5
CONNECTION_TIMEOUT = 10.0  # seconds


class AdwWebSocketClient:
    """
    WebSocket client for broadcasting ADW events to the orchestrator backend.

    The client maintains a persistent connection during workflow execution
    and sends events as JSON messages. The backend relays these to all
    connected frontend clients.

    RESILIENT BY DESIGN:
    - All broadcast methods fail silently if server is unavailable
    - Workflow execution continues regardless of WebSocket connectivity
    - Errors are logged but never raised to caller

    Usage as context manager (recommended):
        async with AdwWebSocketClient() as ws:
            await ws.broadcast_adw_event(adw_id, event_data)

    Usage with manual lifecycle:
        ws = AdwWebSocketClient()
        await ws.connect()
        await ws.broadcast_adw_event(adw_id, event_data)
        await ws.disconnect()
    """

    def __init__(self, url: str = WEBSOCKET_URL, verbose: bool = False):
        """
        Initialize the WebSocket client.

        Args:
            url: WebSocket URL to connect to (defaults to WEBSOCKET_URL from env)
            verbose: If True, print connection/send status messages
        """
        self.url = url
        self.verbose = verbose
        self._ws: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._reconnect_attempts = 0
        self._client_id: Optional[str] = None
        self._connection_failed = False  # Track if initial connection failed

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket is connected."""
        return self._connected and self._ws is not None

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to the backend.

        Returns:
            True if connected successfully, False otherwise

        Note: This method never raises exceptions - it fails silently.
        """
        if self.is_connected:
            return True

        # If we already failed to connect, don't spam retries
        if self._connection_failed and self._reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
            return False

        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(self.url),
                timeout=CONNECTION_TIMEOUT
            )
            self._connected = True
            self._reconnect_attempts = 0
            self._connection_failed = False

            # Wait for connection_established message
            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "connection_established":
                    self._client_id = data.get("client_id")
                    self._log(f"[ADW-WS] Connected to {self.url} as {self._client_id}")
            except asyncio.TimeoutError:
                self._log(f"[ADW-WS] Connected to {self.url} (no welcome message)")

            return True

        except asyncio.TimeoutError:
            self._connection_failed = True
            self._log(f"[ADW-WS] Connection timeout to {self.url}")
            return False
        except Exception as e:
            self._connection_failed = True
            self._log(f"[ADW-WS] Connection failed: {e}")
            return False

    async def disconnect(self):
        """Close the WebSocket connection."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            finally:
                self._ws = None
                self._connected = False
                self._client_id = None
                self._log("[ADW-WS] Disconnected")

    async def _ensure_connected(self) -> bool:
        """
        Ensure connection is established, reconnect if needed.

        Note: This method is resilient - it won't spam reconnection attempts
        if the server is unavailable.
        """
        if self.is_connected:
            return True

        # Don't spam reconnects if we know the server is down
        if self._connection_failed:
            return False

        while self._reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            self._reconnect_attempts += 1
            self._log(f"[ADW-WS] Reconnect attempt {self._reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS}")

            if await self.connect():
                return True

            await asyncio.sleep(RECONNECT_DELAY * min(self._reconnect_attempts, 3))

        self._connection_failed = True
        self._log("[ADW-WS] Max reconnect attempts reached, giving up")
        return False

    async def _send(self, data: dict) -> bool:
        """
        Send a JSON message through the WebSocket.

        Args:
            data: Dictionary to send as JSON

        Returns:
            True if sent successfully, False otherwise

        Note: This method never raises exceptions - it fails silently.
        Workflow execution continues regardless of send success.
        """
        # Don't even try if we know the server is down
        if self._connection_failed:
            return False

        if not await self._ensure_connected():
            return False

        try:
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()

            await self._ws.send(json.dumps(data))
            return True

        except websockets.exceptions.ConnectionClosed:
            self._log("[ADW-WS] Connection closed during send")
            self._connected = False
            # Try one reconnect
            if await self._ensure_connected():
                try:
                    await self._ws.send(json.dumps(data))
                    return True
                except Exception:
                    pass
            return False
        except Exception as e:
            self._log(f"[ADW-WS] Send failed: {e}")
            return False

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    async def __aenter__(self) -> "AdwWebSocketClient":
        """Async context manager entry - establish connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close connection."""
        await self.disconnect()
        return False  # Don't suppress exceptions

    # =========================================================================
    # ADW Broadcast Methods
    # =========================================================================

    async def broadcast_adw_created(self, adw_data: dict) -> bool:
        """
        Broadcast ADW creation event.

        Args:
            adw_data: ADW data dictionary (from database model)
        """
        return await self._send({
            "type": "adw_broadcast",
            "broadcast_type": "adw_created",
            "adw": adw_data,
        })

    async def broadcast_adw_updated(self, adw_id: str, adw_data: dict) -> bool:
        """
        Broadcast ADW update event (status change, step progress).

        Args:
            adw_id: ADW UUID
            adw_data: Updated ADW data
        """
        return await self._send({
            "type": "adw_broadcast",
            "broadcast_type": "adw_updated",
            "adw_id": adw_id,
            "adw": adw_data,
        })

    async def broadcast_adw_event(self, adw_id: str, event_data: dict) -> bool:
        """
        Broadcast ADW event (agent_log entry for swimlane square).

        Args:
            adw_id: ADW UUID
            event_data: Event data dictionary (from agent_logs)
        """
        return await self._send({
            "type": "adw_broadcast",
            "broadcast_type": "adw_event",
            "adw_id": adw_id,
            "event": event_data,
        })

    async def broadcast_adw_step_change(
        self,
        adw_id: str,
        step: str,
        event_type: str,
        payload: Optional[dict] = None,
    ) -> bool:
        """
        Broadcast ADW step lifecycle event (StepStart/StepEnd).

        Args:
            adw_id: ADW UUID
            step: Step slug (e.g., "plan-feature", "build-feature")
            event_type: "StepStart" or "StepEnd"
            payload: Optional step payload
        """
        return await self._send({
            "type": "adw_broadcast",
            "broadcast_type": "adw_step_change",
            "adw_id": adw_id,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
        })

    async def broadcast_adw_status(
        self,
        adw_id: str,
        status: str,
        current_step: Optional[str] = None,
        completed_steps: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Broadcast ADW status change.

        Args:
            adw_id: ADW UUID
            status: New status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
            current_step: Current step slug
            completed_steps: Number of completed steps
            error_message: Error message if failed
        """
        return await self._send({
            "type": "adw_broadcast",
            "broadcast_type": "adw_status",
            "adw_id": adw_id,
            "status": status,
            "current_step": current_step,
            "completed_steps": completed_steps,
            "error_message": error_message,
        })

    # =========================================================================
    # Agent Broadcast Methods (for agents created by ADW workflows)
    # =========================================================================

    async def broadcast_agent_created(self, agent_data: dict) -> bool:
        """
        Broadcast agent creation event.

        Args:
            agent_data: Agent data dictionary with id, name, model, status, etc.
        """
        return await self._send({
            "type": "agent_broadcast",
            "broadcast_type": "agent_created",
            "agent": agent_data,
        })

    async def broadcast_agent_status_change(
        self,
        agent_id: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        """
        Broadcast agent status change.

        Args:
            agent_id: Agent UUID
            old_status: Previous status
            new_status: New status
        """
        return await self._send({
            "type": "agent_broadcast",
            "broadcast_type": "agent_status_changed",
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
        })

    async def broadcast_agent_updated(
        self,
        agent_id: str,
        agent_data: dict,
    ) -> bool:
        """
        Broadcast agent update event (tokens, cost, session_id, etc.).

        Args:
            agent_id: Agent UUID
            agent_data: Updated agent data (partial update)
        """
        return await self._send({
            "type": "agent_broadcast",
            "broadcast_type": "agent_updated",
            "agent_id": agent_id,
            "agent": agent_data,
        })


# =============================================================================
# Global Client Instance (for use in adw_logging.py integration)
# =============================================================================

_global_client: Optional[AdwWebSocketClient] = None
_ws_enabled: bool = True  # Can be disabled to skip all WS operations


def disable_websocket():
    """Disable WebSocket broadcasting globally (for testing/manual workflows)."""
    global _ws_enabled
    _ws_enabled = False


def enable_websocket():
    """Enable WebSocket broadcasting globally."""
    global _ws_enabled
    _ws_enabled = True


def is_websocket_enabled() -> bool:
    """Check if WebSocket broadcasting is enabled."""
    return _ws_enabled


async def get_ws_client() -> Optional[AdwWebSocketClient]:
    """
    Get or create the global WebSocket client.

    Returns:
        The global AdwWebSocketClient instance, or None if WS is disabled
    """
    global _global_client
    if not _ws_enabled:
        return None
    if _global_client is None:
        _global_client = AdwWebSocketClient()
    return _global_client


async def init_ws_client(url: str = WEBSOCKET_URL, verbose: bool = False) -> Optional[AdwWebSocketClient]:
    """
    Initialize and connect the global WebSocket client.

    Args:
        url: WebSocket URL to connect to
        verbose: If True, print connection/send status messages

    Returns:
        Connected AdwWebSocketClient instance, or None if connection failed/disabled

    Note: This method never raises exceptions - it fails silently.
    """
    global _global_client
    if not _ws_enabled:
        return None
    _global_client = AdwWebSocketClient(url, verbose=verbose)
    await _global_client.connect()  # May fail silently
    return _global_client


async def close_ws_client():
    """Close the global WebSocket client connection."""
    global _global_client
    if _global_client:
        await _global_client.disconnect()
        _global_client = None


# =============================================================================
# Convenience Functions (use global client)
# =============================================================================
# These functions are resilient - they fail silently if WS is disabled or unavailable


async def broadcast_adw_created(adw_data: dict) -> bool:
    """Broadcast ADW creation using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_adw_created(adw_data)


async def broadcast_adw_updated(adw_id: str, adw_data: dict) -> bool:
    """Broadcast ADW update using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_adw_updated(adw_id, adw_data)


async def broadcast_adw_event(adw_id: str, event_data: dict) -> bool:
    """Broadcast ADW event using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_adw_event(adw_id, event_data)


async def broadcast_adw_step_change(
    adw_id: str,
    step: str,
    event_type: str,
    payload: Optional[dict] = None,
) -> bool:
    """Broadcast ADW step change using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_adw_step_change(adw_id, step, event_type, payload)


async def broadcast_adw_status(
    adw_id: str,
    status: str,
    current_step: Optional[str] = None,
    completed_steps: Optional[int] = None,
    error_message: Optional[str] = None,
) -> bool:
    """Broadcast ADW status change using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_adw_status(
        adw_id, status, current_step, completed_steps, error_message
    )


# =============================================================================
# Agent Convenience Functions (use global client)
# =============================================================================


async def broadcast_agent_created(agent_data: dict) -> bool:
    """Broadcast agent creation using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_agent_created(agent_data)


async def broadcast_agent_status_change(
    agent_id: str,
    old_status: str,
    new_status: str,
) -> bool:
    """Broadcast agent status change using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_agent_status_change(agent_id, old_status, new_status)


async def broadcast_agent_updated(agent_id: str, agent_data: dict) -> bool:
    """Broadcast agent update using global client. Fails silently."""
    client = await get_ws_client()
    if client is None:
        return False
    return await client.broadcast_agent_updated(agent_id, agent_data)


async def broadcast_adw_event_summary_update(
    adw_id: str,
    event_id: str,
    summary: str,
) -> bool:
    """
    Broadcast ADW event summary update (when AI summary is generated).

    This allows the frontend to update event summaries in real-time after
    the initial event is logged with a static fallback summary.

    Args:
        adw_id: ADW UUID
        event_id: Event/log entry UUID
        summary: AI-generated summary text
    """
    client = await get_ws_client()
    if client is None:
        return False
    return await client._send({
        "type": "adw_broadcast",
        "broadcast_type": "adw_event_summary_update",
        "adw_id": adw_id,
        "event_id": event_id,
        "summary": summary,
    })
