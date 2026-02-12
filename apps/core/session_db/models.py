"""
SQLModel Database Models for Session Management

These models define the database schema for tracking:
- Sessions: Workflow containers (spec -> plan -> build -> docs)
- Agents: Individual agent invocations with Claude SDK session tracking
- AgentLogs: Execution events for observability

Architecture:
- Session artifacts (spec.md, plan.json) live in the filesystem
- Database tracks execution state, timing, costs, and events
- Agents store sdk_session_id for Claude conversation resumption
"""

from datetime import datetime
from typing import Any, Optional, Literal
from uuid import UUID, uuid4
import json

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON, Text


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

AgentType = Literal[
    "spec",  # Spec interview agent
    "plan",  # Plan design agent
    "quick-plan",  # Quick plan agent (for simple tasks)
    "build",  # Build execution agent
    "research",  # Research/exploration agent
    "docs",  # Documentation update agent
    "debug",  # Debug investigation agent
]

AgentStatus = Literal[
    "pending",  # Created but not started
    "executing",  # Currently running
    "waiting",  # Waiting for user input
    "complete",  # Finished successfully
    "failed",  # Failed with error
    "interrupted",  # Interrupted by user
]

EventCategory = Literal[
    "hook",  # SDK hook events (PreToolUse, PostToolUse, etc.)
    "response",  # Response blocks (TextBlock, ThinkingBlock, etc.)
    "phase",  # Session phase transitions
]

