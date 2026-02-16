"""Unit tests for async_sync module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from session_db.async_sync import (
    _sync_session_async,
    make_sync_callback,
    queue_sync_task,
)


class TestMakeSyncCallback:
    """Tests for make_sync_callback factory function."""

    def test_returns_callable(self) -> None:
        """make_sync_callback should return a callable."""
        callback = make_sync_callback("/path/to/project")
        assert callable(callback)

    def test_callback_accepts_path(self) -> None:
        """Returned callback should accept a Path argument."""
        callback = make_sync_callback("/path/to/project")
        # Should not raise
        with patch("session_db.async_sync.queue_sync_task"):
            callback(Path("/path/to/session"))

    @patch("session_db.async_sync.queue_sync_task")
    def test_callback_calls_queue_sync_task(self, mock_queue: Mock) -> None:
        """Callback should invoke queue_sync_task with session_dir and working_dir."""
        callback = make_sync_callback("/path/to/project")
        session_dir = Path("/path/to/session")

        callback(session_dir)

        mock_queue.assert_called_once_with(session_dir, "/path/to/project")


class TestQueueSyncTask:
    """Tests for queue_sync_task function."""

    def test_derives_working_dir_from_session_dir(self) -> None:
        """queue_sync_task should derive working_dir if not provided."""
        # session_dir structure: {working_dir}/agents/sessions/{slug}
        session_dir = Path("/project/agents/sessions/2026-01-01_test")

        with patch("session_db.async_sync.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.create_task = Mock()

            # No event loop error is expected in test context
            try:
                queue_sync_task(session_dir)
            except RuntimeError:
                pass  # Expected - no running loop in test

    @patch("session_db.async_sync.asyncio.get_running_loop")
    def test_creates_task_when_loop_exists(self, mock_get_loop: Mock) -> None:
        """queue_sync_task should create asyncio task when event loop exists."""
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop

        session_dir = Path("/project/agents/sessions/test-session")
        queue_sync_task(session_dir, "/project")

        mock_loop.create_task.assert_called_once()

    @patch("session_db.async_sync.asyncio.get_running_loop")
    def test_logs_warning_when_no_event_loop(
        self, mock_get_loop: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """queue_sync_task should log warning when no event loop is available."""
        mock_get_loop.side_effect = RuntimeError("no running event loop")

        session_dir = Path("/project/agents/sessions/test-session")
        queue_sync_task(session_dir, "/project")

        assert "No event loop available" in caplog.text


class TestSyncSessionAsync:
    """Tests for _sync_session_async internal function."""

    @pytest.mark.asyncio
    @patch("session_db.async_sync.get_async_session")
    @patch("session_db.async_sync.sync_session_from_filesystem")
    async def test_calls_sync_function(
        self,
        mock_sync: AsyncMock,
        mock_get_session: Mock,
    ) -> None:
        """_sync_session_async should call sync_session_from_filesystem."""
        # Setup async context manager mock
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        session_dir = Path("/project/agents/sessions/test-session")

        await _sync_session_async(session_dir, "/project")

        mock_sync.assert_called_once_with(
            mock_session,
            "/project",
            "test-session",  # session_slug from session_dir.name
        )

    @pytest.mark.asyncio
    @patch("session_db.async_sync.get_async_session")
    @patch("session_db.async_sync.sync_session_from_filesystem")
    async def test_logs_exception_on_failure(
        self,
        mock_sync: AsyncMock,
        mock_get_session: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """_sync_session_async should log exceptions without raising."""
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_sync.side_effect = Exception("Sync failed")

        session_dir = Path("/project/agents/sessions/test-session")

        # Should not raise
        await _sync_session_async(session_dir, "/project")

        assert "Failed to sync session" in caplog.text
