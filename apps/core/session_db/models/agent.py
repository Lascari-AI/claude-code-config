"""
Agent models - Database schema and DTOs for agent invocations.

An Agent represents a single Claude SDK invocation within a session.
Agents can be started fresh or resumed using sdk_session_id.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .agent_log import AgentLog
    from .session import Session


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

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
    session: Optional["Session"] = Relationship(back_populates="agents")
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
# DTOs
# ═══════════════════════════════════════════════════════════════════════════════


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
