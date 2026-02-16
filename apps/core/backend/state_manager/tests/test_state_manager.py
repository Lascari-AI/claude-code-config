"""Unit tests for SessionStateManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .. import (
    InvalidPhaseTransitionError,
    Phase,
    SessionNotFoundError,
    SessionState,
    SessionStateManager,
)


class TestLoad:
    """Tests for SessionStateManager.load()."""

    def test_load_returns_session_state(self, temp_session_dir: Path) -> None:
        """load() should return a SessionState instance with correct data."""
        manager = SessionStateManager(temp_session_dir)
        state = manager.load()

        assert isinstance(state, SessionState)
        assert state.session_id == "2026-01-01_test-session"
        assert state.topic == "Test Session"
        assert state.current_phase == Phase.spec

    def test_load_missing_file_raises(self, empty_session_dir: Path) -> None:
        """load() should raise SessionNotFoundError when state.json is missing."""
        manager = SessionStateManager(empty_session_dir)

        with pytest.raises(SessionNotFoundError) as exc_info:
            manager.load()

        assert exc_info.value.session_id == "empty-session"
        assert "state.json" in exc_info.value.path


class TestSave:
    """Tests for SessionStateManager.save()."""

    def test_save_updates_file(self, temp_session_dir: Path) -> None:
        """save() should persist changes to state.json."""
        manager = SessionStateManager(temp_session_dir)
        state = manager.load()

        # Modify the state
        original_topic = state.topic
        state.topic = "Modified Topic"
        manager.save()

        # Re-read the file directly
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["topic"] == "Modified Topic"
        assert saved_data["topic"] != original_topic

    def test_save_updates_timestamp(self, temp_session_dir: Path) -> None:
        """save() should update the updated_at timestamp."""
        manager = SessionStateManager(temp_session_dir)
        state = manager.load()

        original_updated_at = state.updated_at
        manager.save()

        # Re-read and check timestamp changed
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["updated_at"] != original_updated_at.isoformat()


class TestTransition:
    """Tests for SessionStateManager.transition_to_phase()."""

    def test_transition_spec_to_plan_succeeds(self, temp_session_dir: Path) -> None:
        """Transition from spec to plan should succeed."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        assert manager.state.current_phase == Phase.spec

        manager.transition_to_phase(Phase.plan)

        assert manager.state.current_phase == Phase.plan

        # Verify persisted to file
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["current_phase"] == "plan"

    def test_transition_spec_to_build_fails(self, temp_session_dir: Path) -> None:
        """Transition from spec directly to build should raise InvalidPhaseTransitionError."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        with pytest.raises(InvalidPhaseTransitionError) as exc_info:
            manager.transition_to_phase(Phase.build)

        assert exc_info.value.from_phase == "spec"
        assert exc_info.value.to_phase == "build"

        # State should not have changed
        assert manager.state.current_phase == Phase.spec

    def test_transition_updates_phase_history(self, temp_session_dir: Path) -> None:
        """Transition should update phase_history timestamps."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        # Before transition
        assert manager.state.phase_history.spec_completed_at is None
        assert manager.state.phase_history.plan_started_at is None

        manager.transition_to_phase(Phase.plan)

        # After transition
        assert manager.state.phase_history.spec_completed_at is not None
        assert manager.state.phase_history.plan_started_at is not None

        # The two timestamps should be the same (transition happens atomically)
        assert (
            manager.state.phase_history.spec_completed_at
            == manager.state.phase_history.plan_started_at
        )

    def test_transition_plan_to_build_succeeds(self, temp_session_dir: Path) -> None:
        """Full transition chain: spec → plan → build."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        # spec → plan
        manager.transition_to_phase(Phase.plan)
        assert manager.state.current_phase == Phase.plan

        # plan → build
        manager.transition_to_phase(Phase.build)
        assert manager.state.current_phase == Phase.build

    def test_transition_build_to_complete_succeeds(self, temp_session_dir: Path) -> None:
        """Build can transition directly to complete (skipping docs)."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        # Navigate to build phase
        manager.transition_to_phase(Phase.plan)
        manager.transition_to_phase(Phase.build)

        # build → complete (valid shortcut)
        manager.transition_to_phase(Phase.complete)
        assert manager.state.current_phase == Phase.complete
