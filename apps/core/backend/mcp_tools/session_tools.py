"""Session state MCP tool implementations.

These tools wrap StateManager operations for use via Claude Agent SDK.
Each tool is decorated with @tool for registration with create_sdk_mcp_server.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

# Import from sibling state_manager package within backend
from state_manager import (
    InvalidPhaseTransitionError,
    Phase,
    SessionNotFoundError,
    SessionStateManager,
    StateValidationError,
)
from task_pool import make_pooled_sync_callback


def _derive_working_dir(session_dir: str | Path) -> str:
    """Derive the project working directory from a session directory path.

    Session directories follow the structure:
        {working_dir}/agents/sessions/{session_slug}

    So we go up 3 levels to get the project root.
    """
    session_path = Path(session_dir)
    return str(session_path.parent.parent.parent)


def _create_manager(session_dir: str | Path) -> SessionStateManager:
    """Create a SessionStateManager with sync callback injected.

    This is the standard way to create managers in MCP tools - ensures
    all state changes trigger async database sync.
    """
    session_path = Path(session_dir)
    working_dir = _derive_working_dir(session_path)
    callback = make_pooled_sync_callback(working_dir)
    return SessionStateManager(session_path, on_save_callback=callback)


@tool(
    "session_transition_phase",
    "Transition a session to a new phase. Valid transitions: spec→plan, plan→build, build→docs or complete, docs→complete.",
    {
        "session_dir": str,
        "new_phase": str,
    },
)
async def session_transition_phase(args: dict[str, Any]) -> dict[str, Any]:
    """Transition a session to a new phase.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - new_phase: Target phase (spec, plan, build, docs, complete)

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    new_phase_str = args["new_phase"]

    try:
        # Validate phase string
        try:
            new_phase = Phase(new_phase_str)
        except ValueError:
            valid_phases = ", ".join(p.value for p in Phase)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid phase '{new_phase_str}'. Valid phases: {valid_phases}",
                    }
                ]
            }

        # Load state and transition
        manager = _create_manager(session_dir)
        state = manager.load()
        current_phase = state.current_phase

        manager.transition_to_phase(new_phase)

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Transitioned session from '{current_phase.value}' "
                        f"to '{new_phase.value}'.\n"
                        f"Session: {state.session_id}\n"
                        f"Updated: {state.updated_at.isoformat()}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: Session not found - {e}",
                }
            ]
        }

    except InvalidPhaseTransitionError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: Invalid transition - {e}",
                }
            ]
        }

    except StateValidationError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: State validation failed - {e}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: Unexpected error - {type(e).__name__}: {e}",
                }
            ]
        }


# ─── Checkpoint Tools ──────────────────────────────────────────────────────


@tool(
    "session_init_build",
    "Initialize build progress for a session. Sets total checkpoints and resets progress. Call when transitioning to build phase.",
    {
        "session_dir": str,
        "checkpoints_total": int,
    },
)
async def session_init_build(args: dict[str, Any]) -> dict[str, Any]:
    """Initialize build progress for build phase.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - checkpoints_total: Total number of checkpoints in the plan

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    checkpoints_total = args["checkpoints_total"]

    try:
        manager = _create_manager(session_dir)
        manager.load()
        manager.init_build_progress(checkpoints_total)

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Initialized build progress with {checkpoints_total} checkpoints.\n"
                        f"Session: {manager.state.session_id}\n"
                        f"Current checkpoint: 1"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: Invalid value - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }


@tool(
    "session_start_checkpoint",
    "Set the current active checkpoint for a session. Use when beginning work on a checkpoint.",
    {
        "session_dir": str,
        "checkpoint_id": int,
    },
)
async def session_start_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
    """Set the current active checkpoint.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - checkpoint_id: The checkpoint ID to start (1-indexed)

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    checkpoint_id = args["checkpoint_id"]

    try:
        manager = _create_manager(session_dir)
        manager.load()
        manager.start_checkpoint(checkpoint_id)

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Started checkpoint {checkpoint_id}.\n"
                        f"Session: {manager.state.session_id}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: Invalid checkpoint - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }


@tool(
    "session_complete_checkpoint",
    "Mark a checkpoint as completed. Auto-advances current_checkpoint to next, or sets to null if last.",
    {
        "session_dir": str,
        "checkpoint_id": int,
    },
)
async def session_complete_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
    """Mark a checkpoint as completed.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - checkpoint_id: The checkpoint ID that was completed

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    checkpoint_id = args["checkpoint_id"]

    try:
        manager = _create_manager(session_dir)
        manager.load()
        manager.complete_checkpoint(checkpoint_id)

        state = manager.state
        completed_count = len(state.build_progress.checkpoints_completed)
        total = state.build_progress.checkpoints_total
        next_cp = state.build_progress.current_checkpoint

        next_msg = f"Next: Checkpoint {next_cp}" if next_cp else "All checkpoints complete!"

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Completed checkpoint {checkpoint_id}.\n"
                        f"Session: {state.session_id}\n"
                        f"Progress: {completed_count}/{total} checkpoints\n"
                        f"{next_msg}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: Invalid checkpoint - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }


# ─── Commit Tools ──────────────────────────────────────────────────────────


@tool(
    "session_add_commit",
    "Record a git commit made during the session. Optionally link to a checkpoint.",
    {
        "session_dir": str,
        "sha": str,
        "message": str,
        "checkpoint": int,  # Optional in implementation, but schema requires type
    },
)
async def session_add_commit(args: dict[str, Any]) -> dict[str, Any]:
    """Record a git commit made during the session.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - sha: The commit SHA (short or full)
            - message: The commit message
            - checkpoint: (Optional) Checkpoint ID this commit relates to

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    sha = args["sha"]
    message = args["message"]
    checkpoint = args.get("checkpoint")  # Optional

    try:
        manager = _create_manager(session_dir)
        manager.load()
        manager.add_commit(sha=sha, message=message, checkpoint=checkpoint)

        commit_count = len(manager.state.commits)
        checkpoint_msg = f" (Checkpoint {checkpoint})" if checkpoint else ""

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Recorded commit {sha[:7]}{checkpoint_msg}.\n"
                        f"Session: {manager.state.session_id}\n"
                        f"Total commits: {commit_count}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }


# ─── Status and Git Tools ──────────────────────────────────────────────────


@tool(
    "session_set_status",
    "Set the session execution status. Valid statuses: active, paused, complete, failed.",
    {
        "session_dir": str,
        "status": str,
    },
)
async def session_set_status(args: dict[str, Any]) -> dict[str, Any]:
    """Set the session execution status.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - status: Target status (active, paused, complete, failed)

    Returns:
        MCP tool response with success/error message
    """
    from state_manager import Status

    session_dir = args["session_dir"]
    status_str = args["status"]

    try:
        # Validate status string
        try:
            status = Status(status_str)
        except ValueError:
            valid_statuses = ", ".join(s.value for s in Status)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid status '{status_str}'. Valid statuses: {valid_statuses}",
                    }
                ]
            }

        manager = _create_manager(session_dir)
        manager.load()
        old_status = manager.state.status
        manager.set_status(status)

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Status changed from '{old_status.value}' to '{status.value}'.\n"
                        f"Session: {manager.state.session_id}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }


@tool(
    "session_set_git",
    "Set git context for a session. Can set branch and/or worktree path.",
    {
        "session_dir": str,
        "branch": str,
        "worktree": str,
    },
)
async def session_set_git(args: dict[str, Any]) -> dict[str, Any]:
    """Set git context for a session.

    Args:
        args: Dictionary with:
            - session_dir: Path to the session directory containing state.json
            - branch: (Optional) The git branch name
            - worktree: (Optional) The git worktree path

    Returns:
        MCP tool response with success/error message
    """
    session_dir = args["session_dir"]
    branch = args.get("branch")
    worktree = args.get("worktree")

    try:
        manager = _create_manager(session_dir)
        manager.load()

        changes = []
        if branch is not None:
            manager.set_git_branch(branch)
            changes.append(f"branch={branch}")
        if worktree is not None:
            manager.set_git_worktree(worktree if worktree else None)
            changes.append(f"worktree={worktree or 'None'}")

        if not changes:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No changes: Neither branch nor worktree was provided.",
                    }
                ]
            }

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Success: Updated git context - {', '.join(changes)}.\n"
                        f"Session: {manager.state.session_id}"
                    ),
                }
            ]
        }

    except SessionNotFoundError as e:
        return {"content": [{"type": "text", "text": f"Error: Session not found - {e}"}]}

    except Exception as e:
        return {
            "content": [
                {"type": "text", "text": f"Error: Unexpected error - {type(e).__name__}: {e}"}
            ]
        }
