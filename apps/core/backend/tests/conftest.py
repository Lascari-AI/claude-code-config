"""Pytest fixtures for StateManager tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src directory to path for imports
_src_dir = Path(__file__).parent.parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_state_dict() -> dict[str, Any]:
    """Return a valid state.json v2 structure for testing.

    This fixture provides a minimal but complete state.json that passes
    validation. Use it as a base and modify for specific test cases.
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        # Identity
        "session_id": "2026-01-01_test-session",
        "topic": "Test Session",
        "description": "A test session for unit tests",
        "session_type": "full",
        # Timestamps
        "created_at": now,
        "updated_at": now,
        # Current state
        "current_phase": "spec",
        "status": "active",
        # Phase history
        "phase_history": {
            "spec_started_at": now,
            "spec_completed_at": None,
            "plan_started_at": None,
            "plan_completed_at": None,
            "build_started_at": None,
            "build_completed_at": None,
            "docs_started_at": None,
            "docs_completed_at": None,
        },
        # Build progress
        "build_progress": {
            "checkpoints_total": None,
            "checkpoints_completed": [],
            "current_checkpoint": None,
        },
        # Git context
        "git": {
            "branch": None,
            "worktree": None,
            "base_branch": None,
        },
        # Commits
        "commits": [],
        # Artifacts
        "artifacts": {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
    }


@pytest.fixture
def temp_session_dir(tmp_path: Path, sample_state_dict: dict[str, Any]) -> Path:
    """Create a temporary session directory with a valid state.json.

    Args:
        tmp_path: Pytest's temporary directory fixture
        sample_state_dict: The sample state data to write

    Returns:
        Path to the temporary session directory
    """
    session_dir = tmp_path / "test-session"
    session_dir.mkdir()

    state_file = session_dir / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(sample_state_dict, f, indent=2)

    return session_dir


@pytest.fixture
def empty_session_dir(tmp_path: Path) -> Path:
    """Create an empty session directory (no state.json).

    Useful for testing SessionNotFoundError scenarios.
    """
    session_dir = tmp_path / "empty-session"
    session_dir.mkdir()
    return session_dir
