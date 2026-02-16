"""Pydantic models for state.json v2 schema."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Phase(str, Enum):
    """Valid session phases for workflow progression.

    Phases progress in order: spec → plan → build → docs → complete
    """

    spec = "spec"
    plan = "plan"
    build = "build"
    docs = "docs"
    complete = "complete"


class Status(str, Enum):
    """Session execution status."""

    active = "active"
    paused = "paused"
    complete = "complete"
    failed = "failed"


class SessionType(str, Enum):
    """Type of session workflow.

    - full: Complete spec → plan → build → docs workflow
    - quick: Simplified workflow for small tasks
    - research: Exploration/investigation without implementation
    """

    full = "full"
    quick = "quick"
    research = "research"


# ─── Nested Models ────────────────────────────────────────────────────────────


class PhaseHistory(BaseModel):
    """Timestamps for phase transitions.

    Each phase has started_at and completed_at timestamps.
    All fields optional - populated as transitions occur.
    """

    spec_started_at: Optional[datetime] = None
    spec_completed_at: Optional[datetime] = None
    plan_started_at: Optional[datetime] = None
    plan_completed_at: Optional[datetime] = None
    build_started_at: Optional[datetime] = None
    build_completed_at: Optional[datetime] = None
    docs_started_at: Optional[datetime] = None
    docs_completed_at: Optional[datetime] = None


class BuildProgress(BaseModel):
    """Checkpoint progress during build phase.

    Tracks total checkpoints, which are completed, and current active.
    """

    checkpoints_total: Optional[int] = None
    checkpoints_completed: list[int] = Field(default_factory=list)
    current_checkpoint: Optional[int] = None


class GitContext(BaseModel):
    """Git branch and worktree context for the session."""

    branch: Optional[str] = None
    worktree: Optional[str] = None
    base_branch: Optional[str] = None


class Commit(BaseModel):
    """Git commit made during session."""

    sha: str
    message: str
    checkpoint: Optional[int] = None
    created_at: datetime


class Artifacts(BaseModel):
    """Paths to session artifacts (relative to session directory)."""

    spec: str = "spec.md"
    plan: str = "plan.json"
    plan_readable: str = "plan.md"


# ─── Root Model ───────────────────────────────────────────────────────────────


class SessionState(BaseModel):
    """Root model for state.json v2 schema.

    This is the complete session manifest - source of truth for session tracking.
    Updated programmatically via StateManager, never edited directly.
    """

    # ─── Identity ─────────────────────────────────────────────────────────────
    session_id: str
    topic: str
    description: Optional[str] = None
    session_type: SessionType = SessionType.full

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at: datetime
    updated_at: datetime

    # ─── Current State ────────────────────────────────────────────────────────
    current_phase: Phase = Phase.spec
    status: Status = Status.active

    # ─── Phase History ────────────────────────────────────────────────────────
    phase_history: PhaseHistory = Field(default_factory=PhaseHistory)

    # ─── Build Progress ───────────────────────────────────────────────────────
    build_progress: BuildProgress = Field(default_factory=BuildProgress)

    # ─── Git Context ──────────────────────────────────────────────────────────
    git: GitContext = Field(default_factory=GitContext)

    # ─── Commits ──────────────────────────────────────────────────────────────
    commits: list[Commit] = Field(default_factory=list)

    # ─── Artifacts ────────────────────────────────────────────────────────────
    artifacts: Artifacts = Field(default_factory=Artifacts)

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