ProjectStatus = Literal[
    "pending",  # Registered but not yet set up
    "onboarding",  # Setup in progress
    "active",  # Fully managed, sessions can be created
    "paused",  # Temporarily inactive
    "archived",  # No longer managed
]


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Project(SQLModel, table=True):
    """
    A codebase that has been onboarded into the managed system.

    Each project represents a repository/codebase that can have sessions.
    Projects track onboarding status and configuration for agent management.
    """

    __tablename__ = "projects"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique project identifier",
    )
    name: str = Field(
        description="Human-friendly project name",
    )
    slug: str = Field(
        unique=True,
        index=True,
        description="URL-safe identifier for the project",
    )

    # ─── Location ───────────────────────────────────────────────────────────────
    path: str = Field(
        description="Absolute path to codebase root",
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="GitHub/GitLab URL if applicable",
    )

    # ─── Status ─────────────────────────────────────────────────────────────────
    status: str = Field(
        default="pending",
        index=True,
        description="Project lifecycle status",
    )
    onboarding_status: dict[str, Any] = Field(
        default_factory=lambda: {
            "path_validated": False,
            "claude_dir_exists": False,
            "settings_configured": False,
            "skills_linked": False,
            "agents_linked": False,
            "docs_foundation": False,
        },
        sa_column=Column(JSON),
        description="Track onboarding steps completed",
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
        description="Additional project configuration",
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When project was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    sessions: list["Session"] = Relationship(back_populates="project")


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
        default="created",
        index=True,
        description="Current workflow phase",
    )
    session_type: str = Field(
        default="full",
        description="Session type: full, quick, or research",
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
        description="Number of completed checkpoints",
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
# AGENT MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Agent(SQLModel, table=True):
    """
    Individual agent invocation within a session.

    Each agent represents a single SDK invocation that can be:
    - Started fresh (new SDK session)
    - Resumed (using sdk_session_id)

    Multiple agents of the same type can exist in a session
    (e.g., multiple build agents for different checkpoints).
    """

    __tablename__ = "agents"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique agent identifier",
    )
    session_id: UUID = Field(
        foreign_key="sessions.id",
        index=True,
        description="Parent session FK",
    )

    # ─── Agent Type ─────────────────────────────────────────────────────────────
    agent_type: str = Field(
        index=True,
        description="Type of agent: spec, plan, build, etc.",
    )
    name: Optional[str] = Field(
        default=None,
        description="Optional friendly name (e.g., 'build-checkpoint-1')",
    )

    # ─── Claude SDK Session ─────────────────────────────────────────────────────
    sdk_session_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Claude SDK session ID for resumption",
    )

    # ─── Configuration ──────────────────────────────────────────────────────────
    model: str = Field(
        description="Claude model ID (e.g., 'claude-sonnet-4-5-20250929')",
    )
    model_alias: Optional[str] = Field(
        default=None,
        description="Model alias used (e.g., 'sonnet', 'opus', 'haiku')",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Custom system prompt for this agent",
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="Working directory for agent",
    )

    # ─── Execution Context ──────────────────────────────────────────────────────
    status: str = Field(
        default="pending",
        index=True,
        description="Current execution status",
    )
    checkpoint_id: Optional[int] = Field(
        default=None,
        description="Checkpoint number (for build agents)",
    )
    task_group_id: Optional[str] = Field(
        default=None,
        description="Task group ID within checkpoint",
    )

    # ─── Token Usage & Costs ────────────────────────────────────────────────────
    input_tokens: int = Field(
        default=0,
        description="Total input tokens consumed",
    )
    output_tokens: int = Field(
        default=0,
        description="Total output tokens generated",
    )
    cost: float = Field(
        default=0.0,
        description="Total cost in USD",
    )

    # ─── Error Tracking ─────────────────────────────────────────────────────────
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message if agent failed",
    )

    # ─── Tools Configuration ────────────────────────────────────────────────────
    allowed_tools: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="JSON array of allowed tools",
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
        description="Additional agent configuration",
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When agent was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When agent started executing",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When agent completed",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    session: Optional[Session] = Relationship(back_populates="agents")
    logs: list["AgentLog"] = Relationship(back_populates="agent")

    # ─── Helper Methods ─────────────────────────────────────────────────────────
    def get_allowed_tools(self) -> list[str]:
        """Parse allowed_tools JSON string to list."""
        if self.allowed_tools:
            return json.loads(self.allowed_tools)
        return []

    def set_allowed_tools(self, tools: list[str]) -> None:
        """Set allowed_tools from list."""
        self.allowed_tools = json.dumps(tools)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT LOG MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class AgentLog(SQLModel, table=True):
    """
    Unified event log for execution observability.

    Captures:
    - SDK hook events (tool calls, agent lifecycle)
    - Response blocks (text, thinking, tool use)
    - Phase transitions (for workflow tracking)

    Used by UI to show:
    - Real-time execution progress
    - Tool call timeline
    - Cost tracking
    - Debugging/replay
    """

    __tablename__ = "agent_logs"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique log entry identifier",
    )
    agent_id: UUID = Field(
        foreign_key="agents.id",
        index=True,
        description="Agent that generated this event",
    )
    session_id: UUID = Field(
        foreign_key="sessions.id",
        index=True,
        description="Session this event belongs to (denormalized)",
    )

    # ─── SDK Context ────────────────────────────────────────────────────────────
    sdk_session_id: Optional[str] = Field(
        default=None,
        description="Claude SDK session ID for correlation",
    )

    # ─── Event Classification ───────────────────────────────────────────────────
    event_category: str = Field(
        index=True,
        description="Event category: hook, response, or phase",
    )
    event_type: str = Field(
        index=True,
        description="Specific event type",
    )

    # ─── Event Content ──────────────────────────────────────────────────────────
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Text content (for TextBlock, ThinkingBlock)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Full event data (tool info, block details, etc.)",
    )
    summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="AI-generated summary of this event",
    )

    # ─── Tool-Specific Fields ───────────────────────────────────────────────────
    tool_name: Optional[str] = Field(
        default=None,
        index=True,
        description="Tool name (for tool-related events)",
    )
    tool_input: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Tool input parameters as JSON",
    )
    tool_output: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Tool output/result",
    )

    # ─── Sequence Tracking ──────────────────────────────────────────────────────
    entry_index: Optional[int] = Field(
        default=None,
        description="Sequential index within agent execution",
    )

    # ─── Checkpoint Context ─────────────────────────────────────────────────────
    checkpoint_id: Optional[int] = Field(
        default=None,
        description="Checkpoint number (for build phase events)",
    )

    # ─── Timing ─────────────────────────────────────────────────────────────────
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="When the event occurred",
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Duration in milliseconds (for tool calls)",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    agent: Optional[Agent] = Relationship(back_populates="logs")
    session: Optional[Session] = Relationship(
        back_populates="logs",
        sa_relationship_kwargs={"foreign_keys": "[AgentLog.session_id]"},
    )

    # ─── Helper Methods ─────────────────────────────────────────────────────────
    def get_tool_input(self) -> dict[str, Any] | None:
        """Parse tool_input JSON string to dict."""
        if self.tool_input:
            return json.loads(self.tool_input)
        return None

    def set_tool_input(self, input_data: dict[str, Any]) -> None:
        """Set tool_input from dict."""
        self.tool_input = json.dumps(input_data)


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY MODELS (Read-only views)
# ═══════════════════════════════════════════════════════════════════════════════


