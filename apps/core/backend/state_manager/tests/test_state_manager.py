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


class TestCheckpointTracking:
    """Tests for checkpoint tracking methods."""

    def test_init_build_progress(self, temp_session_dir: Path) -> None:
        """init_build_progress should initialize checkpoints_total and reset completed."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.init_build_progress(5)

        assert manager.state.build_progress.checkpoints_total == 5
        assert manager.state.build_progress.checkpoints_completed == []
        assert manager.state.build_progress.current_checkpoint == 1

        # Verify persisted
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["build_progress"]["checkpoints_total"] == 5

    def test_init_build_progress_invalid_total(self, temp_session_dir: Path) -> None:
        """init_build_progress should reject non-positive totals."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        with pytest.raises(ValueError) as exc_info:
            manager.init_build_progress(0)
        assert "at least 1" in str(exc_info.value)

    def test_complete_checkpoint(self, temp_session_dir: Path) -> None:
        """complete_checkpoint should add checkpoint to completed list."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(3)

        manager.complete_checkpoint(1)

        assert 1 in manager.state.build_progress.checkpoints_completed
        assert manager.state.build_progress.current_checkpoint == 2

    def test_complete_checkpoint_advances_current(self, temp_session_dir: Path) -> None:
        """complete_checkpoint should advance current_checkpoint."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(3)

        manager.complete_checkpoint(1)
        assert manager.state.build_progress.current_checkpoint == 2

        manager.complete_checkpoint(2)
        assert manager.state.build_progress.current_checkpoint == 3

    def test_complete_final_checkpoint_sets_current_to_none(self, temp_session_dir: Path) -> None:
        """Completing last checkpoint should set current_checkpoint to None."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(2)

        manager.complete_checkpoint(1)
        manager.complete_checkpoint(2)

        assert manager.state.build_progress.current_checkpoint is None

    def test_complete_invalid_checkpoint_fails(self, temp_session_dir: Path) -> None:
        """complete_checkpoint should reject invalid checkpoint IDs."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(3)

        with pytest.raises(ValueError) as exc_info:
            manager.complete_checkpoint(0)
        assert "between 1 and 3" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            manager.complete_checkpoint(4)
        assert "between 1 and 3" in str(exc_info.value)

    def test_complete_duplicate_checkpoint_fails(self, temp_session_dir: Path) -> None:
        """complete_checkpoint should reject already completed checkpoints."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(3)

        manager.complete_checkpoint(1)

        with pytest.raises(ValueError) as exc_info:
            manager.complete_checkpoint(1)
        assert "already completed" in str(exc_info.value)

    def test_start_checkpoint(self, temp_session_dir: Path) -> None:
        """start_checkpoint should set current_checkpoint."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.init_build_progress(5)

        manager.start_checkpoint(3)

        assert manager.state.build_progress.current_checkpoint == 3

    def test_start_checkpoint_without_init_fails(self, temp_session_dir: Path) -> None:
        """start_checkpoint should fail if build_progress not initialized."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        with pytest.raises(ValueError) as exc_info:
            manager.start_checkpoint(1)
        assert "not initialized" in str(exc_info.value)


class TestCommitTracking:
    """Tests for commit tracking methods."""

    def test_add_commit(self, temp_session_dir: Path) -> None:
        """add_commit should append commit with sha, message, checkpoint, created_at."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        assert len(manager.state.commits) == 0

        manager.add_commit(
            sha="abc1234",
            message="feat: add new feature",
            checkpoint=1,
        )

        assert len(manager.state.commits) == 1
        commit = manager.state.commits[0]
        assert commit.sha == "abc1234"
        assert commit.message == "feat: add new feature"
        assert commit.checkpoint == 1
        assert commit.created_at is not None

        # Verify persisted
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert len(saved_data["commits"]) == 1
        assert saved_data["commits"][0]["sha"] == "abc1234"

    def test_add_commit_without_checkpoint(self, temp_session_dir: Path) -> None:
        """add_commit should work without checkpoint association."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.add_commit(sha="def5678", message="chore: cleanup")

        assert len(manager.state.commits) == 1
        assert manager.state.commits[0].checkpoint is None

    def test_add_multiple_commits(self, temp_session_dir: Path) -> None:
        """Multiple commits should accumulate."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.add_commit(sha="aaa", message="first", checkpoint=1)
        manager.add_commit(sha="bbb", message="second", checkpoint=1)
        manager.add_commit(sha="ccc", message="third", checkpoint=2)

        assert len(manager.state.commits) == 3
        assert [c.sha for c in manager.state.commits] == ["aaa", "bbb", "ccc"]


class TestStatusAndGit:
    """Tests for status and git context methods."""

    def test_set_status(self, temp_session_dir: Path) -> None:
        """set_status should update status field."""
        from .. import Status

        manager = SessionStateManager(temp_session_dir)
        manager.load()

        assert manager.state.status == Status.active

        manager.set_status(Status.paused)
        assert manager.state.status == Status.paused

        # Verify persisted
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["status"] == "paused"

    def test_set_status_from_string(self, temp_session_dir: Path) -> None:
        """set_status should accept string status values."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.set_status("failed")  # type: ignore
        assert manager.state.status.value == "failed"

    def test_set_git_branch(self, temp_session_dir: Path) -> None:
        """set_git_branch should update git.branch."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.set_git_branch("feature/new-feature")

        assert manager.state.git.branch == "feature/new-feature"

        # Verify persisted
        state_file = temp_session_dir / "state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["git"]["branch"] == "feature/new-feature"

    def test_set_git_worktree(self, temp_session_dir: Path) -> None:
        """set_git_worktree should update git.worktree."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()

        manager.set_git_worktree("/path/to/worktree")
        assert manager.state.git.worktree == "/path/to/worktree"

        # Set to None
        manager.set_git_worktree(None)
        assert manager.state.git.worktree is None
