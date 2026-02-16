# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg>=0.29.0",
#   "python-dotenv>=1.0.0",
#   "websockets>=12.0",
# ]
# ///
"""
ADW Logging Module - Step lifecycle and event logging for AI Developer Workflows.

This module provides high-level functions to log ADW step boundaries and events.
Uses adw_database.py for all database operations.
Automatically broadcasts events via WebSocket for real-time frontend updates.

Usage:
    from adw_modules.adw_logging import log_step_start, log_step_end, log_adw_event

    await log_step_start(adw_id="uuid", adw_step="plan-feature")
    await log_step_end(adw_id="uuid", adw_step="plan-feature", status="success")

WebSocket Integration:
    Events are automatically broadcast to the frontend via WebSocket.
    Broadcasting is resilient - it fails silently if the server is unavailable.
    Use init_logging() at workflow start to establish WebSocket connection.
    Use close_logging() at workflow end to clean up.
"""

from __future__ import annotations

from typing import Any, Optional

from .adw_database import (
    close_pool,
    write_agent_log,
    write_system_log,
)
from .adw_database import (
    update_adw_status as db_update_adw_status,
)
from .adw_websockets import (
    broadcast_adw_event as ws_broadcast_adw_event,
)
from .adw_websockets import (
    broadcast_adw_status as ws_broadcast_adw_status,
)
from .adw_websockets import (
    broadcast_adw_step_change as ws_broadcast_adw_step_change,
)
from .adw_websockets import (
    close_ws_client,
    init_ws_client,
)

# Re-export close_pool for workflows to clean up
__all__ = [
    "init_logging",
    "close_logging",
    "log_step_start",
    "log_step_end",
    "log_adw_event",
    "log_system_event",
    "update_adw_status",
    "close_pool",
]


# =============================================================================
# INITIALIZATION / CLEANUP
# =============================================================================


async def init_logging(verbose: bool = False):
    """
    Initialize logging with WebSocket connection for real-time updates.

    Call this at the start of your workflow to establish the WebSocket
    connection. This is optional - logging will still work without it,
    but events won't be broadcast in real-time.

    Args:
        verbose: If True, print WebSocket connection status messages
    """
    await init_ws_client(verbose=verbose)


async def close_logging():
    """
    Clean up logging resources (database pool + WebSocket connection).

    Call this at the end of your workflow to properly close connections.
    """
    await close_ws_client()
    await close_pool()


# =============================================================================
# STEP LIFECYCLE LOGGING
# =============================================================================


async def log_step_start(
    adw_id: str,
    adw_step: str,
    agent_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    summary: Optional[str] = None,
) -> str:
    """
    Log the start of an ADW step.

    Writes to database AND broadcasts via WebSocket for real-time updates.

    Args:
        adw_id: The ADW ID (UUID as string)
        adw_step: Step slug (e.g., "plan-feature", "build-feature")
        agent_id: Optional agent ID driving this step
        payload: Optional payload with step configuration
        summary: Optional human-readable summary

    Returns:
        The log entry ID (UUID as string)
    """
    default_summary = f"Step '{adw_step}' started"

    log_id = await write_agent_log(
        adw_id=adw_id,
        adw_step=adw_step,
        event_category="adw_step",
        event_type="StepStart",
        content=f"StepStart: {adw_step}",
        agent_id=agent_id,
        payload=payload,
        summary=summary or default_summary,
    )

    # Broadcast step change via WebSocket (fails silently if unavailable)
    await ws_broadcast_adw_step_change(
        adw_id=adw_id,
        step=adw_step,
        event_type="StepStart",
        payload=payload,
    )

    return log_id


async def log_step_end(
    adw_id: str,
    adw_step: str,
    agent_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    summary: Optional[str] = None,
    status: str = "success",
    duration_ms: Optional[int] = None,
) -> str:
    """
    Log the end of an ADW step.

    Writes to database AND broadcasts via WebSocket for real-time updates.

    Args:
        adw_id: The ADW ID (UUID as string)
        adw_step: Step slug (e.g., "plan-feature", "build-feature")
        agent_id: Optional agent ID that drove this step
        payload: Optional payload with step results
        summary: Optional human-readable summary
        status: Step completion status ("success", "failed", "skipped")
        duration_ms: Optional step duration in milliseconds

    Returns:
        The log entry ID (UUID as string)
    """
    default_summary = f"Step '{adw_step}' completed with status: {status}"

    # Build payload with duration and status
    step_payload = payload.copy() if payload else {}
    step_payload["status"] = status
    if duration_ms is not None:
        step_payload["duration_ms"] = duration_ms

    log_id = await write_agent_log(
        adw_id=adw_id,
        adw_step=adw_step,
        event_category="adw_step",
        event_type="StepEnd",
        content=f"StepEnd: {adw_step} ({status})",
        agent_id=agent_id,
        payload=step_payload,
        summary=summary or default_summary,
    )

    # Broadcast step change via WebSocket (fails silently if unavailable)
    await ws_broadcast_adw_step_change(
        adw_id=adw_id,
        step=adw_step,
        event_type="StepEnd",
        payload=step_payload,
    )

    return log_id


