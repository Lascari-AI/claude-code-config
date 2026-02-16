"""
ORCHESTRATOR Hook Implementations for Claude SDK Events

Captures hook events from the orchestrator agent itself (not subagents),
logs to orchestrator_chat table, and broadcasts via WebSocket.

Key Features:
- Tracks orchestrator's own tool usage (create_agent, command_agent, etc.)
- Separate from subagent hooks to reduce coupling
- Broadcasts as orchestrator_chat events
- Errors throw loudly for debugging

Used by: orchestrator_service.py when running the main orchestrator agent
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from .database import insert_chat_message
from .logger import OrchestratorLogger
from .websocket_manager import WebSocketManager

# Type alias for hook callbacks
HookCallback = Callable[[Dict[str, Any], Optional[str], Any], Awaitable[Dict[str, Any]]]


# ═══════════════════════════════════════════════════════════
# Hook Factory Functions for Orchestrator Agent
# ═══════════════════════════════════════════════════════════


def create_orchestrator_pre_tool_hook(
    orchestrator_agent_id: uuid.UUID,
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create PreToolUse hook for orchestrator agent tool calls.

    Logs orchestrator's tool usage (create_agent, command_agent, etc.) to
    orchestrator_chat table as tool_use events.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        logger: Logger instance
        ws_manager: WebSocket manager for broadcasting

    Returns:
        Async hook callable
    """
    async def hook(
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """PreToolUse hook implementation for orchestrator"""
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        logger.info(
            f"[OrchestratorHook:PreToolUse] Tool={tool_name} ID={tool_use_id}"
        )

        # Insert orchestrator tool use to chat table - THROW ERRORS LOUDLY
        chat_id = await insert_chat_message(
            orchestrator_agent_id=orchestrator_agent_id,
            sender_type="orchestrator",
            receiver_type="system",
            message=f"Using tool: {tool_name}",
            agent_id=None,
            metadata={
                "type": "tool_use",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_use_id": tool_use_id
            }
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast_orchestrator_chat({
            "id": str(chat_id),
            "sender_type": "orchestrator",
            "receiver_type": "system",
            "message": f"Using tool: {tool_name}",
            "metadata": {
                "type": "tool_use",
                "tool_name": tool_name
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        return {}

    return hook


def create_orchestrator_post_tool_hook(
    orchestrator_agent_id: uuid.UUID,
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create PostToolUse hook for orchestrator agent tool results.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        logger: Logger instance
        ws_manager: WebSocket manager

    Returns:
        Async hook callable
    """
    async def hook(
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """PostToolUse hook implementation for orchestrator"""
        tool_name = input_data.get("tool_name", "unknown")
        is_error = input_data.get("is_error", False)

        logger.info(
            f"[OrchestratorHook:PostToolUse] Tool={tool_name} Error={is_error}"
        )

        # Log tool completion (optional - could be noisy)
        # For now, just log without inserting to database

        return {}

    return hook


def create_orchestrator_stop_hook(
    orchestrator_agent_id: uuid.UUID,
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create Stop hook for orchestrator agent session stops.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        logger: Logger instance
        ws_manager: WebSocket manager

    Returns:
        Async hook callable
    """
    async def hook(
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Stop hook implementation for orchestrator"""
        reason = input_data.get("reason", "unknown")
        num_turns = input_data.get("num_turns", 0)

        logger.info(
            f"[OrchestratorHook:Stop] Reason={reason} Turns={num_turns}"
        )

        return {}

    return hook
