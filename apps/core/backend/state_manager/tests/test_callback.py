"""Unit tests for StateManager on_save_callback functionality."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from .. import SessionStateManager


class TestCallback:
    """Tests for on_save_callback functionality in SessionStateManager."""

    def test_callback_invoked_after_save(self, temp_session_dir: Path) -> None:
        """Callback should be invoked after successful save()."""
        callback = Mock()
        manager = SessionStateManager(temp_session_dir, on_save_callback=callback)
        manager.load()
        manager.save()

        callback.assert_called_once_with(temp_session_dir)

    def test_callback_exception_does_not_break_save(self, temp_session_dir: Path) -> None:
        """save() should complete even if callback raises an exception."""
        callback = Mock(side_effect=RuntimeError("Callback failed"))
        manager = SessionStateManager(temp_session_dir, on_save_callback=callback)
        state = manager.load()

        # Modify state
        state.topic = "Modified by test"
        manager.save()

        # State file should still exist and be updated
        state_file = temp_session_dir / "state.json"
        assert state_file.exists()

        with open(state_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["topic"] == "Modified by test"

    def test_no_callback_works(self, temp_session_dir: Path) -> None:
        """save() should work normally when no callback is provided."""
        manager = SessionStateManager(temp_session_dir)
        manager.load()
        manager.save()

        state_file = temp_session_dir / "state.json"
        assert state_file.exists()

    def test_callback_receives_session_dir_path(self, temp_session_dir: Path) -> None:
        """Callback should receive the session_dir as a Path object."""
        received_args = []

        def capture_callback(session_dir: Path) -> None:
            received_args.append(session_dir)

        manager = SessionStateManager(temp_session_dir, on_save_callback=capture_callback)
        manager.load()
        manager.save()

        assert len(received_args) == 1
        assert received_args[0] == temp_session_dir
        assert isinstance(received_args[0], Path)
