"""SessionStateManager: Programmatic state.json management with validated transitions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .exceptions import (
    InvalidPhaseTransitionError,
    SessionNotFoundError,
    StateValidationError,
)
from .models import Phase, SessionState, Status


class SessionStateManager:
    """Manages session state.json with validated phase transitions.

    The StateManager is the only interface for modifying state.json.
    It ensures:
    - Phase transitions follow the allowed sequence
    - Timestamps are updated appropriately
    - State is always valid according to the v2 schema

    Usage:
        manager = SessionStateManager(Path("/path/to/session"))
        state = manager.load()
        manager.transition_to_phase(Phase.plan)  # Validates and saves

    Attributes:
        session_dir: Path to the session directory containing state.json
    """

    # Valid phase transitions: current_phase -> [allowed_next_phases]
    VALID_TRANSITIONS: dict[Phase, list[Phase]] = {
        Phase.spec: [Phase.plan],
        Phase.plan: [Phase.build],
        Phase.build: [Phase.docs, Phase.complete],
        Phase.docs: [Phase.complete],
        Phase.complete: [],
    }

    def __init__(self, session_dir: Path | str) -> None:
        """Initialize StateManager for a session directory.

        Args:
            session_dir: Path to session directory (contains state.json)
        """
        self.session_dir = Path(session_dir)
        self._state: Optional[SessionState] = None

    @property
    def state_file(self) -> Path:
        """Path to the state.json file."""
        return self.session_dir / "state.json"

    @property
    def state(self) -> SessionState:
        """Get current state, loading if necessary.

        Raises:
            SessionNotFoundError: If state.json doesn't exist
            StateValidationError: If state.json is invalid
        """
        if self._state is None:
            self.load()
        return self._state  # type: ignore[return-value]

    def load(self) -> SessionState:
        """Load and parse state.json from disk.

        Returns:
            The parsed SessionState

        Raises:
            SessionNotFoundError: If state.json doesn't exist
            StateValidationError: If state.json fails validation
        """
        if not self.state_file.exists():
            raise SessionNotFoundError(
                session_id=self.session_dir.name,
                path=str(self.state_file),
            )

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._state = SessionState.model_validate(data)
            return self._state
        except ValidationError as e:
            raise StateValidationError(f"Invalid state.json: {e}") from e

    def save(self) -> None:
        """Write current state to state.json.

        Updates the updated_at timestamp before saving.

        Raises:
            RuntimeError: If no state has been loaded
        """
        if self._state is None:
            raise RuntimeError("No state loaded. Call load() first.")

        # Update timestamp
        self._state.updated_at = datetime.now(timezone.utc)

        # Write atomically (write to temp, then rename)
        temp_file = self.state_file.with_suffix(".json.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                self._state.model_dump(mode="json"),
                f,
                indent=2,
                default=str,  # Handle datetime serialization
            )
            f.write("\n")  # Trailing newline

        temp_file.rename(self.state_file)

    def _validate_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """Check if a phase transition is valid.

        Args:
            from_phase: Current phase
            to_phase: Target phase

        Returns:
            True if transition is allowed, False otherwise
        """
        allowed = self.VALID_TRANSITIONS.get(from_phase, [])
        return to_phase in allowed

    def transition_to_phase(self, new_phase: Phase) -> None:
        """Transition the session to a new phase.

        Validates the transition, updates phase_history timestamps,
        and saves the state.

        Args:
            new_phase: The target phase to transition to

        Raises:
            InvalidPhaseTransitionError: If transition is not allowed
            RuntimeError: If no state has been loaded
        """
        current_phase = self.state.current_phase
        current_phase_enum = (
            Phase(current_phase) if isinstance(current_phase, str) else current_phase
        )

        new_phase_enum = Phase(new_phase) if isinstance(new_phase, str) else new_phase

        if not self._validate_transition(current_phase_enum, new_phase_enum):
            raise InvalidPhaseTransitionError(
                from_phase=str(current_phase_enum.value),
                to_phase=str(new_phase_enum.value),
            )

        now = datetime.now(timezone.utc)

        # Mark current phase as completed
        completed_at_field = f"{current_phase_enum.value}_completed_at"
        setattr(self._state.phase_history, completed_at_field, now)

        # Mark new phase as started (but 'complete' is terminal - no start timestamp)
        if new_phase_enum != Phase.complete:
            started_at_field = f"{new_phase_enum.value}_started_at"
            setattr(self._state.phase_history, started_at_field, now)

        # Update current phase
        self._state.current_phase = new_phase_enum

        # Save changes
        self.save()

    # ─── Checkpoint Tracking ──────────────────────────────────────────────────

    def init_build_progress(self, checkpoints_total: int) -> None:
        """Initialize build progress for build phase.

        Should be called when transitioning to build phase or when
        the plan is finalized with checkpoint count.

        Args:
            checkpoints_total: Total number of checkpoints in the plan

        Raises:
            ValueError: If checkpoints_total is not positive
            RuntimeError: If no state has been loaded
        """
        if checkpoints_total < 1:
            raise ValueError("checkpoints_total must be at least 1")

        self.state.build_progress.checkpoints_total = checkpoints_total
        self.state.build_progress.checkpoints_completed = []
        self.state.build_progress.current_checkpoint = 1
        self.save()

    def start_checkpoint(self, checkpoint_id: int) -> None:
        """Set the current active checkpoint.

        Args:
            checkpoint_id: The checkpoint ID to start (1-indexed)

        Raises:
            ValueError: If checkpoint_id is invalid
            RuntimeError: If no state has been loaded
        """
        total = self.state.build_progress.checkpoints_total
        if total is None:
            raise ValueError("build_progress not initialized. Call init_build_progress first.")
        if checkpoint_id < 1 or checkpoint_id > total:
            raise ValueError(f"checkpoint_id must be between 1 and {total}")

        self.state.build_progress.current_checkpoint = checkpoint_id
        self.save()

    def complete_checkpoint(self, checkpoint_id: int) -> None:
        """Mark a checkpoint as completed.

        Adds checkpoint to completed list and advances current_checkpoint.
        Does not modify current_checkpoint if this is the last checkpoint.

        Args:
            checkpoint_id: The checkpoint ID that was completed

        Raises:
            ValueError: If checkpoint is invalid or already completed
            RuntimeError: If no state has been loaded
        """
        total = self.state.build_progress.checkpoints_total
        if total is None:
            raise ValueError("build_progress not initialized. Call init_build_progress first.")
        if checkpoint_id < 1 or checkpoint_id > total:
            raise ValueError(f"checkpoint_id must be between 1 and {total}")

        completed = self.state.build_progress.checkpoints_completed
        if checkpoint_id in completed:
            raise ValueError(f"Checkpoint {checkpoint_id} is already completed")

        completed.append(checkpoint_id)
        completed.sort()  # Keep list sorted

        # Advance current_checkpoint if not at the end
        if checkpoint_id < total:
            self.state.build_progress.current_checkpoint = checkpoint_id + 1
        else:
            # Last checkpoint - set to None to indicate completion
            self.state.build_progress.current_checkpoint = None

        self.save()

    # ─── Commit Tracking ──────────────────────────────────────────────────────

    def add_commit(
        self,
        sha: str,
        message: str,
        checkpoint: Optional[int] = None,
    ) -> None:
        """Record a git commit made during the session.

        Args:
            sha: The commit SHA (short or full)
            message: The commit message
            checkpoint: Optional checkpoint ID this commit relates to

        Raises:
            RuntimeError: If no state has been loaded
        """
        from .models import Commit

        commit = Commit(
            sha=sha,
            message=message,
            checkpoint=checkpoint,
            created_at=datetime.now(timezone.utc),
        )
        self.state.commits.append(commit)
        self.save()

    # ─── Status and Git Context ───────────────────────────────────────────────

    def set_status(self, status: Status) -> None:
        """Set the session execution status.

        Args:
            status: The new status (active, paused, complete, failed)

        Raises:
            RuntimeError: If no state has been loaded
        """
        status_enum = Status(status) if isinstance(status, str) else status
        self.state.status = status_enum
        self.save()

    def set_git_branch(self, branch: str) -> None:
        """Set the git branch for this session.

        Args:
            branch: The branch name

        Raises:
            RuntimeError: If no state has been loaded
        """
        self.state.git.branch = branch
        self.save()

    def set_git_worktree(self, worktree: Optional[str]) -> None:
        """Set the git worktree path for this session.

        Args:
            worktree: The worktree path, or None if not using a worktree

        Raises:
            RuntimeError: If no state has been loaded
        """
        self.state.git.worktree = worktree
        self.save()
