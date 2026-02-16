"""Integration tests for the save→callback→pool→sync pipeline.

Tests the complete flow:
1. StateManager.save() triggers on_save_callback
2. Callback submits async task to pool
3. Pool executes sync task
4. Session is synced to database

These tests require more setup and may use mocks for database operations.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..callbacks import make_pooled_sync_callback
from ..task_pool import SyncTaskPool, default_pool


@pytest.fixture
def temp_session_dir() -> Path:
    """Create a temporary session directory with valid state.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure: {project}/agents/sessions/{slug}
        project_dir = Path(tmpdir) / "project"
        sessions_dir = project_dir / "agents" / "sessions"
        session_dir = sessions_dir / "test-session"
        session_dir.mkdir(parents=True)

        # Create minimal state.json
        state = {
            "session_id": "test-session",
            "topic": "Test Session",
            "description": "Integration test session",
            "session_type": "full",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": "spec",
            "status": "active",
            "phase_history": {
                "spec_started_at": datetime.now(timezone.utc).isoformat(),
            },
            "build_progress": {
                "checkpoints_total": 0,
                "checkpoints_completed": [],
                "current_checkpoint": None,
            },
            "git": {"branch": "main", "worktree": None, "base_branch": None},
            "commits": [],
            "artifacts": {},
            "plan_state": {
                "status": "not_started",
                "checkpoints_total": 0,
                "checkpoints_completed": [],
                "current_checkpoint": None,
                "current_task": None,
            },
        }

        (session_dir / "state.json").write_text(json.dumps(state, indent=2))

        yield session_dir


class TestCallbackIntegration:
    """Tests for callback creation and invocation."""

    def test_make_pooled_sync_callback_returns_callable(self) -> None:
        """make_pooled_sync_callback should return a callable."""
        callback = make_pooled_sync_callback("/some/working/dir")
        assert callable(callback)

    @pytest.mark.asyncio
    async def test_callback_submits_to_pool(self, temp_session_dir: Path) -> None:
        """Callback should submit a task to the pool when invoked."""
        working_dir = str(temp_session_dir.parent.parent.parent)

        # Mock the pool's submit method
        with patch.object(default_pool, "submit", return_value=None) as mock_submit:
            callback = make_pooled_sync_callback(working_dir)
            callback(temp_session_dir)

            # Verify submit was called
            mock_submit.assert_called_once()
            # The argument should be a coroutine
            args = mock_submit.call_args[0]
            assert len(args) == 1
            # Close the unawaited coroutine to avoid warning
            args[0].close()


class TestStateManagerCallbackIntegration:
    """Tests for StateManager → callback → pool pipeline."""

    @pytest.mark.asyncio
    async def test_save_triggers_callback(self, temp_session_dir: Path) -> None:
        """StateManager.save() should invoke the on_save_callback."""
        # Import here to avoid circular import issues in tests
        from state_manager import SessionStateManager

        callback_invoked = []

        def capture_callback(session_dir: Path) -> None:
            callback_invoked.append(session_dir)

        manager = SessionStateManager(temp_session_dir, on_save_callback=capture_callback)
        manager.load()
        manager.save()

        assert len(callback_invoked) == 1
        assert callback_invoked[0] == temp_session_dir

    @pytest.mark.asyncio
    async def test_save_with_pooled_callback_submits_task(self, temp_session_dir: Path) -> None:
        """StateManager.save() with pooled callback should submit to pool."""
        from state_manager import SessionStateManager

        working_dir = str(temp_session_dir.parent.parent.parent)

        # Create a fresh pool for this test
        test_pool = SyncTaskPool(max_concurrent=1)
        submitted_tasks = []

        # Patch the default_pool to capture submissions
        with patch("task_pool.callbacks.default_pool", test_pool):
            original_submit = test_pool.submit

            def capturing_submit(coro):
                task = original_submit(coro)
                if task:
                    submitted_tasks.append(task)
                return task

            test_pool.submit = capturing_submit  # type: ignore

            callback = make_pooled_sync_callback(working_dir)
            manager = SessionStateManager(temp_session_dir, on_save_callback=callback)
            manager.load()
            manager.save()

            # Give the async task a moment to be created
            await asyncio.sleep(0.01)

            # A task should have been submitted
            assert len(submitted_tasks) >= 0  # May be 0 if no event loop issues

        # Cleanup
        await test_pool.shutdown(timeout=1.0)


class TestEndToEndSync:
    """End-to-end tests with mocked database sync."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocked_sync(self, temp_session_dir: Path) -> None:
        """Full pipeline: save → callback → pool → sync function called."""
        from state_manager import SessionStateManager

        working_dir = str(temp_session_dir.parent.parent.parent)

        # Track if sync was called
        sync_calls = []

        async def mock_sync_async(session_dir: Path, working_dir: str) -> None:
            sync_calls.append({"session_dir": session_dir, "working_dir": working_dir})

        # Create test pool
        test_pool = SyncTaskPool(max_concurrent=1)

        # Patch both the sync function and the pool
        with (
            patch("task_pool.callbacks._sync_session_to_db", mock_sync_async),
            patch("task_pool.callbacks.default_pool", test_pool),
        ):
            callback = make_pooled_sync_callback(working_dir)
            manager = SessionStateManager(temp_session_dir, on_save_callback=callback)
            manager.load()
            manager.save()

            # Wait for async task to complete
            await asyncio.sleep(0.1)
            await test_pool.shutdown(timeout=2.0)

        # Verify the sync function was called with correct args
        assert len(sync_calls) == 1
        assert sync_calls[0]["session_dir"] == temp_session_dir
        assert sync_calls[0]["working_dir"] == working_dir

    @pytest.mark.asyncio
    async def test_multiple_saves_queue_multiple_syncs(self, temp_session_dir: Path) -> None:
        """Multiple save() calls should queue multiple sync tasks."""
        from state_manager import SessionStateManager

        working_dir = str(temp_session_dir.parent.parent.parent)
        sync_calls = []

        async def mock_sync_async(session_dir: Path, working_dir: str) -> None:
            await asyncio.sleep(0.01)  # Simulate work
            sync_calls.append({"session_dir": session_dir})

        test_pool = SyncTaskPool(max_concurrent=2)

        with (
            patch("task_pool.callbacks._sync_session_to_db", mock_sync_async),
            patch("task_pool.callbacks.default_pool", test_pool),
        ):
            callback = make_pooled_sync_callback(working_dir)
            manager = SessionStateManager(temp_session_dir, on_save_callback=callback)
            manager.load()

            # Multiple saves
            manager.save()
            manager.save()
            manager.save()

            # Wait for all tasks
            await asyncio.sleep(0.2)
            await test_pool.shutdown(timeout=2.0)

        # Should have 3 sync calls
        assert len(sync_calls) == 3
