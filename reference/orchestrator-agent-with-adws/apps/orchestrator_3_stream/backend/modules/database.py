"""
Database Connection Pool and Operations

Consolidated database module for orchestrator_3_stream providing:
- Connection pool management (asyncpg)
- Orchestrator agent operations (singleton pattern)
- Chat message operations (three-way communication)

Reference:
- apps/orchestrator_1_term/modules/database/database.py
- apps/orchestrator_1_term/modules/database/orchestrator_agents_db.py
- apps/orchestrator_1_term/modules/database/orchestrator_chat_db.py
"""

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg

from .config import (
    DEFAULT_AGENT_LOG_LIMIT,
    DEFAULT_SYSTEM_LOG_LIMIT,
)
from .orch_database_models import Agent

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


# ═══════════════════════════════════════════════════════════
# CONNECTION POOL MANAGEMENT
# ═══════════════════════════════════════════════════════════


async def init_pool(
    database_url: str = None, min_size: int = 5, max_size: int = 20
) -> asyncpg.Pool:
    """
    Initialize asyncpg connection pool.

    Args:
        database_url: PostgreSQL connection string (from env if not provided)
        min_size: Minimum pool size
        max_size: Maximum pool size

    Returns:
        asyncpg.Pool instance

    Raises:
        ValueError: If DATABASE_URL is not provided and not set in environment
    """
    global _pool

    if _pool is not None:
        return _pool

    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")

    _pool = await asyncpg.create_pool(
        url, min_size=min_size, max_size=max_size, command_timeout=60
    )

    return _pool


def get_pool() -> asyncpg.Pool:
    """
    Get existing connection pool.

    Returns:
        asyncpg.Pool instance

    Raises:
        RuntimeError: If pool not initialized
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool


async def close_pool():
    """
    Close connection pool.

    Safely closes all connections in the pool and resets the global pool variable.
    This should be called during application shutdown.
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """
    Context manager for database connections.

    Acquires a connection from the pool and ensures it's properly released.

    Usage:
        async with get_connection() as conn:
            await conn.execute("SELECT ...")

    Yields:
        asyncpg.Connection: Database connection from the pool

    Raises:
        RuntimeError: If pool not initialized
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR AGENT OPERATIONS
# ═══════════════════════════════════════════════════════════


async def get_or_create_orchestrator(
    system_prompt: str, working_dir: str
) -> Dict[str, Any]:
    """
    Get existing orchestrator or create new one.

    Ensures only one orchestrator exists (singleton pattern).
    If an existing orchestrator is found (WHERE archived=false), returns it.
    Otherwise, creates a new orchestrator with default values.

    Args:
        system_prompt: Orchestrator's system prompt
        working_dir: Orchestrator's working directory path

    Returns:
        Dictionary containing orchestrator data with all fields from database

    Raises:
        asyncpg.PostgresError: For database errors

    Example:
        >>> orch = await get_or_create_orchestrator(
        ...     system_prompt="You are the orchestrator agent...",
        ...     working_dir="/path/to/project"
        ... )
    """
    async with get_connection() as conn:
        # Try to get existing orchestrator (singleton pattern)
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE archived = false LIMIT 1"
        )

        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result

        # Create new orchestrator
        orch_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO orchestrator_agents (
                id, system_prompt, status, working_dir,
                metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5::jsonb, NOW(), NOW())
        """,
            orch_id,
            system_prompt,
            "idle",
            working_dir,
            json.dumps({}),
        )

        # Fetch and return the created orchestrator
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE id = $1", orch_id
        )
        result = dict(row)
        if isinstance(result.get("metadata"), str):
            result["metadata"] = json.loads(result["metadata"])
        return result


async def create_new_orchestrator(
    system_prompt: str, working_dir: str
) -> Dict[str, Any]:
    """
    Always create a new orchestrator (no singleton check).

    Creates a new orchestrator with a fresh session ID, regardless of
    whether one already exists. Used when explicitly starting a new session.

    Args:
        system_prompt: Orchestrator's system prompt
        working_dir: Orchestrator's working directory path

    Returns:
        Dictionary containing orchestrator data with all fields from database

    Example:
        >>> orch = await create_new_orchestrator(
        ...     system_prompt="You are the orchestrator agent...",
        ...     working_dir="/path/to/project"
        ... )
    """
    async with get_connection() as conn:
        # Generate new ID (session_id will be NULL initially, set by Claude SDK later)
        orch_id = uuid.uuid4()

        # Create new orchestrator with NULL session_id (will be populated after first interaction)
        await conn.execute(
            """
            INSERT INTO orchestrator_agents (
                id, session_id, system_prompt, status, working_dir,
                metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, NOW(), NOW())
        """,
            orch_id,
            None,  # session_id starts as NULL, will be set by Claude SDK
            system_prompt,
            "idle",
            working_dir,
            json.dumps({}),
        )

        # Fetch and return the created orchestrator
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE id = $1", orch_id
        )
        result = dict(row)
        if isinstance(result.get("metadata"), str):
            result["metadata"] = json.loads(result["metadata"])
        return result


