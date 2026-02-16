"""
COMMAND AGENT Hook Implementations for Claude SDK Events with WebSocket Streaming

Captures hook events from command agents (subagents created by orchestrator),
logs to database, and broadcasts via WebSocket.

Key Features:
- 6 hook types for complete command agent event coverage
- Database persistence via agent_logs table with event_category='hook'
- Real-time WebSocket broadcasting to frontend
- Async AI summarization in background
- Errors throw loudly for debugging

Used by: agent_manager.py when creating/commanding agents
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from .database import insert_hook_event, reset_agent_tokens, update_log_summary
from .event_summarizer import summarize_event
from .logger import OrchestratorLogger
from .websocket_manager import WebSocketManager

# Type alias for hook callbacks
HookCallback = Callable[[Dict[str, Any], Optional[str], Any], Awaitable[Dict[str, Any]]]


# ═══════════════════════════════════════════════════════════
# Hook Factory Functions
# ═══════════════════════════════════════════════════════════


def create_pre_tool_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create PreToolUse hook that logs every tool call before execution.

    Args:
        agent_id: UUID of the agent executing tools
        agent_name: Name of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key for sequential indexing
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
        """PreToolUse hook implementation"""
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        payload = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_use_id": tool_use_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:PreToolUse] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} Tool={tool_name}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="PreToolUse",
            payload=payload,
            content=f"Using tool: {tool_name}"
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "PreToolUse",
            "content": f"Using tool: {tool_name}",
            "summary": f"Using tool: {tool_name}",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "PreToolUse", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_post_tool_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create PostToolUse hook that logs tool execution results.

    Args:
        agent_id: UUID of the agent
        agent_name: Name of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key
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
        """PostToolUse hook implementation"""
        tool_name = input_data.get("tool_name", "unknown")
        result = input_data.get("result")
        is_error = input_data.get("is_error", False)

        payload = {
            "tool_name": tool_name,
            "result": str(result)[:500] if result else None,  # Truncate large results
            "is_error": is_error,
            "tool_use_id": tool_use_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:PostToolUse] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} Tool={tool_name} Error={is_error}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="PostToolUse",
            payload=payload,
            content=f"Completed tool: {tool_name}"
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "PostToolUse",
            "content": f"Tool result: {tool_name}",
            "summary": f"Completed tool: {tool_name}",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "PostToolUse", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_user_prompt_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create UserPromptSubmit hook that logs user prompts.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key
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
        """UserPromptSubmit hook implementation"""
        prompt = input_data.get("prompt", "")

        # Truncate long prompts for payload
        payload = {
            "prompt": prompt[:1000],  # Truncate to 1000 chars
            "prompt_length": len(prompt),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:UserPromptSubmit] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} PromptLen={len(prompt)}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="UserPromptSubmit",
            payload=payload,
            content=f"User prompt: {prompt_preview}"
        )

        # Broadcast via WebSocket
        prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "UserPromptSubmit",
            "content": f"User prompt: {prompt_preview}",
            "summary": f"User: {prompt_preview}",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "UserPromptSubmit", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_stop_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create Stop hook that logs agent session stops.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key
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
        """Stop hook implementation"""
        reason = input_data.get("reason", "unknown")
        num_turns = input_data.get("num_turns", 0)
        duration_ms = input_data.get("duration_ms", 0)

        payload = {
            "reason": reason,
            "num_turns": num_turns,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:Stop] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} Reason={reason} Turns={num_turns}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="Stop",
            payload=payload,
            content=f"Agent stopped: {reason}"
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "Stop",
            "content": f"Agent stopped: {reason}",
            "summary": f"Stopped after {num_turns} turns",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "Stop", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_subagent_stop_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create SubagentStop hook that logs subagent completions.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key
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
        """SubagentStop hook implementation"""
        subagent_id = input_data.get("subagent_id", "unknown")

        payload = {
            "subagent_id": subagent_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:SubagentStop] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} Subagent={subagent_id}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="SubagentStop",
            payload=payload,
            content=f"Subagent {subagent_id} completed"
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "SubagentStop",
            "content": f"Subagent {subagent_id} completed",
            "summary": "Subagent completed",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "SubagentStop", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_pre_compact_hook(
    agent_id: uuid.UUID,
    agent_name: str,
    task_slug: str,
    entry_counter: Dict[str, int],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> HookCallback:
    """
    Create PreCompact hook that logs conversation compaction events.

    IMPORTANT: Also resets agent token counters in database.

    Args:
        agent_id: UUID of the agent
        task_slug: Task identifier
        entry_counter: Mutable dict with "count" key
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
        """PreCompact hook implementation"""
        tokens_before = input_data.get("tokens_before", 0)

        payload = {
            "tokens_before": tokens_before,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        entry_index = entry_counter["count"]
        entry_counter["count"] += 1

        logger.info(
            f"[Hook:PreCompact] Agent={agent_id} Task={task_slug} "
            f"Entry={entry_index} TokensBefore={tokens_before}"
        )

        # Insert hook event to database - THROW ERRORS LOUDLY
        log_id = await insert_hook_event(
            agent_id=agent_id,
            task_slug=task_slug,
            entry_index=entry_index,
            event_type="PreCompact",
            payload=payload,
            content=f"Context compaction: {tokens_before} tokens"
        )

        # CRITICAL: Reset agent token counters after compaction
        await reset_agent_tokens(agent_id)
        logger.info(f"[Hook:PreCompact] Reset token counters for agent {agent_id}")

        # Broadcast via WebSocket
        await ws_manager.broadcast_agent_log({
            "id": str(log_id),
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "task_slug": task_slug,
            "entry_index": entry_index,
            "event_category": "hook",
            "event_type": "PreCompact",
            "content": f"Context compaction: {tokens_before} tokens",
            "summary": "Context compaction triggered",
            "payload": payload,
            "timestamp": payload["timestamp"]
        })

        # Spawn async summarization
        asyncio.create_task(
            _summarize_and_update(log_id, agent_id, "PreCompact", payload, logger, ws_manager)
        )

        return {}

    return hook


def create_post_tool_file_tracking_hook(
    file_tracker: Any,  # FileTracker instance
    agent_id: uuid.UUID,
    agent_name: str,
    logger: OrchestratorLogger
) -> HookCallback:
    """
    Create PostToolUse hook for file tracking (captures modified and read files).

    This hook:
    - Tracks files modified by Write, Edit, MultiEdit, Bash tools
    - Tracks files read by Read tool
    - Does NOT broadcast individual operations (only in final response)
    - Does NOT insert to database (avoids duplicate events)

    Args:
        file_tracker: FileTracker instance for this agent
        agent_id: UUID of the agent
        agent_name: Name of the agent
        logger: Logger instance

    Returns:
        Async hook callable
    """
    # Import here to avoid circular dependency
    from .file_tracker import FILE_MODIFYING_TOOLS, FILE_READING_TOOLS

    async def hook(
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """File tracking hook implementation"""
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})

        # Track modified files
        if tool_name in FILE_MODIFYING_TOOLS:
            file_path = tool_input.get("file_path")
            if file_path:
                file_tracker.track_modified_file(tool_name, tool_input)
                logger.debug(
                    f"[FileTracker] Agent={agent_name} Modified: {file_path}"
                )

        # Track read files
        elif tool_name in FILE_READING_TOOLS:
            file_path = tool_input.get("file_path")
            if file_path:
                file_tracker.track_read_file(file_path)
                logger.debug(
                    f"[FileTracker] Agent={agent_name} Read: {file_path}"
                )

        # For Bash, we could parse stdout for file operations (future enhancement)
        # For now, skip Bash file tracking

        return {}  # Don't block or modify anything

    return hook


# ═══════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════


async def _summarize_and_update(
    log_id: uuid.UUID,
    agent_id: uuid.UUID,
    event_type: str,
    event_data: Dict[str, Any],
    logger: OrchestratorLogger,
    ws_manager: WebSocketManager
) -> None:
    """
    Generate AI summary and update log entry.

    Runs in background, does not block hook execution.
    Also broadcasts the summary to frontend via WebSocket.

    Args:
        log_id: UUID of the log entry to update
        agent_id: UUID of the agent this log belongs to
        event_type: Type of event
        event_data: Event payload
        logger: Logger instance
        ws_manager: WebSocket manager for broadcasting
    """
    try:
        summary = await summarize_event(event_data, event_type)
        await update_log_summary(log_id, summary)
        logger.debug(f"[Hook:Summary] Generated for log_id={log_id}: {summary}")

        # Broadcast the latest summary for this agent to frontend
        await ws_manager.broadcast_agent_summary_update(
            agent_id=str(agent_id),
            summary=summary
        )
        logger.debug(f"[Hook:Summary] Broadcast summary update for agent={agent_id}")

    except Exception as e:
        logger.error(f"[Hook:Summary] Failed for log_id={log_id}: {e}", exc_info=True)
