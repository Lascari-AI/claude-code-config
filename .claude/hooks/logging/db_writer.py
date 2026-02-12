"""
Database Writer for Hook Logger

Provides async database writing for hook events.
Writes AgentLog entries to PostgreSQL via session_db.

This module is designed to be non-blocking - errors are logged but don't
prevent the JSONL file writing from succeeding.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any
from uuid import UUID

# Add the apps/core directory to the path for imports
_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
_apps_core_path = os.path.join(_project_dir, "apps", "core")
if _apps_core_path not in sys.path:
    sys.path.insert(0, _apps_core_path)


async def write_event_to_db(input_data: dict[str, Any]) -> bool:
    """
    Write a hook event to the database.

    This function imports session_db lazily to avoid import errors
    when the database is not configured.

    Args:
        input_data: The hook payload with event details

    Returns:
        True if successful, False otherwise
    """
    try:
        # Lazy import to avoid errors when DB is not configured
        from session_db import (
            AgentLogCreate,
            create_agent_log,
            get_async_session,
        )

        # Extract required identifiers
        agent_id = input_data.get("agent_id")
        session_id = input_data.get("session_id")

        # If no agent_id or session_id, we can't write to DB
        if not agent_id or not session_id:
            # Not an error - just no DB context
            return False

        # Validate UUIDs
        try:
            agent_uuid = UUID(agent_id) if isinstance(agent_id, str) else agent_id
            session_uuid = (
                UUID(session_id) if isinstance(session_id, str) else session_id
            )
        except (ValueError, TypeError):
            # Invalid UUIDs - skip DB write
            return False

        # Build the log entry
        hook_event_name = input_data.get("hook_event_name", "unknown")
        event_category = _categorize_event(hook_event_name)
        event_type = hook_event_name

        # Extract tool-specific fields
        tool_name = input_data.get("tool_name")
        tool_input = input_data.get("tool_input")
        tool_output = input_data.get("tool_output")

        # Build content from relevant fields
        content = _extract_content(input_data)

        # Build payload (full hook data minus redundant fields)
        payload = _build_payload(input_data)

        log_create = AgentLogCreate(
            agent_id=agent_uuid,
            session_id=session_uuid,
            sdk_session_id=input_data.get("sdk_session_id"),
            event_category=event_category,
            event_type=event_type,
            content=content,
            payload=payload,
            tool_name=tool_name,
            tool_input=tool_input if isinstance(tool_input, dict) else None,
            tool_output=str(tool_output) if tool_output else None,
            checkpoint_id=input_data.get("checkpoint_id"),
        )

        # Write to database
        async with get_async_session() as db:
            await create_agent_log(db, log_create)

        return True

    except ImportError as e:
        # session_db not available - this is expected in some environments
        print(f"DB writer: session_db not available: {e}", file=sys.stderr)
        return False

    except Exception as e:
        # Log error but don't fail
        print(f"DB writer error: {e}", file=sys.stderr)
        return False


def _categorize_event(hook_event_name: str) -> str:
    """
    Categorize an event based on the hook event name.

    Returns: 'hook', 'response', or 'phase'
    """
    hook_events = {
        "PreToolUse",
        "PostToolUse",
        "ToolError",
        "Notification",
        "Stop",
    }

    phase_events = {
        "phase_start",
        "phase_end",
        "phase_transition",
    }

    if hook_event_name in hook_events:
        return "hook"
    elif hook_event_name in phase_events:
        return "phase"
    else:
        return "response"


def _extract_content(input_data: dict[str, Any]) -> str | None:
    """Extract text content from hook payload."""
    # Check common content fields
    if "content" in input_data:
        return str(input_data["content"])
    if "message" in input_data:
        return str(input_data["message"])
    if "text" in input_data:
        return str(input_data["text"])
    if "output" in input_data:
        return str(input_data["output"])
    return None


def _build_payload(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build the payload dict, excluding redundant fields.
    """
    # Fields to exclude from payload (already stored elsewhere)
    exclude_fields = {
        "agent_id",
        "session_id",
        "sdk_session_id",
        "tool_name",
        "tool_input",
        "tool_output",
        "checkpoint_id",
        "content",
        "message",
        "text",
    }

    return {k: v for k, v in input_data.items() if k not in exclude_fields}


def write_event_sync(input_data: dict[str, Any]) -> bool:
    """
    Synchronous wrapper for write_event_to_db.

    Creates an event loop and runs the async function.
    Used when called from synchronous hook code.

    Args:
        input_data: The hook payload

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - create a task
            # This shouldn't happen in hook context, but handle it
            future = asyncio.ensure_future(write_event_to_db(input_data))
            # Can't wait for it in this context, just fire and forget
            return True
        except RuntimeError:
            # No running loop - create one
            return asyncio.run(write_event_to_db(input_data))

    except Exception as e:
        print(f"DB writer sync error: {e}", file=sys.stderr)
        return False