async def get_orchestrator() -> Optional[Dict[str, Any]]:
    """
    Get the active orchestrator.

    Retrieves the current orchestrator record (WHERE archived=false).
    Returns None if no orchestrator exists.

    Returns:
        Dictionary containing orchestrator data or None if not found

    Example:
        >>> orch = await get_orchestrator()
        >>> if orch:
        ...     print(f"Orchestrator status: {orch['status']}")
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE archived = false LIMIT 1"
        )
        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        return None


async def get_orchestrator_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get orchestrator by session ID.

    Validates that a session ID exists and returns the orchestrator data.
    Used when resuming an existing orchestrator session.

    Args:
        session_id: Claude SDK session ID to look up

    Returns:
        Dictionary containing orchestrator data or None if session not found

    Example:
        >>> orch = await get_orchestrator_by_session("sess_abc123...")
        >>> if orch:
        ...     print(f"Resuming session: {orch['session_id']}")
        ... else:
        ...     raise ValueError(f"Invalid session ID")
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE session_id = $1 AND archived = false",
            session_id,
        )
        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        return None


async def get_orchestrator_by_id(orchestrator_agent_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get orchestrator by ID.

    Retrieves a specific orchestrator record by its UUID.
    Used to refresh orchestrator data from database.

    Args:
        orchestrator_agent_id: UUID of the orchestrator to retrieve

    Returns:
        Dictionary containing orchestrator data or None if not found

    Example:
        >>> orch = await get_orchestrator_by_id(uuid.UUID("..."))
        >>> if orch:
        ...     print(f"Orchestrator status: {orch['status']}")
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM orchestrator_agents WHERE id = $1 AND archived = false",
            orchestrator_agent_id,
        )
        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        return None


async def update_orchestrator_session(
    orchestrator_agent_id: uuid.UUID, session_id: str
) -> Optional[Dict[str, Any]]:
    """
    Update orchestrator's Claude SDK session ID.

    ONLY updates if the current session_id is NULL (first-time session setup).
    This prevents overwriting existing session_ids and violating UNIQUE constraint.

    Args:
        orchestrator_agent_id: UUID of the orchestrator to update
        session_id: Claude SDK session ID

    Returns:
        Dictionary containing updated orchestrator data or None if not found

    Example:
        >>> updated_orch = await update_orchestrator_session(orch_id, session.id)
        >>> if updated_orch:
        ...     print(f"Session ID updated: {updated_orch['session_id']}")
    """
    async with get_connection() as conn:
        # Execute the UPDATE
        await conn.execute(
            """
            UPDATE orchestrator_agents
            SET session_id = $1, updated_at = NOW()
            WHERE id = $2 AND session_id IS NULL
        """,
            session_id,
            orchestrator_agent_id,
        )

        # Fetch and return updated row
        row = await conn.fetchrow(
            """
            SELECT * FROM orchestrator_agents
            WHERE id = $1 AND archived = false
            """,
            orchestrator_agent_id,
        )

        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        return None


async def update_orchestrator_costs(
    orchestrator_agent_id: uuid.UUID,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
) -> Dict[str, Any]:
    """
    Update orchestrator's cumulative token usage and costs.

    Uses incremental updates (adds to existing values).
    IMPORTANT: Updates ONLY the specified orchestrator by ID, not all agents.

    Args:
        orchestrator_agent_id: UUID of the specific orchestrator to update
        input_tokens: Number of input tokens from this execution
        output_tokens: Number of output tokens from this execution
        cost_usd: Cost in USD from this execution

    Returns:
        Dictionary with updated values and row count

    Example:
        >>> await update_orchestrator_costs(
        ...     orchestrator_agent_id=uuid.UUID("..."),
        ...     input_tokens=message.usage.input_tokens,
        ...     output_tokens=message.usage.output_tokens,
        ...     cost_usd=message.usage.total_cost_usd
        ... )
    """
    async with get_connection() as conn:
        # Execute the UPDATE - with ID matching to only update THIS orchestrator
        result = await conn.execute(
            """
            UPDATE orchestrator_agents
            SET input_tokens = input_tokens + $1,
                output_tokens = output_tokens + $2,
                total_cost = total_cost + $3,
                updated_at = NOW()
            WHERE id = $4 AND archived = false
        """,
            input_tokens,
            output_tokens,
            cost_usd,
            orchestrator_agent_id,
        )

        # Get updated row to verify
        row = await conn.fetchrow(
            """
            SELECT id, input_tokens, output_tokens, total_cost, updated_at
            FROM orchestrator_agents
            WHERE id = $1 AND archived = false
            """,
            orchestrator_agent_id,
        )

        if row:
            return {
                "success": True,
                "rows_updated": int(result.split()[-1]) if result else 0,
                "id": str(row["id"]),
                "input_tokens": row["input_tokens"],
                "output_tokens": row["output_tokens"],
                "total_cost": float(row["total_cost"]),
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
        else:
            return {
                "success": False,
                "rows_updated": 0,
                "error": f"No orchestrator found with id={orchestrator_agent_id} (archived=false)",
            }


async def update_orchestrator_status(
    orchestrator_agent_id: uuid.UUID, status: str
) -> None:
    """
    Update orchestrator's status.

    IMPORTANT: Updates ONLY the specified orchestrator by ID, not all agents.

    Args:
        orchestrator_agent_id: UUID of the specific orchestrator to update
        status: New status - "idle", "executing", "waiting", "blocked", "complete"

    Example:
        >>> await update_orchestrator_status(orch_id, "executing")
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE orchestrator_agents
            SET status = $1, updated_at = NOW()
            WHERE id = $2 AND archived = false
        """,
            status,
            orchestrator_agent_id,
        )


async def update_orchestrator_metadata(
    orchestrator_agent_id: uuid.UUID, metadata_updates: Dict[str, Any]
) -> None:
    """
    Update orchestrator metadata fields using JSONB merge.

    Merges provided metadata with existing metadata without replacing it.
    This allows partial updates to specific metadata fields.

    IMPORTANT: Updates ONLY the specified orchestrator by ID, not all agents.

    Args:
        orchestrator_agent_id: UUID of the specific orchestrator to update
        metadata_updates: Dictionary of metadata fields to add/update

    Example:
        >>> await update_orchestrator_metadata(
        ...     orchestrator_agent_id=uuid.UUID("..."),
        ...     metadata_updates={
        ...         "system_message_info": {
        ...             "session_id": "abc123",
        ...             "cwd": "/path/to/workspace"
        ...         }
        ...     }
        ... )
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE orchestrator_agents
            SET metadata = metadata || $1::jsonb, updated_at = NOW()
            WHERE id = $2 AND archived = false
            """,
            json.dumps(metadata_updates),
            orchestrator_agent_id,
        )


# ═══════════════════════════════════════════════════════════
# CHAT MESSAGE OPERATIONS
# ═══════════════════════════════════════════════════════════


async def insert_chat_message(
    orchestrator_agent_id: uuid.UUID,
    sender_type: str,
    receiver_type: str,
    message: str,
    agent_id: Optional[uuid.UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> uuid.UUID:
    """
    Insert a new chat message into orchestrator_chat table.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        sender_type: "user", "orchestrator", or "agent"
        receiver_type: "user", "orchestrator", or "agent"
        message: The message text
        agent_id: UUID of command agent (required when sender/receiver is "agent")
        metadata: Optional JSONB metadata

    Returns:
        UUID of the created chat message

    Raises:
        ValueError: If sender_type or receiver_type is invalid
        ValueError: If agent_id validation fails

    Examples:
        >>> # User → Orchestrator
        >>> msg_id = await insert_chat_message(
        ...     orchestrator_agent_id=orch_id,
        ...     sender_type="user",
        ...     receiver_type="orchestrator",
        ...     message="Create an agent called builder"
        ... )
        >>>
        >>> # Orchestrator → User
        >>> msg_id = await insert_chat_message(
        ...     orchestrator_agent_id=orch_id,
        ...     sender_type="orchestrator",
        ...     receiver_type="user",
        ...     message="Created builder agent successfully",
        ...     metadata={"tools_used": ["create_agent"]}
        ... )
    """
    valid_types = ("user", "orchestrator", "agent")

    if sender_type not in valid_types:
        raise ValueError(
            f"sender_type must be one of {valid_types}, got: {sender_type}"
        )

    if receiver_type not in valid_types:
        raise ValueError(
            f"receiver_type must be one of {valid_types}, got: {receiver_type}"
        )

    # Validate agent_id requirements
    agent_involved = sender_type == "agent" or receiver_type == "agent"
    if agent_involved and agent_id is None:
        raise ValueError(
            "agent_id is required when sender_type or receiver_type is 'agent'"
        )
    if not agent_involved and agent_id is not None:
        raise ValueError(
            "agent_id must be None when neither sender nor receiver is 'agent'"
        )

    message_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO orchestrator_chat (
                id, orchestrator_agent_id, sender_type, receiver_type,
                message, agent_id, metadata,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, NOW(), NOW())
        """,
            message_id,
            orchestrator_agent_id,
            sender_type,
            receiver_type,
            message,
            agent_id,
            json.dumps(metadata or {}),
        )

    return message_id


