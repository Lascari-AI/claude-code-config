"""
InteractiveMessage models - Database schema and DTOs for chat block storage.

InteractiveMessage captures individual blocks from interactive phases (spec, plan)
for rendering the chat conversation panel. Each row is one block (TextBlock,
ToolUseBlock, etc.) from either the user or the agent.

Double-stored alongside AgentLog — AgentLog serves execution observability,
InteractiveMessage serves chat UI rendering. Different query patterns.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .agent import Agent
    from .session import Session


# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE MESSAGE MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class InteractiveMessage(SQLModel, table=True):
    """
    Block-level chat message for interactive phases.

    Each row represents one block from the conversation:
    - User text submissions (role='user', block_type='text')
    - Agent text responses (role='assistant', block_type='text')
    - Tool use blocks (role='tool_use', block_type='tool_use')
    - Tool result blocks (role='tool_result', block_type='tool_result')
    - Thinking blocks (role='assistant', block_type='thinking')

    Ordered by (turn_index, block_index) for chronological rendering.
    """

    __tablename__ = "interactive_messages"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique message block identifier",
    )
    session_id: UUID = Field(
        foreign_key="sessions.id",
        index=True,
        description="Parent session FK",
    )
    agent_id: Optional[UUID] = Field(
        default=None,
        foreign_key="agents.id",
        index=True,
        description="Agent that generated this block (null for user messages)",
    )

    # ─── Phase Context ──────────────────────────────────────────────────────────
    phase: str = Field(
        index=True,
        description="Workflow phase: spec or plan",
    )

    # ─── Message Classification ─────────────────────────────────────────────────
    role: str = Field(
        description="Message role: user, assistant, tool_use, or tool_result",
    )
    block_type: str = Field(
        description="Block type: text, tool_use, tool_result, or thinking",
    )

    # ─── Content ────────────────────────────────────────────────────────────────
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Text content or JSON for tool blocks",
    )
    tool_name: Optional[str] = Field(
        default=None,
        index=True,
        description="Tool name (for tool_use/tool_result blocks)",
    )

    # ─── Sequence Tracking ──────────────────────────────────────────────────────
    turn_index: int = Field(
        description="Turn number within the conversation (groups blocks)",
    )
    block_index: int = Field(
        description="Block order within a turn",
    )

    # ─── Timing ─────────────────────────────────────────────────────────────────
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="When the block was created",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    session: Optional["Session"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[InteractiveMessage.session_id]"},
    )
    agent: Optional["Agent"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[InteractiveMessage.agent_id]"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class InteractiveMessageCreate(SQLModel):
    """DTO for creating a new interactive message block."""

    session_id: UUID
    agent_id: Optional[UUID] = None
    phase: str
    role: str
    block_type: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    turn_index: int
    block_index: int


class InteractiveMessageSummary(SQLModel):
    """Lightweight message block for chat panel rendering."""

    id: UUID
    session_id: UUID
    role: str
    block_type: str
    content: Optional[str]
    tool_name: Optional[str]
    turn_index: int
    block_index: int
    timestamp: datetime
