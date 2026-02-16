"""MCP Tools package for session state management.

This package provides in-process SDK MCP tools that wrap StateManager
operations, allowing Claude Agent SDK agents to manage session state
through tool calls.

Example usage:
    from mcp_tools import get_session_mcp_server
    from claude_agent_sdk import query, ClaudeAgentOptions

    async for message in query(
        prompt="Transition the session to plan phase",
        options=ClaudeAgentOptions(
            mcp_servers={"session_state": get_session_mcp_server()},
            allowed_tools=["mcp__session_state__*"],
        ),
    ):
        print(message)
"""

from .server import get_session_mcp_server
from .session_tools import session_transition_phase

__all__ = [
    "get_session_mcp_server",
    "session_transition_phase",
]