async def get_chat_history(
    orchestrator_agent_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: int = 0,
    agent_id: Optional[uuid.UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Get chat history for an orchestrator agent.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        limit: Maximum number of messages to return (None = all)
        offset: Number of messages to skip (for pagination)
        agent_id: Optional - filter messages involving specific command agent

    Returns:
        List of chat message dictionaries, ordered by created_at ASC (oldest first)
        When limit is used, returns the MOST RECENT messages (DESC order, then reversed)

    Example:
        >>> history = await get_chat_history(orch_id, limit=50)
        >>> for msg in history:
        ...     print(f"[{msg['sender_type']} → {msg['receiver_type']}] {msg['message']}")
    """
    async with get_connection() as conn:
        query = """
            SELECT id, orchestrator_agent_id, sender_type, receiver_type,
                   message, agent_id, metadata,
                   created_at, updated_at
            FROM orchestrator_chat
            WHERE orchestrator_agent_id = $1
        """

        params = [orchestrator_agent_id]

        # Add agent_id filter if provided
        if agent_id is not None:
            query += " AND agent_id = $2"
            params.append(agent_id)

        # CRITICAL FIX: Order by DESC to get newest messages when using LIMIT
        # Then reverse the array to return in chronological order (oldest first)
        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            result = dict(row)
            # Parse metadata JSONB if it's a string
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)

        # Reverse to return in chronological order (oldest first)
        # Since we queried DESC to get the most recent messages with LIMIT
        results.reverse()

        return results


async def get_turn_count(orchestrator_agent_id: uuid.UUID) -> int:
    """
    Get the turn count (number of messages) for an orchestrator agent.

    The turn count is derived from the total number of messages
    (both user and orchestrator) in the conversation history.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent

    Returns:
        Integer count of total messages in the conversation

    Example:
        >>> turn = await get_turn_count(orch_id)
        >>> print(f"[{turn}] You: ")
    """
    async with get_connection() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM orchestrator_chat
            WHERE orchestrator_agent_id = $1
        """,
            orchestrator_agent_id,
        )

        return result or 0


async def delete_chat_history(orchestrator_agent_id: uuid.UUID) -> int:
    """
    Delete all chat history for an orchestrator agent.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent

    Returns:
        Number of messages deleted

    Example:
        >>> deleted = await delete_chat_history(orch_id)
        >>> print(f"Deleted {deleted} messages")
    """
    async with get_connection() as conn:
        result = await conn.execute(
            """
            DELETE FROM orchestrator_chat
            WHERE orchestrator_agent_id = $1
        """,
            orchestrator_agent_id,
        )

        # Extract count from result string "DELETE N"
        return int(result.split()[1]) if result else 0


# ═══════════════════════════════════════════════════════════
# AGENT CRUD OPERATIONS
# ═══════════════════════════════════════════════════════════


async def create_agent(
    orchestrator_agent_id: uuid.UUID,
    name: str,
    model: str,
    system_prompt: str,
    working_dir: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> uuid.UUID:
    """
    Create new agent in database.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent that owns this command agent
        name: Agent identifier/name (unique per orchestrator)
        model: Claude model ID (e.g., "claude-sonnet-4-5-20250929")
        system_prompt: Agent's custom system prompt
        working_dir: Agent's working directory path
        metadata: Optional JSONB metadata (allowed_tools, disallowed_tools, etc.)

    Returns:
        UUID of created agent

    Raises:
        asyncpg.UniqueViolationError: If agent name already exists for this orchestrator
        asyncpg.PostgresError: For other database errors
    """
    agent_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO agents (
                id, orchestrator_agent_id, name, model, system_prompt, working_dir,
                status, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, NOW(), NOW())
        """,
            agent_id,
            orchestrator_agent_id,
            name,
            model,
            system_prompt,
            working_dir,
            "idle",
            json.dumps(metadata or {}),
        )

    return agent_id


async def get_agent(agent_id: uuid.UUID) -> Optional[Agent]:
    """
    Get agent by ID.

    Args:
        agent_id: UUID of the agent

    Returns:
        Agent Pydantic model or None if not found or archived
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM agents WHERE id = $1 AND archived = false", agent_id
        )
        if not row:
            return None

        return Agent(**dict(row))


async def get_agent_by_name(orchestrator_agent_id: uuid.UUID, name: str) -> Optional[Agent]:
    """
    Get agent by name (scoped to orchestrator).

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        name: Agent name (unique per orchestrator)

    Returns:
        Agent Pydantic model or None if not found or archived
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM agents
            WHERE orchestrator_agent_id = $1
              AND name = $2
              AND archived = false
            """,
            orchestrator_agent_id,
            name
        )
        if not row:
            return None

        return Agent(**dict(row))


