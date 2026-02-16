# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "claude-agent-sdk>=0.1.18",
# ]
# ///
"""
ADW Summarizer Module - Fast AI-powered event summarization.

Uses Claude Haiku for cheap, fast single-shot queries to generate
concise 1-sentence summaries of agent events (hooks and response blocks).

Usage:
    from adw_modules.adw_summarizer import summarize_event

    summary = await summarize_event(
        event_data={"tool_name": "Read", "tool_input": {"file_path": "/path/to/file.py"}},
        event_type="PreToolUse"
    )
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

# Fast model for summarization (Haiku for speed and cost)
FAST_MODEL = "claude-haiku-4-5-20251001"

# Prompt templates (inline to avoid file dependencies)
EVENT_SUMMARIZER_SYSTEM_PROMPT = """You are a concise log summarizer. Create brief, informative 1-sentence summaries of events. Focus on the key action or information. Keep summaries under 100 characters."""

EVENT_SUMMARIZER_USER_PROMPT = """Summarize this event in one concise sentence (50-100 chars):

Event Type: {event_type}
{details}

Provide ONLY the summary sentence, no other text."""


# =============================================================================
# CORE QUERY FUNCTION
# =============================================================================


async def fast_claude_query(
    prompt: str, model: str = FAST_MODEL, system_prompt: Optional[str] = None
) -> str:
    """
    Execute a fast, single-shot Claude query without session management.

    Uses Claude Haiku by default for speed and cost efficiency.

    Args:
        prompt: The user prompt to send to Claude
        model: Claude model to use (defaults to Haiku)
        system_prompt: Optional system prompt

    Returns:
        Text response from Claude
    """
    try:
        # Pass ANTHROPIC_API_KEY explicitly
        env_vars = {}
        if "ANTHROPIC_API_KEY" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

        options = ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt,
            permission_mode="bypassPermissions",
            env=env_vars,
        )

        response_text = ""

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text

        return response_text.strip()

    except Exception as e:
        # Log but don't fail - return empty string for graceful degradation
        print(f"[ADW Summarizer] Fast query failed: {e}")
        return ""


# =============================================================================
# EVENT SUMMARIZATION
# =============================================================================


async def summarize_event(event_data: dict[str, Any], event_type: str) -> str:
    """
    Generate a concise 1-sentence summary of an agent event.

    Args:
        event_data: Event data dictionary containing:
            - For hooks: tool_name, tool_input, tool_use_id, etc.
            - For message blocks: content, text, thinking, etc.
        event_type: Type of event:
            Hook types: "PreToolUse", "PostToolUse", "Stop", etc.
            Block types: "TextBlock", "ThinkingBlock", "ToolUseBlock", "result"

    Returns:
        Concise 1-sentence summary (50-100 chars)
    """
    # Build prompt based on event type
    if event_type in ["PreToolUse", "PostToolUse"]:
        tool_name = event_data.get("tool_name", "unknown")
        tool_input = event_data.get("tool_input", {})
        details = f"Tool: {tool_name}\nInput: {json.dumps(tool_input, indent=2)[:500]}"
        fallback = f"{event_type}: {tool_name}"

    elif event_type in ["TextBlock", "text"]:
        content = event_data.get("content", event_data.get("text", ""))
        truncated = content[:500] if len(content) > 500 else content
        details = f"Content: {truncated}"
        fallback = f"Response: {content[:50]}..."

    elif event_type in ["ThinkingBlock", "thinking"]:
        thinking = event_data.get("thinking", event_data.get("content", ""))
        truncated = thinking[:500] if len(thinking) > 500 else thinking
        details = f"Thinking: {truncated}"
        fallback = f"Thinking: {thinking[:50]}..."

    elif event_type in ["ToolUseBlock", "tool_use"]:
        tool_name = event_data.get("tool_name", "unknown")
        tool_input = event_data.get("tool_input", {})
        details = f"Tool: {tool_name}\nInput: {json.dumps(tool_input, indent=2)[:500]}"
        fallback = f"Using tool: {tool_name}"

    elif event_type == "result":
        content = event_data.get("content", "")
        truncated = content[:200] if len(content) > 200 else content
        details = f"Result: {truncated}"
        fallback = "Step completed"

    elif event_type in ["Stop", "SubagentStop", "PreCompact"]:
        details = f"Data: {json.dumps(event_data, indent=2)[:500]}"
        fallback = event_type

    elif event_type == "UserPromptSubmit":
        prompt = event_data.get("prompt", "")[:200]
        details = f"Prompt: {prompt}"
        fallback = "User prompt submitted"

    else:
        details = f"Data: {json.dumps(event_data, indent=2)[:500]}"
        fallback = f"Event: {event_type}"

    # Build the full prompt
    prompt = EVENT_SUMMARIZER_USER_PROMPT.format(
        event_type=event_type, details=details
    )

    # Execute fast query
    try:
        summary = await fast_claude_query(
            prompt=prompt,
            system_prompt=EVENT_SUMMARIZER_SYSTEM_PROMPT,
            model=FAST_MODEL,
        )

        if summary and len(summary.strip()) > 0:
            return summary.strip()
        else:
            return fallback

    except Exception as e:
        print(f"[ADW Summarizer] Error generating summary: {e}")
        return fallback


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "fast_claude_query",
    "summarize_event",
]
