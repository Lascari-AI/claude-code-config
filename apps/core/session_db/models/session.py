"""
Session models - Database schema and DTOs for workflow sessions.

A Session represents a spec -> plan -> build -> docs workflow lifecycle.
Session artifacts (spec.md, plan.json) live in the filesystem while
the database tracks execution state, timing, costs, and events.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .agent import Agent
    from .agent_log import AgentLog
    from .project import Project


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

SessionStatus = Literal[
    "created",  # Session created, no work started
    "spec",  # Spec phase in progress
    "spec_done",  # Spec complete, ready for plan
    "plan",  # Plan phase in progress
    "plan_done",  # Plan complete, ready for build
    "build",  # Build phase in progress
    "docs",  # Docs update phase in progress
    "complete",  # All phases complete
    "failed",  # Session failed with error
    "paused",  # Session paused by user
]

SessionType = Literal[
    "full",  # Full workflow: spec -> plan -> build -> docs
    "quick",  # Quick workflow: quick-plan -> build -> docs
    "research",  # Research only: no code changes
]


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Session(SQLModel, table=True):
    """
    Workflow container for spec -> plan -> build -> docs lifecycle.

    Each session has a corresponding folder: agents/sessions/{session_slug}/

    The session tracks workflow state in the database while artifacts
    (spec.md, plan.json) live in the filesystem for agent access.
    """

    __tablename__ = "sessions"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique session identifier",
    )
    session_slug: str = Field(
        unique=True,
        index=True,
        description="Folder name in agents/sessions/ (e.g., '2026-01-15_auth-feature')",
    )
    title: Optional[str] = Field(
        default=None,
        description="Human-readable session title",
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Brief description of what this session accomplishes",
    )

    # ─── Project Link ────────────────────────────────────────────────────────────
    project_id: Optional[UUID] = Field(
        default=None,
        foreign_key="projects.id",
        index=True,
        description="Optional parent project FK",
    )

    # ─── Workflow State ─────────────────────────────────────────────────────────
    status: str = Field(
        default="active",
        index=True,
        description="Session execution status: active, paused, complete, failed",
    )
    current_phase: str = Field(
        default="spec",
        index=True,
        description="Current workflow phase: spec, plan, build, docs, complete",
    )
    session_type: str = Field(
        default="full",
        description="Session type: full, quick, or research",
    )

    # ─── Phase History (v2: timestamps for phase transitions) ──────────────────
    phase_history: dict[str, Any] = Field(
        default_factory=lambda: {
            "spec_started_at": None,
            "spec_completed_at": None,
            "plan_started_at": None,
            "plan_completed_at": None,
            "build_started_at": None,
            "build_completed_at": None,
            "docs_started_at": None,
            "docs_completed_at": None,
        },
        sa_column=Column(JSON),
        description="Timestamps for each phase transition",
    )

    # ─── Filesystem References ──────────────────────────────────────────────────
    working_dir: str = Field(
        description="Absolute path to project root",
    )
    session_dir: Optional[str] = Field(
        default=None,
        description="Absolute path to session folder",
    )
    git_worktree: Optional[str] = Field(
        default=None,
        description="Git worktree path if using isolation",
    )
    git_branch: Optional[str] = Field(
        default=None,
        description="Git branch name for this session",
    )
    git_base_branch: Optional[str] = Field(
        default=None,
        description="Base branch for PR (e.g., main)",
    )

    # ─── Artifact Status ────────────────────────────────────────────────────────
    spec_exists: bool = Field(
        default=False,
        description="Whether spec.md exists in session folder",
    )
    plan_exists: bool = Field(
        default=False,
        description="Whether plan.json exists in session folder",
    )
    checkpoints_total: int = Field(
        default=0,
        description="Total checkpoints in plan",
    )
    checkpoints_completed: int = Field(
        default=0,
        description="Number of completed checkpoints (count for UI display)",
    )
    checkpoints_completed_list: list[int] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of completed checkpoint IDs (v2: matches state.json build_progress)",
    )
    current_checkpoint: Optional[int] = Field(
        default=None,
        description="Currently active checkpoint ID",
    )

    # ─── Aggregated Stats ───────────────────────────────────────────────────────
    total_input_tokens: int = Field(
        default=0,
        description="Sum of input tokens across all agents",
    )
    total_output_tokens: int = Field(
        default=0,
        description="Sum of output tokens across all agents",
    )
    total_cost: float = Field(
        default=0.0,
        description="Sum of costs across all agents (USD)",
    )

    # ─── Error Tracking ─────────────────────────────────────────────────────────
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message if session failed",
    )
    error_phase: Optional[str] = Field(
        default=None,
        description="Phase where error occurred",
    )

    # ─── Commits (v2: tracked for session portability) ───────────────────────────
    commits_list: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Git commits made during session [{sha, message, checkpoint, created_at}]",
    )

    # ─── Artifacts (v2: paths to session artifacts) ─────────────────────────────
    artifacts: dict[str, str] = Field(
        default_factory=lambda: {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
        sa_column=Column(JSON),
        description="Paths to session artifacts relative to session directory",
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
        description="Additional session configuration",
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When session was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When first phase started",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When session completed",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    project: Optional["Project"] = Relationship(back_populates="sessions")
    agents: list["Agent"] = Relationship(back_populates="session")
    logs: list["AgentLog"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"foreign_keys": "[AgentLog.session_id]"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class SessionSummary(SQLModel):
    """Lightweight session info for list views."""

    id: UUID
    session_slug: str
    title: Optional[str]
    status: str
    current_phase: str
    session_type: str
    project_id: Optional[UUID] = None
    checkpoints_completed: int
    checkpoints_total: int
    current_checkpoint: Optional[int] = None
    total_cost: float
    created_at: datetime
    updated_at: datetime


class SessionCreate(SQLModel):
    """DTO for creating a new session."""

    session_slug: str
    title: Optional[str] = None
    description: Optional[str] = None
    session_type: str = "full"
    working_dir: str
    session_dir: Optional[str] = None
    project_id: Optional[UUID] = None
    # Git context (v2)
    git_worktree: Optional[str] = None
    git_branch: Optional[str] = None
    git_base_branch: Optional[str] = None
    # Phase tracking (v2)
    current_phase: str = "spec"
    status: str = "active"
    phase_history: dict[str, Any] = Field(default_factory=dict)
    # Build progress (v2)
    checkpoints_total: int = 0
    checkpoints_completed_list: list[int] = Field(default_factory=list)
    current_checkpoint: Optional[int] = None
    # Commits and artifacts (v2)
    commits_list: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(
        default_factory=lambda: {"spec": "spec.md", "plan": "plan.json", "plan_readable": "plan.md"}
    )
    metadata_: dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(SQLModel):
    """DTO for updating session fields."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    project_id: Optional[UUID] = None
    # Git context (v2)
    git_branch: Optional[str] = None
    git_worktree: Optional[str] = None
    git_base_branch: Optional[str] = None
    # Artifact status
    spec_exists: Optional[bool] = None
    plan_exists: Optional[bool] = None
    # Build progress (v2)
    checkpoints_total: Optional[int] = None
    checkpoints_completed: Optional[int] = None
    checkpoints_completed_list: Optional[list[int]] = None
    current_checkpoint: Optional[int] = None
    # Phase history (v2)
    phase_history: Optional[dict[str, Any]] = None
    # Commits and artifacts (v2)
    commits_list: Optional[list[dict[str, Any]]] = None
    artifacts: Optional[dict[str, str]] = None
    # Error tracking
    error_message: Optional[str] = None
    error_phase: Optional[str] = None
    # Stats
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_: Optional[dict[str, Any]] = None