async def list_agents(orchestrator_agent_id: uuid.UUID, archived: bool = False) -> List[Agent]:
    """
    List all agents for this orchestrator.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        archived: If True, return archived agents. If False, return active agents.

    Returns:
        List of Agent Pydantic models, ordered by creation date (newest first)
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM agents
            WHERE orchestrator_agent_id = $1
              AND archived = $2
            ORDER BY created_at DESC
            """,
            orchestrator_agent_id,
            archived,
        )
        return [Agent(**dict(row)) for row in rows]


async def update_agent_status(agent_id: uuid.UUID, status: str) -> None:
    """
    Update agent status.

    Args:
        agent_id: UUID of the agent
        status: New status ("idle" | "executing" | "waiting" | "blocked" | "complete")
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE agents SET status = $1, updated_at = NOW() WHERE id = $2",
            status,
            agent_id,
        )


async def update_agent_session(agent_id: uuid.UUID, session_id: Optional[str]) -> None:
    """
    Update agent's Claude SDK session ID.

    Args:
        agent_id: UUID of the agent
        session_id: Claude SDK session ID or None to clear
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE agents SET session_id = $1, updated_at = NOW() WHERE id = $2",
            session_id,
            agent_id,
        )


async def update_agent_costs(
    agent_id: uuid.UUID, input_tokens: int, output_tokens: int, cost_usd: float
) -> None:
    """
    Update agent's cumulative token usage and costs.

    Uses incremental updates (adds to existing values).

    Args:
        agent_id: UUID of the agent
        input_tokens: Number of input tokens from this execution
        output_tokens: Number of output tokens from this execution
        cost_usd: Cost in USD from this execution
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE agents
            SET input_tokens = input_tokens + $1,
                output_tokens = output_tokens + $2,
                total_cost = total_cost + $3,
                updated_at = NOW()
            WHERE id = $4
        """,
            input_tokens,
            output_tokens,
            cost_usd,
            agent_id,
        )