class SessionSummary(SQLModel):
    """Lightweight session info for list views."""

    id: UUID
    session_slug: str
    title: Optional[str]
    status: str
    session_type: str
    project_id: Optional[UUID] = None
    checkpoints_completed: int
    checkpoints_total: int
    total_cost: float
    created_at: datetime
    updated_at: datetime


class ProjectSummary(SQLModel):
    """Lightweight project info for list views."""

    id: UUID
    name: str
    slug: str
    status: str
    path: str
    created_at: datetime
    updated_at: datetime


class AgentSummary(SQLModel):
    """Lightweight agent info for session detail views."""

    id: UUID
    agent_type: str
    name: Optional[str]
    model_alias: Optional[str]
    status: str
    checkpoint_id: Optional[int]
    input_tokens: int
    output_tokens: int
    cost: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# ═══════════════════════════════════════════════════════════════════════════════
# CREATE/UPDATE DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class SessionCreate(SQLModel):
    """DTO for creating a new session."""

    session_slug: str
    title: Optional[str] = None
    description: Optional[str] = None
    session_type: str = "full"
    working_dir: str
    project_id: Optional[UUID] = None
    git_worktree: Optional[str] = None
    git_branch: Optional[str] = None
    metadata_: dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(SQLModel):
    """DTO for updating session fields."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[UUID] = None
    spec_exists: Optional[bool] = None
    plan_exists: Optional[bool] = None
    checkpoints_total: Optional[int] = None
    checkpoints_completed: Optional[int] = None
    error_message: Optional[str] = None
    error_phase: Optional[str] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_: Optional[dict[str, Any]] = None


class ProjectCreate(SQLModel):
    """DTO for creating a new project."""

    name: str
    slug: str
    path: str
    repo_url: Optional[str] = None
    status: str = "pending"
    onboarding_status: dict[str, Any] = Field(default_factory=dict)
    metadata_: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(SQLModel):
    """DTO for updating project fields."""

    name: Optional[str] = None
    slug: Optional[str] = None
    path: Optional[str] = None
    repo_url: Optional[str] = None
    status: Optional[str] = None
    onboarding_status: Optional[dict[str, Any]] = None
    metadata_: Optional[dict[str, Any]] = None


class AgentCreate(SQLModel):
    """DTO for creating a new agent."""

    session_id: UUID
    agent_type: str
    name: Optional[str] = None
    model: str
    model_alias: Optional[str] = None
    system_prompt: Optional[str] = None
    working_dir: Optional[str] = None
    checkpoint_id: Optional[int] = None
    task_group_id: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    metadata_: dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(SQLModel):
    """DTO for updating agent fields."""

    sdk_session_id: Optional[str] = None
    status: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_: Optional[dict[str, Any]] = None


class AgentLogSummary(SQLModel):
    """Lightweight log entry for timeline views."""

    id: UUID
    agent_id: UUID
    session_id: UUID
    event_category: str
    event_type: str
    tool_name: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    timestamp: datetime
    duration_ms: Optional[int]


class AgentLogCreate(SQLModel):
    """DTO for creating a new log entry."""

    agent_id: UUID
    session_id: UUID
    sdk_session_id: Optional[str] = None
    event_category: str
    event_type: str
    content: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    tool_output: Optional[str] = None
    entry_index: Optional[int] = None
    checkpoint_id: Optional[int] = None
    duration_ms: Optional[int] = None
