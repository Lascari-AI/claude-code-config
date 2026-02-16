"""StateManager package for programmatic session state management.

This package provides:
- SessionStateManager: The main interface for managing state.json
- SessionState: Pydantic model for the state.json v2 schema
- Phase, Status, SessionType: Enums for valid state values
- Exceptions for validation and transition errors

Example:
    from state_manager import SessionStateManager, Phase

    manager = SessionStateManager("/path/to/session")
    state = manager.load()
    print(f"Current phase: {state.current_phase}")

    # Transition to next phase (validates and saves)
    manager.transition_to_phase(Phase.plan)
"""

from .exceptions import (
    InvalidPhaseTransitionError,
    SessionNotFoundError,
    StateValidationError,
)
from .models import (
    Artifacts,
    BuildProgress,
    Commit,
    GitContext,
    Phase,
    PhaseHistory,
    SessionState,
    SessionType,
    Status,
)
from .state_manager import SaveCallback, SessionStateManager

__all__ = [
    # Main interface
    "SessionStateManager",
    # Type aliases
    "SaveCallback",
    # Root model
    "SessionState",
    # Enums
    "Phase",
    "Status",
    "SessionType",
    # Nested models (for type hints)
    "PhaseHistory",
    "BuildProgress",
    "GitContext",
    "Commit",
    "Artifacts",
    # Exceptions
    "InvalidPhaseTransitionError",
    "SessionNotFoundError",
    "StateValidationError",
]