async def reset_agent_tokens(agent_id: uuid.UUID) -> None:
    """
    Reset agent's token usage and costs to zero.

    Called when /compact is triggered to reset context window tracking.

    Args:
        agent_id: UUID of the agent to reset
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE agents
            SET input_tokens = 0,
                output_tokens = 0,
                total_cost = 0.0,
                updated_at = NOW()
            WHERE id = $1
        """,
            agent_id,
        )


async def delete_agent(agent_id: uuid.UUID) -> None:
    """
    Soft delete agent (sets archived=true).

    Args:
        agent_id: UUID of the agent to archive
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE agents SET archived = true, updated_at = NOW() WHERE id = $1",
            agent_id,
        )


# ═══════════════════════════════════════════════════════════
# AGENT EVENT LOGGING OPERATIONS
# ═══════════════════════════════════════════════════════════


async def insert_hook_event(
    agent_id: uuid.UUID,
    task_slug: str,
    entry_index: int,
    event_type: str,
    payload: Dict[str, Any],
    content: Optional[str] = None,
    session_id: Optional[str] = None,
    adw_id: Optional[str] = None,
    adw_step: Optional[str] = None,
) -> uuid.UUID:
    """
    Insert hook event to agent_logs.

    Args:
        agent_id: UUID of the agent generating the event
        task_slug: Task identifier in kebab-case format
        entry_index: Sequential index within task for tail reading (0-based)
        event_type: Hook event type (PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact)
        payload: Complete hook data as JSONB
        content: Human-readable description of the event (e.g., "Using tool: Read")
        session_id: Claude SDK session ID (optional)
        adw_id: AI Developer Workflow identifier (optional)
        adw_step: AI Developer Workflow step identifier (optional)

    Returns:
        UUID of the created log entry
    """
    log_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO agent_logs (
                id, agent_id, session_id, task_slug, adw_id, adw_step, entry_index,
                event_category, event_type, content, payload, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        """,
            log_id,
            agent_id,
            session_id,
            task_slug,
            adw_id,
            adw_step,
            entry_index,
            "hook",
            event_type,
            content,
            json.dumps(payload),
        )

    return log_id


async def insert_message_block(
    agent_id: uuid.UUID,
    task_slug: str,
    entry_index: int,
    block_type: str,
    content: Optional[str],
    payload: Dict[str, Any],
    session_id: Optional[str] = None,
    adw_id: Optional[str] = None,
    adw_step: Optional[str] = None,
) -> uuid.UUID:
    """
    Insert message block to agent_logs.

    Args:
        agent_id: UUID of the agent generating the response
        task_slug: Task identifier in kebab-case format
        entry_index: Sequential index within task for tail reading (0-based)
        block_type: Message block type (text, thinking, tool_use, tool_result)
        content: Text content for text/thinking blocks, None for tool_use/tool_result
        payload: Complete block data as JSONB
        session_id: Claude SDK session ID (optional)
        adw_id: AI Developer Workflow identifier (optional)
        adw_step: AI Developer Workflow step identifier (optional)

    Returns:
        UUID of the created log entry
    """
    log_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO agent_logs (
                id, agent_id, session_id, task_slug, adw_id, adw_step, entry_index,
                event_category, event_type, content, payload, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        """,
            log_id,
            agent_id,
            session_id,
            task_slug,
            adw_id,
            adw_step,
            entry_index,
            "response",
            block_type,
            content,
            json.dumps(payload),
        )

    return log_id


async def update_log_summary(log_id: uuid.UUID, summary: str) -> None:
    """
    Add AI-generated summary to existing log entry.

    Args:
        log_id: UUID of the log entry to update
        summary: AI-generated summary text
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE agent_logs SET summary = $1 WHERE id = $2", summary, log_id
        )


async def update_log_payload(log_id: uuid.UUID, payload: Dict[str, Any]) -> None:
    """
    Update payload for existing log entry (merges with existing payload).

    Args:
        log_id: UUID of the log entry to update
        payload: Dictionary to merge into existing payload
    """
    async with get_connection() as conn:
        # Use JSONB concatenation operator || to merge payloads
        await conn.execute(
            "UPDATE agent_logs SET payload = payload || $1::jsonb WHERE id = $2",
            json.dumps(payload),
            log_id
        )


async def update_chat_summary(chat_id: uuid.UUID, summary: str) -> None:
    """
    Add AI-generated summary to existing chat message.

    Args:
        chat_id: UUID of the chat message to update
        summary: AI-generated summary text
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE orchestrator_chat SET summary = $1 WHERE id = $2", summary, chat_id
        )


async def update_prompt_summary(prompt_id: uuid.UUID, summary: str) -> None:
    """
    Add AI-generated summary to existing prompt.

    Args:
        prompt_id: UUID of the prompt to update
        summary: AI-generated summary text
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE prompts SET summary = $1 WHERE id = $2", summary, prompt_id
        )


