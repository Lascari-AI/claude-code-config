"""Custom exceptions for StateManager operations."""


class InvalidPhaseTransitionError(Exception):
    """Raised when attempting an invalid phase transition.

    Phase transitions must follow the allowed sequence:
    spec → plan → build → docs → complete

    Attributes:
        from_phase: The current phase
        to_phase: The attempted target phase
    """

    def __init__(self, from_phase: str, to_phase: str):
        self.from_phase = from_phase
        self.to_phase = to_phase
        super().__init__(f"Invalid phase transition: {from_phase} → {to_phase}")


class SessionNotFoundError(Exception):
    """Raised when session state.json is not found at expected path.

    Attributes:
        session_id: The session identifier
        path: The path where state.json was expected
    """

    def __init__(self, session_id: str, path: str):
        self.session_id = session_id
        self.path = path
        super().__init__(f"Session not found: {session_id} at {path}")


class StateValidationError(Exception):
    """Raised when state.json fails Pydantic validation.

    This wraps Pydantic ValidationError to provide a consistent
    exception interface for StateManager consumers.
    """

    pass
