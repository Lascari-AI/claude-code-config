# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg>=0.29.0",
#   "python-dotenv>=1.0.0",
#   "websockets>=12.0",
# ]
# ///
"""
ADW Database Module - Database operations for AI Developer Workflows.

Provides functions to read/write ADW-related tables:
- ai_developer_workflows
- agent_logs
- system_logs

Usage:
    from adw_modules.adw_database import get_adw, write_agent_log, write_system_log
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Import WebSocket broadcast functions (resilient - fails silently)
from adw_modules.adw_websockets import (
    broadcast_agent_created,
    broadcast_agent_status_change,
    broadcast_agent_updated,
)

# =============================================================================
# CONNECTION POOL
# =============================================================================

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    return _pool


async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


# =============================================================================
# AI_DEVELOPER_WORKFLOWS TABLE
# =============================================================================


async def get_adw(adw_id: str) -> Optional[dict[str, Any]]:
    """
    Fetch an ADW record by ID.

    Args:
        adw_id: UUID string of the ADW

    Returns:
        Dict with ADW record or None if not found
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, orchestrator_agent_id, adw_name, workflow_type, description,
                   status, current_step, total_steps, completed_steps,
                   started_at, completed_at, duration_seconds,
                   input_data, output_data, error_message, error_step, error_count,
                   metadata, created_at, updated_at
            FROM ai_developer_workflows
            WHERE id = $1
            """,
            uuid.UUID(adw_id),
        )
        if row:
            result = dict(row)
            # Parse JSONB fields
            if isinstance(result.get("input_data"), str):
                result["input_data"] = json.loads(result["input_data"])
            if isinstance(result.get("output_data"), str):
                result["output_data"] = json.loads(result["output_data"])
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        return None


async def update_adw_status(
    adw_id: str,
    status: str,
    current_step: Optional[str] = None,
    completed_steps: Optional[int] = None,
    error_message: Optional[str] = None,
    error_step: Optional[str] = None,
) -> bool:
    """
    Update ADW status in ai_developer_workflows table.

    Args:
        adw_id: UUID string of the ADW
        status: New status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
        current_step: Current step slug
        completed_steps: Number of completed steps
        error_message: Error message if failed
        error_step: Step where error occurred

    Returns:
        True if updated, False if not found
    """
    async with get_connection() as conn:
        updates = ["status = $2", "updated_at = NOW()"]
        params: list[Any] = [uuid.UUID(adw_id), status]
        param_idx = 3

        if current_step is not None:
            updates.append(f"current_step = ${param_idx}")
            params.append(current_step)
            param_idx += 1

        if completed_steps is not None:
            updates.append(f"completed_steps = ${param_idx}")
            params.append(completed_steps)
            param_idx += 1

        if error_message is not None:
            updates.append(f"error_message = ${param_idx}")
            params.append(error_message)
            param_idx += 1

        if error_step is not None:
            updates.append(f"error_step = ${param_idx}")
            params.append(error_step)
            param_idx += 1

        # Status-specific updates
        if status == "in_progress":
            updates.append("started_at = COALESCE(started_at, NOW())")
        elif status in ("completed", "failed", "cancelled"):
            updates.append("completed_at = NOW()")
            updates.append("duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::integer")

        query = f"""
            UPDATE ai_developer_workflows
            SET {', '.join(updates)}
            WHERE id = $1
        """
        result = await conn.execute(query, *params)
        return result == "UPDATE 1"


# =============================================================================
# AGENTS TABLE
# =============================================================================


async def create_agent(
    orchestrator_agent_id: str,
    name: str,
    model: str,
    working_dir: Optional[str] = None,
    adw_id: Optional[str] = None,
    adw_step: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """
    Create an agent record in the agents table.

    Args:
        orchestrator_agent_id: Parent orchestrator agent UUID
        name: Agent name (e.g., "plan-agent", "build-agent")
        model: Model name (e.g., "claude-sonnet-4-5-20250929")
        working_dir: Working directory for the agent
        adw_id: Optional ADW ID this agent belongs to
        adw_step: Optional ADW step this agent is executing
        agent_id: Optional pre-generated UUID (if None, one is created)

    Returns:
        Agent ID (UUID string)
    """
    final_agent_id = agent_id or str(uuid.uuid4())

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO agents (
                id, orchestrator_agent_id, name, model, working_dir,
                adw_id, adw_step, status, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, 'idle', NOW(), NOW()
            )
            """,
            uuid.UUID(final_agent_id),
            uuid.UUID(orchestrator_agent_id),
            name,
            model,
            working_dir,
            adw_id,
            adw_step,
        )

    # Broadcast agent creation via WebSocket (fails silently if server unavailable)
    await broadcast_agent_created({
        "id": final_agent_id,
        "orchestrator_agent_id": orchestrator_agent_id,
        "name": name,
        "model": model,
        "status": "idle",
        "working_dir": working_dir,
        "adw_id": adw_id,
        "adw_step": adw_step,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0,
    })

    return final_agent_id


