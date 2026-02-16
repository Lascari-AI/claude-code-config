"""
AgentLog models - Database schema and DTOs for execution events.

AgentLog captures SDK hook events, response blocks, and phase transitions
for execution observability and debugging/replay.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .agent import Agent
    from .session import Session


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

EventCategory = Literal[
    "hook",  # SDK hook events (PreToolUse, PostToolUse, etc.)
    "response",  # Response blocks (TextBlock, ThinkingBlock, etc.)
    "phase",  # Session phase transitions
]


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
    agent: Optional["Agent"] = Relationship(back_populates="logs")
    session: Optional["Session"] = Relationship(
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
# DTOs
# ═══════════════════════════════════════════════════════════════════════════════


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
