"""Tests for database sync functions.

Tests cover:
- sync_session_from_filesystem: single session sync/upsert
- onboard_project_sessions: batch sync all sessions
- sync_all_sessions_in_project: full sync with summary
- v1/v2 state.json compatibility
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from database.sync import (
    sync_session_from_filesystem,
    onboard_project_sessions,
    sync_all_sessions_in_project,
    map_state_to_session_create,
    map_state_to_session_update,
    SessionNotFoundOnFilesystem,
    InvalidStateJson,
)
from database.crud import get_session_by_slug


# ═══════════════════════════════════════════════════════════════════════════════
# MAPPING FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestMapStateToSessionCreate:
    """Tests for map_state_to_session_create function."""

    def test_maps_v2_state_correctly(self, sample_state_v2: dict):
        """V2 state.json fields are correctly mapped."""
        result = map_state_to_session_create(
            state=sample_state_v2,
            session_slug="test-session",
            working_dir="/path/to/project",
            session_dir="/path/to/project/agents/sessions/test-session",
            project_id=None,
        )

        assert result.session_slug == "test-session"
        assert result.title == sample_state_v2["topic"]
        assert result.description == sample_state_v2["description"]
        assert result.session_type == "full"
        assert result.current_phase == "spec"
        assert result.status == "active"
        assert result.git_branch == "feature/test"
        assert result.git_base_branch == "main"
        assert result.checkpoints_total == 0  # None in state maps to 0
        assert result.checkpoints_completed_list == []
        assert result.artifacts["spec"] == "spec.md"

    def test_maps_v1_state_correctly(self, sample_state_v1: dict):
        """V1 (legacy) state.json fields are correctly mapped."""
        result = map_state_to_session_create(
            state=sample_state_v1,
            session_slug="legacy-session",
            working_dir="/path/to/project",
            session_dir="/path/to/project/agents/sessions/legacy-session",
            project_id=None,
        )

        assert result.session_slug == "legacy-session"
        assert result.title == sample_state_v1["topic"]
        assert result.session_type == "full"  # granularity mapped to session_type
        assert result.current_phase == "build"
        # V1 didn't have separate status, defaults to active
        assert result.checkpoints_total == 5
        assert result.checkpoints_completed_list == [1, 2]
        assert result.current_checkpoint == 3
        # V1 commits have checkpoint_id instead of checkpoint
        assert len(result.commits_list) == 1
        assert result.commits_list[0]["checkpoint"] == 1

    def test_sets_project_id(self, sample_state_v2: dict):
        """Project ID is correctly set when provided."""
        project_id = uuid4()

        result = map_state_to_session_create(
            state=sample_state_v2,
            session_slug="test-session",
            working_dir="/path/to/project",
            session_dir="/path/to/project/agents/sessions/test-session",
            project_id=project_id,
        )

        assert result.project_id == project_id


class TestMapStateToSessionUpdate:
    """Tests for map_state_to_session_update function."""

    def test_maps_v2_state_for_update(self, sample_state_in_build: dict, tmp_path: Path):
        """V2 state in build phase maps correctly for update."""
        session_dir = tmp_path / "session"
        session_dir.mkdir()
        (session_dir / "spec.md").write_text("# Spec")
        (session_dir / "plan.json").write_text("{}")

        result = map_state_to_session_update(
            state=sample_state_in_build,
            session_dir=str(session_dir),
        )

        assert result.current_phase == "build"
        assert result.status == "active"
        assert result.checkpoints_total == 5
        assert result.checkpoints_completed == 3  # len([1, 2, 3])
        assert result.checkpoints_completed_list == [1, 2, 3]
        assert result.current_checkpoint == 4
        assert len(result.commits_list) == 3
        assert result.spec_exists is True
        assert result.plan_exists is True


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyncSessionFromFilesystem:
    """Tests for sync_session_from_filesystem function."""

    @pytest.mark.asyncio
    async def test_creates_new_session(
        self,
        db_session: AsyncSession,
        temp_session_dir_v2: tuple[Path, str],
    ):
        """Syncing a new session creates it in the database."""
        working_dir, session_slug = temp_session_dir_v2

        session = await sync_session_from_filesystem(
            db=db_session,
            working_dir=str(working_dir),
            session_slug=session_slug,
        )

        assert session is not None
        assert session.session_slug == session_slug
        assert session.title == "Test Session"
        assert session.current_phase == "spec"
        assert session.status == "active"
        assert session.spec_exists is True
        assert session.plan_exists is False

    @pytest.mark.asyncio
    async def test_updates_existing_session(
        self,
        db_session: AsyncSession,
        temp_session_dir_v2: tuple[Path, str],
    ):
        """Syncing an existing session updates it."""
        working_dir, session_slug = temp_session_dir_v2

        # First sync
        session1 = await sync_session_from_filesystem(
            db=db_session,
            working_dir=str(working_dir),
            session_slug=session_slug,
        )

        # Modify state.json
        state_path = working_dir / "agents" / "sessions" / session_slug / "state.json"
        state = json.loads(state_path.read_text())
        state["current_phase"] = "plan"
        state["topic"] = "Updated Title"
        state_path.write_text(json.dumps(state))

        # Second sync
        session2 = await sync_session_from_filesystem(
            db=db_session,
            working_dir=str(working_dir),
            session_slug=session_slug,
        )

        assert session2.id == session1.id  # Same record updated
        assert session2.current_phase == "plan"
        assert session2.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_raises_on_missing_state_json(
        self,
        db_session: AsyncSession,
        temp_project_dir: Path,
    ):
        """Raises SessionNotFoundOnFilesystem when state.json doesn't exist."""
        # Create session dir without state.json
        session_slug = "missing-state"
        session_dir = temp_project_dir / "agents" / "sessions" / session_slug
        session_dir.mkdir(parents=True)

        with pytest.raises(SessionNotFoundOnFilesystem) as exc_info:
            await sync_session_from_filesystem(
                db=db_session,
                working_dir=str(temp_project_dir),
                session_slug=session_slug,
            )

        assert exc_info.value.session_slug == session_slug

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(
        self,
        db_session: AsyncSession,
        temp_project_dir: Path,
    ):
        """Raises InvalidStateJson when state.json is malformed."""
        session_slug = "invalid-json"
        session_dir = temp_project_dir / "agents" / "sessions" / session_slug
        session_dir.mkdir(parents=True)
        (session_dir / "state.json").write_text("{ invalid json }")

        with pytest.raises(InvalidStateJson) as exc_info:
            await sync_session_from_filesystem(
                db=db_session,
                working_dir=str(temp_project_dir),
                session_slug=session_slug,
            )

        assert exc_info.value.session_slug == session_slug

    @pytest.mark.asyncio
    async def test_sets_project_id(
        self,
        db_session: AsyncSession,
        temp_session_dir_v2: tuple[Path, str],
    ):
        """Project ID is correctly associated with session."""
        working_dir, session_slug = temp_session_dir_v2
        project_id = uuid4()

        session = await sync_session_from_filesystem(
            db=db_session,
            working_dir=str(working_dir),
            session_slug=session_slug,
            project_id=project_id,
        )

        assert session.project_id == project_id

    @pytest.mark.asyncio
    async def test_handles_v1_state_format(
        self,
        db_session: AsyncSession,
        temp_session_dir_v1: tuple[Path, str],
    ):
        """V1 (legacy) state.json format is correctly synced."""
        working_dir, session_slug = temp_session_dir_v1

        session = await sync_session_from_filesystem(
            db=db_session,
            working_dir=str(working_dir),
            session_slug=session_slug,
        )

        assert session.session_slug == session_slug
        assert session.current_phase == "build"
        assert session.checkpoints_total == 5
        assert session.checkpoints_completed == 2  # len([1, 2])
        assert session.checkpoints_completed_list == [1, 2]
        assert session.current_checkpoint == 3
        assert session.spec_exists is True
        assert session.plan_exists is True


