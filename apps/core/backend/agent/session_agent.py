#!/usr/bin/env python3
"""Example agent using session MCP tools via Claude Agent SDK.

This script demonstrates how to:
1. Create an agent with all 7 session state MCP tools
2. Have the agent manage session state through MCP tool calls
3. Verify state.json is updated correctly

Available MCP Tools:
    - session_transition_phase: Transition session to a new phase
    - session_init_build: Initialize build progress with checkpoint count
    - session_start_checkpoint: Set current active checkpoint
    - session_complete_checkpoint: Mark checkpoint as completed
    - session_add_commit: Record a git commit
    - session_set_status: Set session status (active/paused/complete/failed)
    - session_set_git: Set git context (branch/worktree)

Usage:
    # Set your API key
    export ANTHROPIC_API_KEY=your-api-key

    # Run from apps/core/backend directory
    cd apps/core/backend
    python -m agent.session_agent /path/to/session/dir

Requirements:
    - claude-agent-sdk installed
    - Valid session directory with state.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    query,
)

# Add backend directory to path for local imports
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from mcp_tools import get_session_mcp_server  # noqa: E402
from mcp_tools.server import SERVER_NAME  # noqa: E402


async def run_session_agent(session_dir: str, action: str = "status") -> None:
    """Run an agent that can manage session state.

    Args:
        session_dir: Path to the session directory
        action: What action to perform ("status", "transition_to_plan", etc.)
    """
    # Build the prompt based on action
    if action == "status":
        prompt = f"""Read the session state from {session_dir}/state.json and report:
        - Current phase
        - Session ID
        - When it was last updated"""
    elif action == "transition_to_plan":
        prompt = f"""Transition the session at {session_dir} from spec phase to plan phase.
        Use the session_transition_phase tool with:
        - session_dir: {session_dir}
        - new_phase: plan"""
    elif action == "transition_to_build":
        prompt = f"""Transition the session at {session_dir} from plan phase to build phase.
        Use the session_transition_phase tool with:
        - session_dir: {session_dir}
        - new_phase: build"""
    elif action == "init_build":
        prompt = f"""Initialize build progress for the session at {session_dir}.
        Use the session_init_build tool with:
        - session_dir: {session_dir}
        - checkpoints_total: 5 (example count)"""
    elif action == "complete_checkpoint":
        prompt = f"""Mark checkpoint 1 as completed for the session at {session_dir}.
        Use the session_complete_checkpoint tool with:
        - session_dir: {session_dir}
        - checkpoint_id: 1"""
    elif action == "add_commit":
        prompt = f"""Record a test commit for the session at {session_dir}.
        Use the session_add_commit tool with:
        - session_dir: {session_dir}
        - sha: abc1234
        - message: test commit from agent
        - checkpoint: 1 (optional)"""
    elif action == "set_status":
        prompt = f"""Set the session status to 'paused' for the session at {session_dir}.
        Use the session_set_status tool with:
        - session_dir: {session_dir}
        - status: paused"""
    elif action == "set_git":
        prompt = f"""Set the git branch for the session at {session_dir}.
        Use the session_set_git tool with:
        - session_dir: {session_dir}
        - branch: feature/test-branch"""
    elif action == "test_all":
        prompt = f"""Test all 7 session MCP tools for the session at {session_dir}.

        Run each tool in order and report results:
        1. session_transition_phase (report current phase, don't actually transition)
        2. session_init_build (report if build progress can be initialized)
        3. session_start_checkpoint (report current checkpoint)
        4. session_complete_checkpoint (report checkpoint status)
        5. session_add_commit (report commit count)
        6. session_set_status (report current status)
        7. session_set_git (report git context)

        For each tool, just READ the current state and report what the tool would do.
        Do NOT make actual changes unless explicitly told to do so.

        Session dir: {session_dir}"""
    else:
        prompt = f"Help the user with session management for: {session_dir}. Action: {action}"

    # Configure the agent with all session MCP tools
    options = ClaudeAgentOptions(
        mcp_servers={SERVER_NAME: get_session_mcp_server()},
        allowed_tools=[
            f"mcp__{SERVER_NAME}__*",  # All session tools
            "Read",  # For reading state.json
        ],
        max_turns=10,
    )

    print(f"\n{'=' * 60}")
    print(f"Session Agent - {action}")
    print(f"Session: {session_dir}")
    print(f"{'=' * 60}\n")

    # Run the agent
    async for message in query(prompt=prompt, options=options):
        # Log MCP server connection status
        if isinstance(message, SystemMessage) and message.subtype == "init":
            mcp_servers = message.data.get("mcp_servers", [])
            for server in mcp_servers:
                status = server.get("status", "unknown")
                name = server.get("name", "unnamed")
                print(f"[MCP] {name}: {status}")

        # Log tool calls
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "name") and hasattr(block, "input"):
                    print(f"\n[Tool Call] {block.name}")
                    print(f"  Input: {block.input}")

        # Print final result
        if isinstance(message, ResultMessage):
            if message.subtype == "success":
                print(f"\n[Result] Success")
                print(message.result)
            else:
                print(f"\n[Result] {message.subtype}")
                if hasattr(message, "error"):
                    print(f"  Error: {message.error}")


async def demo_full_workflow(session_dir: str) -> None:
    """Demonstrate a full session workflow.

    Shows transitioning from spec → plan → build.
    """
    print("\n" + "=" * 60)
    print("Full Session Workflow Demo")
    print("=" * 60)

    # Read initial state
    print("\n[1/3] Reading initial state...")
    await run_session_agent(session_dir, "status")

    # Note: In a real workflow, you'd only transition if appropriate
    # This is just a demonstration of the MCP tool capabilities
    print("\n[2/3] Attempting transition to plan...")
    await run_session_agent(session_dir, "transition_to_plan")

    # Read final state
    print("\n[3/3] Reading final state...")
    await run_session_agent(session_dir, "status")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Example agent using session MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # From apps/core/backend directory:

    # Check session status
    python -m agent.session_agent /path/to/session status

    # Transition to plan phase
    python -m agent.session_agent /path/to/session transition_to_plan

    # Initialize build progress
    python -m agent.session_agent /path/to/session init_build

    # Complete a checkpoint
    python -m agent.session_agent /path/to/session complete_checkpoint

    # Record a commit
    python -m agent.session_agent /path/to/session add_commit

    # Set session status
    python -m agent.session_agent /path/to/session set_status

    # Set git context
    python -m agent.session_agent /path/to/session set_git

    # Test all 7 tools (read-only)
    python -m agent.session_agent /path/to/session test_all

    # Run full demo workflow
    python -m agent.session_agent /path/to/session demo
        """,
    )
    parser.add_argument(
        "session_dir",
        type=str,
        help="Path to session directory containing state.json",
    )
    parser.add_argument(
        "action",
        type=str,
        nargs="?",
        default="status",
        choices=[
            "status",
            "transition_to_plan",
            "transition_to_build",
            "init_build",
            "complete_checkpoint",
            "add_commit",
            "set_status",
            "set_git",
            "test_all",
            "demo",
        ],
        help="Action to perform (default: status)",
    )

    args = parser.parse_args()

    # Validate session directory
    session_path = Path(args.session_dir)
    if not session_path.exists():
        print(f"Error: Session directory not found: {args.session_dir}")
        sys.exit(1)

    state_file = session_path / "state.json"
    if not state_file.exists():
        print(f"Error: state.json not found in: {args.session_dir}")
        sys.exit(1)

    # Run the agent
    if args.action == "demo":
        asyncio.run(demo_full_workflow(args.session_dir))
    else:
        asyncio.run(run_session_agent(args.session_dir, args.action))


if __name__ == "__main__":
    main()