# =============================================================================
# GENERIC EVENT LOGGING
# =============================================================================


async def log_adw_event(
    adw_id: str,
    adw_step: Optional[str],
    event_category: str,
    event_type: str,
    content: str,
    agent_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    summary: Optional[str] = None,
) -> str:
    """
    Log a generic ADW event to agent_logs.

    Writes to database AND broadcasts via WebSocket for real-time updates.

    Args:
        adw_id: The ADW ID
        adw_step: Optional step slug (None for workflow-level events)
        event_category: Category ('hook', 'response', 'adw_step')
        event_type: Event type (e.g., 'PreToolUse', 'text', 'StepStart')
        content: Event content/description
        agent_id: Optional agent ID
        payload: Optional event payload
        summary: Optional human-readable summary

    Returns:
        The log entry ID
    """
    log_id = await write_agent_log(
        adw_id=adw_id,
        adw_step=adw_step,
        event_category=event_category,
        event_type=event_type,
        content=content,
        agent_id=agent_id,
        payload=payload,
        summary=summary,
    )

    # Broadcast event via WebSocket (fails silently if unavailable)
    await ws_broadcast_adw_event(
        adw_id=adw_id,
        event_data={
            "id": log_id,
            "adw_id": adw_id,
            "adw_step": adw_step,
            "event_category": event_category,
            "event_type": event_type,
            "content": content,
            "agent_id": agent_id,
            "payload": payload,
            "summary": summary,
        },
    )

    return log_id


async def log_system_event(
    adw_id: str,
    adw_step: Optional[str],
    level: str,
    message: str,
    file_path: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Log a system event to both system_logs AND agent_logs (for swimlane display).

    Writes to both database tables AND broadcasts via WebSocket for real-time updates.
    The agent_logs entry ensures system events appear as squares in the ADW swimlanes.

    Args:
        adw_id: The ADW ID
        adw_step: Optional step slug
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        message: Log message
        file_path: Optional source file path
        metadata: Optional additional metadata

    Returns:
        The log entry ID (from agent_logs)
    """
    # Write to system_logs table ONLY (not agent_logs)
    # The backend /adws/{adw_id}/events endpoint fetches from both tables
    log_id = await write_system_log(
        adw_id=adw_id,
        adw_step=adw_step,
        level=level,
        message=message,
        file_path=file_path,
        metadata=metadata,
    )

    # Broadcast system event via WebSocket (fails silently if unavailable)
    await ws_broadcast_adw_event(
        adw_id=adw_id,
        event_data={
            "id": log_id,
            "adw_id": adw_id,
            "adw_step": adw_step,
            "event_category": "system",
            "event_type": f"System{level.capitalize()}",
            "content": message,
            "summary": f"[{level}] {message[:100]}{'...' if len(message) > 100 else ''}",
            "payload": {
                "level": level,
                "file_path": file_path,
                **(metadata or {}),
            },
        },
    )

    return log_id


# =============================================================================
# ADW STATUS UPDATES
# =============================================================================


async def update_adw_status(
    adw_id: str,
    status: str,
    current_step: Optional[str] = None,
    completed_steps: Optional[int] = None,
    error_message: Optional[str] = None,
    error_step: Optional[str] = None,
) -> bool:
    """
    Update the ADW status in ai_developer_workflows table.

    Updates database AND broadcasts via WebSocket for real-time updates.

    Args:
        adw_id: The ADW ID
        status: New status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
        current_step: Current step slug
        completed_steps: Number of completed steps
        error_message: Error message if failed
        error_step: Step where error occurred

    Returns:
        True if updated, False if not found
    """
    result = await db_update_adw_status(
        adw_id=adw_id,
        status=status,
        current_step=current_step,
        completed_steps=completed_steps,
        error_message=error_message,
        error_step=error_step,
    )

    # Broadcast status change via WebSocket (fails silently if unavailable)
    await ws_broadcast_adw_status(
        adw_id=adw_id,
        status=status,
        current_step=current_step,
        completed_steps=completed_steps,
        error_message=error_message,
    )

    return result
