"""SDK MCP Server for session state management.

This module creates an in-process MCP server that registers session state tools.
The server runs within the SDK application, not as a separate process.

Usage:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from mcp_tools import get_session_mcp_server

    async for message in query(
        prompt="Transition session to plan phase",
        options=ClaudeAgentOptions(
            mcp_servers={"session_state": get_session_mcp_server()},
            allowed_tools=["mcp__session_state__*"],
        ),
    ):
        print(message)
"""

from __future__ import annotations

from claude_agent_sdk import create_sdk_mcp_server

from .session_tools import (
    session_add_commit,
    session_complete_checkpoint,
    session_init_build,
    session_set_git,
    session_set_status,
    session_start_checkpoint,
    session_transition_phase,
)

# Server version for tracking
_SERVER_VERSION = "0.2.0"  # Updated: added full tool suite

# Server name used in MCP tool naming convention
# Tools will be named: mcp__session_state__<tool_name>
SERVER_NAME = "session_state"


def get_session_mcp_server():
    """Create an SDK MCP server with session state tools.

    Returns an MCP server configuration dict that can be passed to
    ClaudeAgentOptions.mcp_servers. The server runs in-process with
    the Claude Agent SDK.

    Tools available:
        - session_transition_phase: Transition session to a new phase
        - session_init_build: Initialize build progress with checkpoint count
        - session_start_checkpoint: Set current active checkpoint
        - session_complete_checkpoint: Mark checkpoint as completed
        - session_add_commit: Record a git commit
        - session_set_status: Set session status (active/paused/complete/failed)
        - session_set_git: Set git context (branch/worktree)

    Returns:
        MCP server configuration for use with ClaudeAgentOptions

    Example:
        options = ClaudeAgentOptions(
            mcp_servers={"session_state": get_session_mcp_server()},
            allowed_tools=["mcp__session_state__*"],
        )
    """
    return create_sdk_mcp_server(
        name=SERVER_NAME,
        version=_SERVER_VERSION,
        tools=[
            # Phase transitions
            session_transition_phase,
            # Checkpoint tracking
            session_init_build,
            session_start_checkpoint,
            session_complete_checkpoint,
            # Commit tracking
            session_add_commit,
            # Status and git context
            session_set_status,
            session_set_git,
        ],
    )


# Convenience export for direct server access
session_mcp_server = get_session_mcp_server