async def update_system_log_summary(log_id: uuid.UUID, summary: str) -> None:
    """
    Add AI-generated summary to existing system log.

    Args:
        log_id: UUID of the system log to update
        summary: AI-generated summary text
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE system_logs SET summary = $1 WHERE id = $2", summary, log_id
        )


async def get_agent_logs(
    agent_id: uuid.UUID,
    task_slug: Optional[str] = None,
    limit: int = DEFAULT_AGENT_LOG_LIMIT,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get agent logs with optional filtering.

    Args:
        agent_id: UUID of the agent
        task_slug: Optional task identifier to filter by
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of log dicts, ordered by entry_index ASC
    """
    async with get_connection() as conn:
        if task_slug:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, session_id, task_slug, adw_id, adw_step,
                       entry_index, event_category, event_type, content, payload, summary, timestamp
                FROM agent_logs
                WHERE agent_id = $1 AND task_slug = $2
                ORDER BY entry_index ASC
                LIMIT $3 OFFSET $4
            """,
                agent_id,
                task_slug,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, session_id, task_slug, adw_id, adw_step,
                       entry_index, event_category, event_type, content, payload, summary, timestamp
                FROM agent_logs
                WHERE agent_id = $1
                ORDER BY timestamp DESC
                LIMIT $2 OFFSET $3
            """,
                agent_id,
                limit,
                offset,
            )

        results = []
        for row in rows:
            result = dict(row)
            # Parse payload JSONB if it's a string
            if isinstance(result.get("payload"), str):
                result["payload"] = json.loads(result["payload"])
            results.append(result)
        return results


async def get_tail_summaries(
    agent_id: uuid.UUID, task_slug: str, count: int = 10, offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get last N events with their AI-generated summaries.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier to filter by
        count: Maximum number of events to return

    Returns:
        List of dicts with entry_index, event_category, event_type, summary, timestamp
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT entry_index, event_category, event_type, summary, timestamp
            FROM agent_logs
            WHERE agent_id = $1
              AND task_slug = $2
              AND summary IS NOT NULL
            ORDER BY entry_index DESC
            LIMIT $3 OFFSET $4
        """,
            agent_id,
            task_slug,
            count,
            offset,
        )

    # Return in ascending order (chronological: oldest to newest)
    return [dict(row) for row in reversed(rows)]


async def get_tail_raw(
    agent_id: uuid.UUID, task_slug: str, count: int = 10, offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get last N events with full details (raw mode).

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier to filter by
        count: Maximum number of events to return
        offset: Number of events to skip from the end

    Returns:
        List of dicts with full event details
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT entry_index, event_category, event_type, content, payload, timestamp
            FROM agent_logs
            WHERE agent_id = $1 AND task_slug = $2
            ORDER BY entry_index DESC
            LIMIT $3 OFFSET $4
        """,
            agent_id,
            task_slug,
            count,
            offset,
        )

    # Return in ascending order (chronological: oldest to newest)
    results = []
    for row in reversed(rows):
        result = dict(row)
        # Parse payload JSONB if it's a string
        if isinstance(result.get("payload"), str):
            result["payload"] = json.loads(result["payload"])
        results.append(result)
    return results


async def get_latest_task_slug(agent_id: uuid.UUID) -> Optional[str]:
    """
    Get the most recent task_slug for an agent.

    Args:
        agent_id: UUID of the agent

    Returns:
        Most recent task_slug for the agent, or None if no logs exist
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT task_slug
            FROM agent_logs
            WHERE agent_id = $1
            GROUP BY task_slug
            ORDER BY MAX(timestamp) DESC
            LIMIT 1
        """,
            agent_id,
        )

    return row["task_slug"] if row else None


async def insert_prompt(
    agent_id: uuid.UUID,
    task_slug: str,
    author: str,
    prompt_text: str,
    session_id: Optional[str] = None,
) -> uuid.UUID:
    """
    Insert prompt to prompts table.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier
        author: "engineer" or "orchestrator_agent"
        prompt_text: The prompt text
        session_id: Claude SDK session ID (optional)

    Returns:
        UUID of the created prompt entry
    """
    prompt_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO prompts (
                id, agent_id, task_slug, author, prompt_text, session_id, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """,
            prompt_id,
            agent_id,
            task_slug,
            author,
            prompt_text,
            session_id,
        )

    return prompt_id


# ═══════════════════════════════════════════════════════════
# SYSTEM LOGS OPERATIONS
# ═══════════════════════════════════════════════════════════


async def insert_system_log(
    level: str,
    message: str,
    file_path: Optional[str] = None,
    adw_id: Optional[str] = None,
    adw_step: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> uuid.UUID:
    """
    Insert a system log entry.

    Args:
        level: Log level - "DEBUG", "INFO", "WARNING", or "ERROR"
        message: Log message text
        file_path: Optional file path reference
        adw_id: Optional AI Developer Workflow identifier
        adw_step: Optional AI Developer Workflow step identifier
        metadata: Optional JSONB metadata

    Returns:
        UUID of the created log entry

    Example:
        >>> log_id = await insert_system_log(
        ...     level="INFO",
        ...     message="Orchestrator thinking started",
        ...     metadata={"type": "thinking", "length": 150}
        ... )
    """
    log_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO system_logs (
                id, file_path, adw_id, adw_step, level, message, metadata, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, NOW())
        """,
            log_id,
            file_path,
            adw_id,
            adw_step,
            level,
            message,
            json.dumps(metadata or {}),
        )

    return log_id


# ═══════════════════════════════════════════════════════════
# EVENT STREAM FUNCTIONS
# ═══════════════════════════════════════════════════════════