async def update_agent(
    agent_id: str,
    status: Optional[str] = None,
    session_id: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    total_cost: Optional[float] = None,
    old_status: Optional[str] = None,
) -> bool:
    """
    Update an agent record.

    Args:
        agent_id: Agent UUID string
        status: New status ('pending', 'running', 'completed', 'failed')
        session_id: Claude SDK session ID
        input_tokens: Input token count
        output_tokens: Output token count
        total_cost: Total cost in USD
        old_status: Previous status (for broadcasting status change)

    Returns:
        True if updated, False if not found
    """
    async with get_connection() as conn:
        updates = ["updated_at = NOW()"]
        params: list[Any] = [uuid.UUID(agent_id)]
        param_idx = 2

        if status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if session_id is not None:
            updates.append(f"session_id = ${param_idx}")
            params.append(session_id)
            param_idx += 1

        if input_tokens is not None:
            updates.append(f"input_tokens = ${param_idx}")
            params.append(input_tokens)
            param_idx += 1

        if output_tokens is not None:
            updates.append(f"output_tokens = ${param_idx}")
            params.append(output_tokens)
            param_idx += 1

        if total_cost is not None:
            updates.append(f"total_cost = ${param_idx}")
            params.append(total_cost)
            param_idx += 1

        query = f"""
            UPDATE agents
            SET {', '.join(updates)}
            WHERE id = $1
        """
        result = await conn.execute(query, *params)
        updated = result == "UPDATE 1"

    # Broadcast agent updates via WebSocket (fails silently if server unavailable)
    if updated:
        # Broadcast status change if status was updated
        if status is not None and old_status is not None:
            await broadcast_agent_status_change(agent_id, old_status, status)

        # Broadcast cost/token update if any cost fields were updated
        if input_tokens is not None or output_tokens is not None or total_cost is not None:
            await broadcast_agent_updated(agent_id, {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": total_cost,
                "session_id": session_id,
            })

    return updated


# =============================================================================
# AGENT_LOGS TABLE
# =============================================================================


async def write_agent_log(
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
    Write an entry to agent_logs table.

    Args:
        adw_id: ADW ID (UUID string)
        adw_step: Step slug (None for workflow-level events)
        event_category: 'hook', 'response', or 'adw_step'
        event_type: Event type (e.g., 'StepStart', 'StepEnd', 'PreToolUse')
        content: Event content/description
        agent_id: Optional agent ID (UUID string)
        payload: Optional JSON payload
        summary: Optional human-readable summary

    Returns:
        Log entry ID (UUID string)
    """
    log_id = str(uuid.uuid4())

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO agent_logs (
                id, agent_id, session_id, task_slug, adw_id, adw_step,
                entry_index, event_category, event_type, content, payload, summary, timestamp
            ) VALUES (
                $1, $2, NULL, NULL, $3, $4,
                0, $5, $6, $7, $8, $9, NOW()
            )
            """,
            uuid.UUID(log_id),
            uuid.UUID(agent_id) if agent_id else None,
            adw_id,
            adw_step,
            event_category,
            event_type,
            content,
            json.dumps(payload or {}),
            summary,
        )

    return log_id


async def update_log_summary(log_id: str, summary: str) -> bool:
    """
    Update the summary field of an agent_logs entry.

    Used by async summarization to update logs after AI summary is generated.

    Args:
        log_id: Log entry ID (UUID string)
        summary: AI-generated summary text

    Returns:
        True if updated, False if not found
    """
    async with get_connection() as conn:
        result = await conn.execute(
            """
            UPDATE agent_logs
            SET summary = $2
            WHERE id = $1
            """,
            uuid.UUID(log_id),
            summary,
        )
        return result == "UPDATE 1"


# =============================================================================
# SYSTEM_LOGS TABLE
# =============================================================================


async def write_system_log(
    adw_id: str,
    adw_step: Optional[str],
    level: str,
    message: str,
    file_path: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Write an entry to system_logs table.

    Args:
        adw_id: ADW ID (UUID string)
        adw_step: Step slug (None for workflow-level events)
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        message: Log message
        file_path: Optional source file path
        metadata: Optional JSON metadata

    Returns:
        Log entry ID (UUID string)
    """
    log_id = str(uuid.uuid4())

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO system_logs (
                id, file_path, adw_id, adw_step, level, message, metadata, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
            uuid.UUID(log_id),
            file_path,
            adw_id,
            adw_step,
            level,
            message,
            json.dumps(metadata or {}),
        )

    return log_id
