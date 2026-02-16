"""
Single Agent Prompt Module - Fast Stateless Claude Queries

Provides fast, single-shot Claude queries for AI summarization without session management.
Used for generating concise summaries of agent events (hooks and response blocks).

This module uses the Claude Agent SDK's query() function for stateless, one-off
interactions. It's designed for cheap, fast operations like summarization where
conversation history is not needed.

Key Features:
- Fast single-shot queries using Claude Haiku for speed and cost efficiency
- Event summarization for hooks (PreToolUse, PostToolUse, etc.)
- Message block summarization for agent responses
- No session persistence or conversation history
- Comprehensive error handling and fallbacks

Reference: Copied from apps/orchestrator_1_term/modules/single_agent_prompt.py
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from .logger import OrchestratorLogger

# Configure module logger
logger = OrchestratorLogger()

# Fast model for summarization (Haiku for speed and cost)
FAST_MODEL = "claude-haiku-4-5-20251001"

# Load prompt templates from files
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
EVENT_SUMMARIZER_USER_PROMPT = (
    PROMPTS_DIR / "event_summarizer_user_prompt.md"
).read_text()
EVENT_SUMMARIZER_SYSTEM_PROMPT = (
    PROMPTS_DIR / "event_summarizer_system_prompt.md"
).read_text()


# ═══════════════════════════════════════════════════════════
# CORE QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════


async def fast_claude_query(
    prompt: str, model: str = FAST_MODEL, system_prompt: Optional[str] = None
) -> str:
    """
    Execute a fast, single-shot Claude query without session management.

    This is for stateless operations where you don't need conversation history.
    Uses the Claude Agent SDK's query() function for one-off interactions.

    Uses Claude Haiku by default for speed and cost efficiency. Perfect for
    summarization, quick analysis, name generation, and other simple tasks.

    Args:
        prompt: The user prompt to send to Claude
        model: Claude model to use (defaults to FAST_MODEL/Haiku for speed/cost)
        system_prompt: Optional system prompt to guide Claude's behavior

    Returns:
        Text response from Claude (first TextBlock content)

    Raises:
        Exception: If API call fails (logged and re-raised)

    Example:
        >>> summary = await fast_claude_query(
        ...     prompt="Summarize this log: Read file config.py",
        ...     system_prompt="Provide concise 1-sentence summaries"
        ... )
        >>> print(summary)
        "Reading configuration file to understand project settings"

    Note:
        - No conversation history is maintained
        - Each call creates a fresh session via query()
        - Suitable for stateless operations only
        - Falls back to empty string on API errors
    """
    try:
        logger.debug(
            f"Making fast Claude query with model={model}, "
            f"prompt_length={len(prompt)}"
        )

        # Use Claude Agent SDK's query() function for one-off interactions
        # Pass ANTHROPIC_API_KEY explicitly to ensure subprocess has access
        env_vars = {}
        if "ANTHROPIC_API_KEY" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

        options = ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt,
            permission_mode="bypassPermissions",  # No user interaction needed
            env=env_vars,  # Ensure API key is available to subprocess
        )

        response_text = ""

        # Query returns an async generator of messages
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                # Extract text from TextBlocks
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text

        logger.debug(f"Fast query completed, response_length={len(response_text)}")

        return response_text.strip()

    except Exception as e:
        logger.error(f"Fast Claude query failed: {e}", exc_info=True)
        # Return empty string on error (graceful degradation)
        return ""


# ═══════════════════════════════════════════════════════════
# EVENT SUMMARIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════


async def summarize_event(event_data: dict[str, Any], event_type: str) -> str:
    """
    Generate a concise 1-sentence summary of an agent event.

    Takes event data (either hook event or message block) and generates
    a human-readable summary using fast Claude query. Used by hooks.py
    and agent_manager.py to populate the summary column in agent_logs table.

    Args:
        event_data: Event data dictionary containing:
            - For hooks: tool_name, tool_input, tool_use_id, etc.
            - For message blocks: content, text, thinking, etc.
        event_type: Type of event, one of:
            Hook types: "PreToolUse", "PostToolUse", "UserPromptSubmit",
                       "Stop", "SubagentStop", "PreCompact"
            Block types: "text", "thinking", "tool_use", "tool_result"

    Returns:
        Concise 1-sentence summary of the event (50-100 chars recommended)
        Returns fallback summary if API call fails

    Example:
        >>> # Summarize a hook event
        >>> summary = await summarize_event(
        ...     event_data={
        ...         "tool_name": "Read",
        ...         "tool_input": {"file_path": "/path/to/config.py"}
        ...     },
        ...     event_type="PreToolUse"
        ... )
        >>> print(summary)
        "Reading configuration file at /path/to/config.py"

        >>> # Summarize a message block
        >>> summary = await summarize_event(
        ...     event_data={"content": "I'll analyze the codebase structure..."},
        ...     event_type="text"
        ... )
        >>> print(summary)
        "Agent responding: analyzing codebase structure"

    Note:
        - Summaries are stored in agent_logs.summary column
        - Used for tail reading and quick status checks
        - Falls back to descriptive defaults on errors
    """
    # Build prompt based on event type
    if event_type in ["PreToolUse", "PostToolUse"]:
        # Tool use hook events
        tool_name = event_data.get("tool_name", "unknown")
        tool_input = event_data.get("tool_input", {})

        details = f"Tool: {tool_name}\nInput: {json.dumps(tool_input, indent=2)}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT

        fallback = f"{event_type}: {tool_name}"

    elif event_type in ["text", "thinking"]:
        # Response block events with content
        content = event_data.get("content", "")

        # Truncate long content for the prompt
        truncated_content = content[:500] if len(content) > 500 else content

        details = f"Content: {truncated_content}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT

        fallback = f"{event_type.capitalize()}: {content[:50]}..."

    elif event_type in ["tool_use", "tool_result"]:
        # Tool use/result blocks
        if "tool_name" in event_data:
            tool_name = event_data["tool_name"]
            fallback = f"Tool use: {tool_name}"
        else:
            fallback = f"Tool {event_type}"

        details = f"Data: {json.dumps(event_data, indent=2)[:500]}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT

    elif event_type in ["Stop", "SubagentStop", "PreCompact"]:
        # Control flow hook events
        details = f"Data: {json.dumps(event_data, indent=2)}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT

        fallback = event_type

    elif event_type == "UserPromptSubmit":
        # User prompt submission
        details = f"Data: {json.dumps(event_data, indent=2)[:500]}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT

        fallback = "User prompt submitted"

    else:
        # Unknown event type - create generic summary
        logger.warning(f"Unknown event type for summarization: {event_type}")

        details = f"Data: {json.dumps(event_data, indent=2)[:500]}"
        prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
            event_type=event_type, details=details
        )

        system_prompt = EVENT_SUMMARIZER_SYSTEM_PROMPT
        fallback = f"Event: {event_type}"

    # Execute fast query to generate summary
    try:
        summary = await fast_claude_query(
            prompt=prompt, system_prompt=system_prompt, model=FAST_MODEL
        )

        # If we got a response, use it; otherwise use fallback
        if summary and len(summary.strip()) > 0:
            logger.debug(f"Generated summary for {event_type}: {summary}")
            return summary.strip()
        else:
            logger.warning(f"Empty summary returned for {event_type}, using fallback")
            return fallback

    except Exception as e:
        logger.error(f"Error generating summary for {event_type}: {e}", exc_info=True)
        return fallback


# ═══════════════════════════════════════════════════════════
# EXPORT PUBLIC API
# ═══════════════════════════════════════════════════════════

__all__ = [
    "fast_claude_query",
    "summarize_event",
]