async def list_agent_logs(orchestrator_agent_id: uuid.UUID, limit: int = DEFAULT_AGENT_LOG_LIMIT, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all agent logs for agents belonging to this orchestrator.

    Args:
        orchestrator_agent_id: UUID of the orchestrator agent
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of log dicts with agent_name from JOIN, ordered by timestamp DESC
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT al.id, al.agent_id, al.session_id, al.task_slug, al.adw_id, al.adw_step,
                   al.entry_index, al.event_category, al.event_type, al.content, al.payload,
                   al.summary, al.timestamp,
                   a.name as agent_name
            FROM agent_logs al
            LEFT JOIN agents a ON al.agent_id = a.id
            WHERE a.orchestrator_agent_id = $1
            ORDER BY al.timestamp DESC
            LIMIT $2 OFFSET $3
        """,
            orchestrator_agent_id,
            limit,
            offset,
        )

        results = []
        for row in rows:
            result = dict(row)
            # Parse payload JSONB if it's a string
            if isinstance(result.get("payload"), str):
                result["payload"] = json.loads(result["payload"])
            results.append(result)
        return results


async def list_system_logs(
    limit: int = DEFAULT_SYSTEM_LOG_LIMIT,
    offset: int = 0,
    message_contains: Optional[str] = None,
    level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get system logs with optional filtering.

    Args:
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        message_contains: Optional filter by message text (case-insensitive)
        level: Optional filter by log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        List of log dicts, ordered by timestamp DESC
    """
    async with get_connection() as conn:
        # Build dynamic query with filters
        query = """
            SELECT id, file_path, adw_id, level, message, summary, metadata, timestamp
            FROM system_logs
            WHERE 1=1
        """
        params = []
        param_count = 0

        # Add message filter if provided (non-empty string)
        if message_contains and message_contains.strip():
            param_count += 1
            query += f" AND message ILIKE ${param_count}"
            params.append(f"%{message_contains}%")

        # Add level filter if provided (non-empty string)
        if level and level.strip():
            param_count += 1
            query += f" AND level = ${param_count}"
            params.append(level.upper())

        # Add ordering and pagination
        param_count += 1
        query += f" ORDER BY timestamp DESC LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            result = dict(row)
            # Parse metadata JSONB if it's a string
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)
        return results


