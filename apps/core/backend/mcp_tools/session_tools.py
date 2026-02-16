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
        manager = SessionStateManager(Path(session_dir))
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
