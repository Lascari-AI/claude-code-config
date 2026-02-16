"""
Event Summarizer Module - Fast AI-Powered Summarization

This module is a lightweight wrapper around single_agent_prompt.py for backwards compatibility.
All functionality has been moved to single_agent_prompt.py.

Use single_agent_prompt.py directly for new code.
"""

from .single_agent_prompt import fast_claude_query, summarize_event

__all__ = [
    "summarize_event",
    "fast_claude_query",
]