async def get_orchestrator_action_blocks(
    orchestrator_agent_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get orchestrator action blocks (ThinkingBlock, ToolUseBlock) from system_logs.

    Queries system_logs where metadata contains orchestrator_agent_id and type is
    either "thinking_block" or "tool_use_block".

    Args:
        orchestrator_agent_id: UUID of orchestrator agent
        limit: Maximum number of blocks to return
        offset: Number of blocks to skip

    Returns:
        List of action block dicts with metadata, ordered by timestamp DESC
    """
    async with get_connection() as conn:
        query = """
            SELECT id, level, message, summary, metadata, timestamp
            FROM system_logs
            WHERE metadata->>'orchestrator_agent_id' = $1
            AND metadata->>'type' IN ('thinking_block', 'tool_use_block')
            ORDER BY timestamp DESC
            LIMIT $2 OFFSET $3
        """

        rows = await conn.fetch(query, str(orchestrator_agent_id), limit, offset)

        results = []
        for row in rows:
            result = dict(row)
            # Parse metadata JSONB if it's a string
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)
        return results


async def list_orchestrator_chat(
    orchestrator_agent_id: Optional[uuid.UUID] = None,
    limit: int = DEFAULT_AGENT_LOG_LIMIT,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get orchestrator chat logs.

    Args:
        orchestrator_agent_id: Optional filter by orchestrator agent ID
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of chat log dicts, ordered by created_at DESC
    """
    async with get_connection() as conn:
        if orchestrator_agent_id:
            rows = await conn.fetch(
                """
                SELECT id, created_at, updated_at, orchestrator_agent_id,
                       sender_type, receiver_type, message, agent_id, metadata
                FROM orchestrator_chat
                WHERE orchestrator_agent_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """,
                orchestrator_agent_id,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, created_at, updated_at, orchestrator_agent_id,
                       sender_type, receiver_type, message, agent_id, metadata
                FROM orchestrator_chat
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """,
                limit,
                offset,
            )

        results = []
        for row in rows:
            result = dict(row)
            # Parse metadata JSONB if it's a string
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            results.append(result)
        return results


# ═══════════════════════════════════════════════════════════
# AI DEVELOPER WORKFLOW OPERATIONS
# ═══════════════════════════════════════════════════════════


async def create_adw(
    orchestrator_agent_id: uuid.UUID,
    adw_name: str,
    workflow_type: str,
    prompt: str,
    working_dir: str,
    description: Optional[str] = None,
    total_steps: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new AI Developer Workflow record.

    Args:
        orchestrator_agent_id: UUID of the orchestrator that started this ADW
        adw_name: Human-readable name for the workflow
        workflow_type: Type of workflow (maps to adw_*.py file)
        prompt: The task/prompt for the ADW to execute
        working_dir: Working directory for the workflow
        description: Optional detailed description
        total_steps: Total number of steps (if known upfront)
        metadata: Optional additional metadata

    Returns:
        Dict with ADW record including id, status, etc.
    """
    # Store prompt and working_dir in input_data so workflows can reload with just adw_id
    input_data = {"prompt": prompt, "working_dir": working_dir}

    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO ai_developer_workflows (
                orchestrator_agent_id, adw_name, workflow_type, description,
                status, total_steps, input_data, metadata
            )
            VALUES ($1, $2, $3, $4, 'pending', $5, $6, $7)
            RETURNING id, orchestrator_agent_id, adw_name, workflow_type, description,
                      status, current_step, total_steps, completed_steps,
                      started_at, completed_at, duration_seconds,
                      input_data, output_data, error_message, error_step, error_count,
                      metadata, created_at, updated_at
            """,
            orchestrator_agent_id,
            adw_name,
            workflow_type,
            description,
            total_steps,
            json.dumps(input_data),
            json.dumps(metadata or {}),
        )
        return dict(row)


async def get_adw(adw_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get an AI Developer Workflow by ID.

    Args:
        adw_id: UUID of the ADW

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
            adw_id,
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
    adw_id: uuid.UUID,
    status: str,
    current_step: Optional[str] = None,
    completed_steps: Optional[int] = None,
    error_message: Optional[str] = None,
    error_step: Optional[str] = None,
) -> bool:
    """
    Update ADW status and progress.

    Args:
        adw_id: UUID of the ADW
        status: New status (pending, in_progress, completed, failed, cancelled)
        current_step: Current step slug
        completed_steps: Number of completed steps
        error_message: Error message if failed
        error_step: Step where error occurred

    Returns:
        True if updated, False if not found
    """
    async with get_connection() as conn:
        # Build dynamic update
        updates = ["status = $2", "updated_at = NOW()"]
        params = [adw_id, status]
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

        # Handle status-specific updates
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


async def get_adw_logs(
    adw_id: uuid.UUID,
    limit: int = 2000,
    event_type: Optional[str] = None,
    include_payload: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get agent logs for an ADW.

    Args:
        adw_id: UUID of the ADW (stored as text in agent_logs.adw_id)
        limit: Maximum number of logs to return
        event_type: Optional filter by event_type (e.g., 'StepStart', 'StepEnd')
        include_payload: Whether to include full payload

    Returns:
        List of log entries
    """
    async with get_connection() as conn:
        # Build query based on whether we filter by event_type
        if event_type:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, adw_id, adw_step, event_category, event_type,
                       summary, payload, timestamp
                FROM agent_logs
                WHERE adw_id = $1 AND event_type = $2
                ORDER BY timestamp DESC
                LIMIT $3
                """,
                str(adw_id),
                event_type,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, adw_id, adw_step, event_category, event_type,
                       summary, payload, timestamp
                FROM agent_logs
                WHERE adw_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                str(adw_id),
                limit,
            )

        results = []
        for row in rows:
            result = dict(row)
            # Parse payload if needed
            if isinstance(result.get("payload"), str):
                result["payload"] = json.loads(result["payload"])
            # Remove payload if not requested
            if not include_payload:
                result["payload"] = None
            results.append(result)

        # Reverse to show oldest first
        results.reverse()
        return results


async def get_adw_system_logs(
    adw_id: uuid.UUID,
    limit: int = 2000,
    include_metadata: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get system logs for an ADW.

    Args:
        adw_id: UUID of the ADW (stored as text in system_logs.adw_id)
        limit: Maximum number of logs to return
        include_metadata: Whether to include full metadata

    Returns:
        List of system log entries formatted for swimlane display
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, adw_id, adw_step, level, message, metadata, timestamp
            FROM system_logs
            WHERE adw_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
            """,
            str(adw_id),
            limit,
        )

        results = []
        for row in rows:
            result = dict(row)
            # Parse metadata if needed
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            # Format for swimlane display (match agent_logs structure)
            formatted = {
                "id": result["id"],
                "adw_id": result["adw_id"],
                "adw_step": result.get("adw_step"),
                "event_category": "system",  # Mark as system event
                "event_type": f"System{result['level'].capitalize()}",
                "summary": f"[{result['level']}] {result['message'][:100]}{'...' if len(result['message']) > 100 else ''}",
                "payload": result["metadata"] if include_metadata else {"level": result["level"]},
                "timestamp": result["timestamp"],
                "content": result["message"],
            }
            results.append(formatted)

        # Reverse to show oldest first
        results.reverse()
        return results


async def list_adws(
    orchestrator_agent_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    List AI Developer Workflows for an orchestrator.

    Args:
        orchestrator_agent_id: UUID of the orchestrator
        status: Optional filter by status
        limit: Maximum number of ADWs to return

    Returns:
        List of ADW records
    """
    async with get_connection() as conn:
        if status:
            rows = await conn.fetch(
                """
                SELECT id, orchestrator_agent_id, adw_name, workflow_type, description,
                       status, current_step, total_steps, completed_steps,
                       started_at, completed_at, duration_seconds,
                       error_message, created_at, updated_at
                FROM ai_developer_workflows
                WHERE orchestrator_agent_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                orchestrator_agent_id,
                status,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, orchestrator_agent_id, adw_name, workflow_type, description,
                       status, current_step, total_steps, completed_steps,
                       started_at, completed_at, duration_seconds,
                       error_message, created_at, updated_at
                FROM ai_developer_workflows
                WHERE orchestrator_agent_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                orchestrator_agent_id,
                limit,
            )

        return [dict(row) for row in rows]