class TestOnboardProjectSessions:
    """Tests for onboard_project_sessions function."""

    @pytest.mark.asyncio
    async def test_syncs_all_valid_sessions(
        self,
        db_session: AsyncSession,
        temp_multiple_sessions: tuple[Path, list[str]],
    ):
        """All valid sessions are synced, invalid ones are skipped."""
        working_dir, session_slugs = temp_multiple_sessions
        project_id = uuid4()

        sessions = await onboard_project_sessions(
            db=db_session,
            working_dir=str(working_dir),
            project_id=project_id,
        )

        # Only 2 valid sessions (3rd has no state.json)
        assert len(sessions) == 2
        assert all(s.project_id == project_id for s in sessions)

        # Check session details
        slugs = {s.session_slug for s in sessions}
        assert "2026-01-01_test-session" in slugs
        assert "2026-01-15_build-test" in slugs
        assert "2026-01-20_invalid-session" not in slugs

    @pytest.mark.asyncio
    async def test_returns_empty_for_missing_directory(
        self,
        db_session: AsyncSession,
        tmp_path: Path,
    ):
        """Returns empty list when agents/sessions doesn't exist."""
        sessions = await onboard_project_sessions(
            db=db_session,
            working_dir=str(tmp_path),
            project_id=uuid4(),
        )

        assert sessions == []


class TestSyncAllSessionsInProject:
    """Tests for sync_all_sessions_in_project function."""

    @pytest.mark.asyncio
    async def test_returns_sync_summary(
        self,
        db_session: AsyncSession,
        temp_multiple_sessions: tuple[Path, list[str]],
    ):
        """Returns summary with synced and failed sessions."""
        working_dir, session_slugs = temp_multiple_sessions

        result = await sync_all_sessions_in_project(
            db=db_session,
            working_dir=str(working_dir),
        )

        assert "synced" in result
        assert "failed" in result
        assert "total" in result
        assert result["total"] == 3  # 2 synced + 1 invalid
        assert len(result["synced"]) == 2
        assert len(result["failed"]) == 1

        # Check failed entry
        failed = result["failed"][0]
        assert failed["session_slug"] == "2026-01-20_invalid-session"
        assert failed["error"] == "state.json not found"

    @pytest.mark.asyncio
    async def test_synced_entries_have_details(
        self,
        db_session: AsyncSession,
        temp_multiple_sessions: tuple[Path, list[str]],
    ):
        """Synced entries include session details."""
        working_dir, _ = temp_multiple_sessions

        result = await sync_all_sessions_in_project(
            db=db_session,
            working_dir=str(working_dir),
        )

        for entry in result["synced"]:
            assert "session_slug" in entry
            assert "id" in entry
            assert "current_phase" in entry
            assert "status" in entry
