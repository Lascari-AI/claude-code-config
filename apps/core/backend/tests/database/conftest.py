"""Pytest fixtures for database tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from database.models import Session, Agent, AgentLog, Project


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite engine for testing.

    Uses SQLite instead of PostgreSQL for fast, isolated tests.
    Note: Some PostgreSQL-specific features may not work in SQLite.
    """
    # Use aiosqlite for async SQLite support
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing.

    Each test gets a fresh session with automatic rollback.
    """
    async_session_factory = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ═══════════════════════════════════════════════════════════════════════════════
# STATE.JSON FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_state_v2() -> dict[str, Any]:
    """Return a valid state.json v2 structure for testing."""
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
            "branch": "feature/test",
            "worktree": None,
            "base_branch": "main",
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
def sample_state_v1() -> dict[str, Any]:
    """Return a valid state.json v1 (legacy) structure for testing."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        # Identity
        "session_id": "2026-01-01_legacy-session",
        "topic": "Legacy Session",
        "description": "A legacy v1 session for testing",
        "granularity": "full",  # v1 used granularity instead of session_type
        # Timestamps
        "created_at": now,
        "updated_at": now,
        # Current phase
        "current_phase": "build",
        # Phases (v1 structure)
        "phases": {
            "spec": {
                "status": "finalized",
                "started_at": now,
                "finalized_at": now,
            },
            "plan": {
                "status": "finalized",
                "started_at": now,
                "finalized_at": now,
            },
            "build": {
                "status": "in_progress",
                "started_at": now,
                "completed_at": None,
            },
        },
        # Plan state (v1 build progress)
        "plan_state": {
            "status": "in_progress",
            "checkpoints_total": 5,
            "checkpoints_completed": [1, 2],
            "current_checkpoint": 3,
        },
        # Commits (v1 format with checkpoint_id)
        "commits": [
            {
                "sha": "abc123",
                "message": "feat: checkpoint 1",
                "checkpoint_id": 1,
                "created_at": now,
            },
        ],
        # v1 had goals in state.json
        "goals": {
            "high_level": ["Test goal"],
        },
    }


@pytest.fixture
def sample_state_in_build() -> dict[str, Any]:
    """Return a state.json v2 in build phase with progress."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "session_id": "2026-01-15_build-test",
        "topic": "Build Test Session",
        "description": "Session in build phase with checkpoints",
        "session_type": "full",
        "created_at": now,
        "updated_at": now,
        "current_phase": "build",
        "status": "active",
        "phase_history": {
            "spec_started_at": now,
            "spec_completed_at": now,
            "plan_started_at": now,
            "plan_completed_at": now,
            "build_started_at": now,
            "build_completed_at": None,
            "docs_started_at": None,
            "docs_completed_at": None,
        },
        "build_progress": {
            "checkpoints_total": 5,
            "checkpoints_completed": [1, 2, 3],
            "current_checkpoint": 4,
        },
        "git": {
            "branch": "feature/build-test",
            "worktree": None,
            "base_branch": "main",
        },
        "commits": [
            {
                "sha": "abc123",
                "message": "feat: checkpoint 1",
                "checkpoint": 1,
                "created_at": now,
            },
            {
                "sha": "def456",
                "message": "feat: checkpoint 2",
                "checkpoint": 2,
                "created_at": now,
            },
            {
                "sha": "ghi789",
                "message": "feat: checkpoint 3",
                "checkpoint": 3,
                "created_at": now,
            },
        ],
        "artifacts": {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FILESYSTEM FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure.

    Returns:
        Path to the temporary project root (working_dir)
    """
    project_dir = tmp_path / "test-project"
    sessions_dir = project_dir / "agents" / "sessions"
    sessions_dir.mkdir(parents=True)
    return project_dir


@pytest.fixture
def temp_session_dir_v2(
    temp_project_dir: Path,
    sample_state_v2: dict[str, Any],
) -> tuple[Path, str]:
    """Create a session directory with state.json v2.

    Returns:
        Tuple of (working_dir, session_slug)
    """
    session_slug = "2026-01-01_test-session"
    session_dir = temp_project_dir / "agents" / "sessions" / session_slug
    session_dir.mkdir(parents=True)

    # Write state.json
    state_path = session_dir / "state.json"
    state_path.write_text(json.dumps(sample_state_v2, indent=2))

    # Create spec.md
    (session_dir / "spec.md").write_text("# Test Spec\n")

    return temp_project_dir, session_slug


@pytest.fixture
def temp_session_dir_v1(
    temp_project_dir: Path,
    sample_state_v1: dict[str, Any],
) -> tuple[Path, str]:
    """Create a session directory with state.json v1 (legacy).

    Returns:
        Tuple of (working_dir, session_slug)
    """
    session_slug = "2026-01-01_legacy-session"
    session_dir = temp_project_dir / "agents" / "sessions" / session_slug
    session_dir.mkdir(parents=True)

    # Write state.json
    state_path = session_dir / "state.json"
    state_path.write_text(json.dumps(sample_state_v1, indent=2))

    # Create spec.md and plan.json
    (session_dir / "spec.md").write_text("# Legacy Spec\n")
    (session_dir / "plan.json").write_text("{}")

    return temp_project_dir, session_slug


@pytest.fixture
def temp_multiple_sessions(
    temp_project_dir: Path,
    sample_state_v2: dict[str, Any],
    sample_state_in_build: dict[str, Any],
) -> tuple[Path, list[str]]:
    """Create multiple session directories for batch sync testing.

    Returns:
        Tuple of (working_dir, list of session_slugs)
    """
    sessions = []

    # Session 1: spec phase
    slug1 = "2026-01-01_test-session"
    dir1 = temp_project_dir / "agents" / "sessions" / slug1
    dir1.mkdir(parents=True)
    (dir1 / "state.json").write_text(json.dumps(sample_state_v2, indent=2))
    (dir1 / "spec.md").write_text("# Spec 1\n")
    sessions.append(slug1)

    # Session 2: build phase
    slug2 = "2026-01-15_build-test"
    dir2 = temp_project_dir / "agents" / "sessions" / slug2
    dir2.mkdir(parents=True)
    (dir2 / "state.json").write_text(json.dumps(sample_state_in_build, indent=2))
    (dir2 / "spec.md").write_text("# Spec 2\n")
    (dir2 / "plan.json").write_text("{}")
    sessions.append(slug2)

    # Session 3: invalid (no state.json)
    slug3 = "2026-01-20_invalid-session"
    dir3 = temp_project_dir / "agents" / "sessions" / slug3
    dir3.mkdir(parents=True)
    (dir3 / "spec.md").write_text("# Spec 3\n")
    sessions.append(slug3)

    return temp_project_dir, sessions


@pytest.fixture
def sample_project_id() -> str:
    """Return a sample project UUID as string."""
    return str(uuid4())
