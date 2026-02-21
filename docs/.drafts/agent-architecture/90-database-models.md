# Database Models

Pydantic models for the session management system. These models track execution state and events while session artifacts (spec.md, plan.json) live in the codebase.

---

## Architecture: Hybrid Storage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CODEBASE (Files)                                  │
│                                                                             │
│   agents/sessions/{session_slug}/                                           │
│   ├── state.json     ← Session phase, status (quick reads)                  │
│   ├── spec.md        ← What we're building (agent writes)                   │
│   ├── plan.json      ← How we're building it (agent writes)                 │
│   └── research/      ← Research artifacts                                   │
│                                                                             │
│   SOURCE OF TRUTH for: Work artifacts that agents read/write                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ synced/referenced
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE (SQLite)                                  │
│                                                                             │
│   sessions              ← Workflow tracking, quick queries                   │
│   agents                ← Agent instances, SDK session IDs for resume       │
│   agent_logs            ← All hook events, observability                    │
│   interactive_messages  ← Block-level chat for spec/plan UI rendering       │
│                                                                             │
│   SOURCE OF TRUTH for: Execution events, timing, costs, agent state,       │
│                         interactive chat history                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Models

### Session

The top-level workflow container. Maps to a folder in `agents/sessions/`.

```python
"""
Session Model

Represents a spec → plan → build → docs workflow.
Each session has a corresponding folder: agents/sessions/{session_slug}/

The session tracks workflow state in the database while artifacts
(spec.md, plan.json) live in the filesystem for agent access.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATUS TYPES
# ═══════════════════════════════════════════════════════════════════════════════

SessionStatus = Literal[
    'created',      # Session created, no work started
    'spec',         # Spec phase in progress
    'spec_done',    # Spec complete, ready for plan
    'plan',         # Plan phase in progress
    'plan_done',    # Plan complete, ready for build
    'build',        # Build phase in progress
    'docs',         # Docs update phase in progress
    'complete',     # All phases complete
    'failed',       # Session failed with error
    'paused',       # Session paused by user
]


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Session(BaseModel):
    """
    Workflow container for spec → plan → build → docs lifecycle.

    Maps to: sessions table
    Filesystem: agents/sessions/{session_slug}/

    The session tracks:
    - Workflow status and phase progression
    - Aggregated token usage and costs
    - References to filesystem artifacts
    - Git worktree if using isolation

    Artifacts (spec.md, plan.json, state.json) are stored in the filesystem
    for direct agent access via grep/read tools.
    """

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(description="Unique session identifier (database PK)")
    session_slug: str = Field(
        description="Folder name in agents/sessions/ (e.g., '2026-01-15_auth-feature')"
    )
    title: Optional[str] = Field(
        default=None,
        description="Human-readable session title"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of what this session accomplishes"
    )

    # ─── Workflow State ─────────────────────────────────────────────────────────
    status: SessionStatus = Field(
        default='created',
        description="Current workflow phase"
    )
    session_type: Literal['full', 'quick', 'research'] = Field(
        default='full',
        description="Session type: full (spec→plan→build), quick (quick-plan→build), research (no code)"
    )

    # ─── Filesystem References ──────────────────────────────────────────────────
    working_dir: str = Field(
        description="Absolute path to project root"
    )
    session_dir: Optional[str] = Field(
        default=None,
        description="Absolute path to session folder (agents/sessions/{slug}/)"
    )
    git_worktree: Optional[str] = Field(
        default=None,
        description="Git worktree path if using worktree isolation"
    )
    git_branch: Optional[str] = Field(
        default=None,
        description="Git branch name for this session"
    )

    # ─── Artifact Status (synced from filesystem) ───────────────────────────────
    spec_exists: bool = Field(
        default=False,
        description="Whether spec.md exists in session folder"
    )
    plan_exists: bool = Field(
        default=False,
        description="Whether plan.json exists in session folder"
    )
    checkpoints_total: int = Field(
        default=0,
        description="Total checkpoints in plan"
    )
    checkpoints_completed: int = Field(
        default=0,
        description="Number of completed checkpoints"
    )

    # ─── Aggregated Stats ───────────────────────────────────────────────────────
    total_input_tokens: int = Field(
        default=0,
        description="Sum of input tokens across all agents"
    )
    total_output_tokens: int = Field(
        default=0,
        description="Sum of output tokens across all agents"
    )
    total_cost: float = Field(
        default=0.0,
        description="Sum of costs across all agents (USD)"
    )

    # ─── Error Tracking ─────────────────────────────────────────────────────────
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if session failed"
    )
    error_phase: Optional[str] = Field(
        default=None,
        description="Phase where error occurred"
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session configuration and context"
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(description="When session was created")
    updated_at: datetime = Field(description="Last update timestamp")
    started_at: Optional[datetime] = Field(
        default=None,
        description="When first phase started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When session completed"
    )

    # ─── Validators ─────────────────────────────────────────────────────────────

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert string or asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('total_cost', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
```

---

### Agent

Individual agent instances spawned during a session. Each agent has its own Claude SDK session for resumption.

```python
"""
Agent Model

Represents an individual agent invocation within a session.
Each agent type (spec, plan, build, research, docs) gets its own record.

The agent tracks:
- Claude SDK session ID for conversation resumption
- Execution status and timing
- Token usage and costs
- Configuration (model, system prompt)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT TYPE AND STATUS
# ═══════════════════════════════════════════════════════════════════════════════

AgentType = Literal[
    'spec',         # Spec interview agent
    'plan',         # Plan design agent
    'quick-plan',   # Quick plan agent (for simple tasks)
    'build',        # Build execution agent
    'research',     # Research/exploration agent
    'docs',         # Documentation update agent
    'debug',        # Debug investigation agent
]

AgentStatus = Literal[
    'pending',      # Created but not started
    'executing',    # Currently running
    'waiting',      # Waiting for user input
    'complete',     # Finished successfully
    'failed',       # Failed with error
    'interrupted',  # Interrupted by user
]


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Agent(BaseModel):
    """
    Individual agent invocation within a session.

    Maps to: agents table

    Each agent represents a single SDK invocation that can be:
    - Started fresh (new SDK session)
    - Resumed (using sdk_session_id)

    Multiple agents of the same type can exist in a session
    (e.g., multiple build agents for different checkpoints).
    """

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(description="Unique agent identifier (database PK)")
    session_id: UUID = Field(description="Parent session FK")

    # ─── Agent Type ─────────────────────────────────────────────────────────────
    agent_type: AgentType = Field(
        description="Type of agent (spec, plan, build, etc.)"
    )
    name: Optional[str] = Field(
        default=None,
        description="Optional friendly name (e.g., 'build-checkpoint-1')"
    )

    # ─── Claude SDK Session ─────────────────────────────────────────────────────
    sdk_session_id: Optional[str] = Field(
        default=None,
        description="Claude SDK session ID for resumption (from init message)"
    )

    # ─── Configuration ──────────────────────────────────────────────────────────
    model: str = Field(
        description="Claude model ID (e.g., 'claude-sonnet-4-5-20250929')"
    )
    model_alias: Optional[str] = Field(
        default=None,
        description="Model alias used (e.g., 'sonnet', 'opus', 'haiku')"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for this agent"
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="Working directory for agent (may differ from session)"
    )

    # ─── Execution Context ──────────────────────────────────────────────────────
    status: AgentStatus = Field(
        default='pending',
        description="Current execution status"
    )
    checkpoint_id: Optional[int] = Field(
        default=None,
        description="Checkpoint number (for build agents)"
    )
    task_group_id: Optional[str] = Field(
        default=None,
        description="Task group ID within checkpoint"
    )

    # ─── Token Usage & Costs ────────────────────────────────────────────────────
    input_tokens: int = Field(
        default=0,
        description="Total input tokens consumed"
    )
    output_tokens: int = Field(
        default=0,
        description="Total output tokens generated"
    )
    cost: float = Field(
        default=0.0,
        description="Total cost in USD"
    )

    # ─── Error Tracking ─────────────────────────────────────────────────────────
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if agent failed"
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    allowed_tools: Optional[list[str]] = Field(
        default=None,
        description="List of allowed tools for this agent"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent configuration"
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(description="When agent was created")
    updated_at: datetime = Field(description="Last update timestamp")
    started_at: Optional[datetime] = Field(
        default=None,
        description="When agent started executing"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When agent completed"
    )

    # ─── Validators ─────────────────────────────────────────────────────────────

    @field_validator('id', 'session_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert string or asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('cost', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator('allowed_tools', mode='before')
    @classmethod
    def parse_tools_list(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
```

---

### AgentLog

Event log for all hook events and response blocks. This is the observability layer.

```python
"""
AgentLog Model

Unified event log capturing all execution events from Claude SDK hooks
and response blocks. This is the primary observability mechanism.

Event Categories:
- hook: SDK hook events (PreToolUse, PostToolUse, Stop, etc.)
- response: Response blocks (TextBlock, ThinkingBlock, ToolUseBlock)
- phase: Session phase transitions (spec_start, plan_complete, etc.)
"""

# ═══════════════════════════════════════════════════════════════════════════════
# EVENT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

EventCategory = Literal[
    'hook',      # SDK hook events
    'response',  # Response blocks from Claude
    'phase',     # Session phase transitions
]

# Hook event types
HookEventType = Literal[
    'PreToolUse',
    'PostToolUse',
    'UserPromptSubmit',
    'Stop',
    'SubagentStart',
    'SubagentStop',
    'PreCompact',
]

# Response block types
ResponseEventType = Literal[
    'TextBlock',
    'ThinkingBlock',
    'ToolUseBlock',
    'ToolResultBlock',
]

# Phase event types
PhaseEventType = Literal[
    'session_created',
    'spec_started',
    'spec_completed',
    'plan_started',
    'plan_completed',
    'build_started',
    'checkpoint_started',
    'checkpoint_completed',
    'build_completed',
    'docs_started',
    'docs_completed',
    'session_completed',
    'session_failed',
]


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT_LOG MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class AgentLog(BaseModel):
    """
    Unified event log for execution observability.

    Maps to: agent_logs table

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

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(description="Unique log entry identifier")
    agent_id: UUID = Field(description="Agent that generated this event")
    session_id: UUID = Field(description="Session this event belongs to")

    # ─── SDK Context ────────────────────────────────────────────────────────────
    sdk_session_id: Optional[str] = Field(
        default=None,
        description="Claude SDK session ID for correlation"
    )

    # ─── Event Classification ───────────────────────────────────────────────────
    event_category: EventCategory = Field(
        description="Event category: hook, response, or phase"
    )
    event_type: str = Field(
        description="Specific event type (PreToolUse, TextBlock, spec_started, etc.)"
    )

    # ─── Event Content ──────────────────────────────────────────────────────────
    content: Optional[str] = Field(
        default=None,
        description="Text content (for TextBlock, ThinkingBlock)"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full event data (tool info, block details, etc.)"
    )
    summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of this event"
    )

    # ─── Tool-Specific Fields ───────────────────────────────────────────────────
    tool_name: Optional[str] = Field(
        default=None,
        description="Tool name (for PreToolUse, PostToolUse, ToolUseBlock)"
    )
    tool_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tool input parameters"
    )
    tool_output: Optional[str] = Field(
        default=None,
        description="Tool output/result (for PostToolUse, ToolResultBlock)"
    )

    # ─── Sequence Tracking ──────────────────────────────────────────────────────
    entry_index: Optional[int] = Field(
        default=None,
        description="Sequential index within agent execution"
    )

    # ─── Checkpoint Context ─────────────────────────────────────────────────────
    checkpoint_id: Optional[int] = Field(
        default=None,
        description="Checkpoint number (for build phase events)"
    )

    # ─── Timing ─────────────────────────────────────────────────────────────────
    timestamp: datetime = Field(description="When the event occurred")
    duration_ms: Optional[int] = Field(
        default=None,
        description="Duration in milliseconds (for tool calls)"
    )

    # ─── Validators ─────────────────────────────────────────────────────────────

    @field_validator('id', 'agent_id', 'session_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert string or asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('payload', 'tool_input', mode='before')
    @classmethod
    def parse_json(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
```

---

### InteractiveMessage

Block-level chat messages for interactive phases (spec, plan). Each row represents one block from the conversation — a user text submission, an agent text response, a tool use/result, or a thinking block. This table is the rendering source for the frontend chat panel.

**Relationship to AgentLog**: Content is double-stored. AgentLog captures all agent activity (including background agents) for observability. InteractiveMessage stores only the chat-visible blocks for the interactive conversation thread. Different query patterns, different rendering needs.

```python
"""
InteractiveMessage Model

Block-level chat storage for interactive session phases.
Each row is one block: TextBlock, ToolUseBlock, ToolResultBlock, etc.

Used by the frontend chat panel to render the conversation.
Ordered by (turn_index, block_index) for chronological display.
"""

class InteractiveMessage(SQLModel, table=True):
    """
    Block-level chat message for interactive phases.

    Maps to: interactive_messages table

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
    id: UUID = Field(primary_key=True, description="Unique message block identifier")
    session_id: UUID = Field(
        foreign_key="sessions.id",
        index=True,
        description="Parent session FK"
    )
    agent_id: Optional[UUID] = Field(
        default=None,
        foreign_key="agents.id",
        index=True,
        description="Agent that generated this block (null for user messages)"
    )

    # ─── Phase Context ──────────────────────────────────────────────────────────
    phase: str = Field(
        index=True,
        description="Workflow phase: spec or plan"
    )

    # ─── Message Classification ─────────────────────────────────────────────────
    role: str = Field(description="Message role: user, assistant, tool_use, or tool_result")
    block_type: str = Field(description="Block type: text, tool_use, tool_result, or thinking")

    # ─── Content ────────────────────────────────────────────────────────────────
    content: Optional[str] = Field(
        default=None,
        description="Text content or JSON for tool blocks"
    )
    tool_name: Optional[str] = Field(
        default=None,
        index=True,
        description="Tool name (for tool_use/tool_result blocks)"
    )

    # ─── Sequence Tracking ──────────────────────────────────────────────────────
    turn_index: int = Field(description="Turn number within the conversation (groups blocks)")
    block_index: int = Field(description="Block order within a turn")

    # ─── Timing ─────────────────────────────────────────────────────────────────
    timestamp: datetime = Field(index=True, description="When the block was created")

    # ─── Relationships ──────────────────────────────────────────────────────────
    session: Optional["Session"] = Relationship(...)
    agent: Optional["Agent"] = Relationship(...)
```

**DTOs:**

```python
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
```

---

### Supporting Models

Additional models for specific use cases.

```python
"""
Supporting Models

Additional models for specific queries and API responses.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION SUMMARY (for list views)
# ═══════════════════════════════════════════════════════════════════════════════


class SessionSummary(BaseModel):
    """
    Lightweight session info for list views.
    Excludes heavy fields like metadata.
    """
    id: UUID
    session_slug: str
    title: Optional[str]
    status: SessionStatus
    session_type: Literal['full', 'quick', 'research']
    checkpoints_completed: int
    checkpoints_total: int
    total_cost: float
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT SUMMARY (for session detail views)
# ═══════════════════════════════════════════════════════════════════════════════


class AgentSummary(BaseModel):
    """
    Lightweight agent info for session detail views.
    """
    id: UUID
    agent_type: AgentType
    name: Optional[str]
    model_alias: Optional[str]
    status: AgentStatus
    checkpoint_id: Optional[int]
    input_tokens: int
    output_tokens: int
    cost: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION WITH AGENTS (for full session view)
# ═══════════════════════════════════════════════════════════════════════════════


class SessionWithAgents(Session):
    """
    Session with nested agent summaries.
    Used for detailed session views.
    """
    agents: list[AgentSummary] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# CREATE/UPDATE DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class SessionCreate(BaseModel):
    """DTO for creating a new session"""
    session_slug: str
    title: Optional[str] = None
    description: Optional[str] = None
    session_type: Literal['full', 'quick', 'research'] = 'full'
    working_dir: str
    git_worktree: Optional[str] = None
    git_branch: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """DTO for updating session fields"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SessionStatus] = None
    spec_exists: Optional[bool] = None
    plan_exists: Optional[bool] = None
    checkpoints_total: Optional[int] = None
    checkpoints_completed: Optional[int] = None
    error_message: Optional[str] = None
    error_phase: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentCreate(BaseModel):
    """DTO for creating a new agent"""
    session_id: UUID
    agent_type: AgentType
    name: Optional[str] = None
    model: str
    model_alias: Optional[str] = None
    system_prompt: Optional[str] = None
    working_dir: Optional[str] = None
    checkpoint_id: Optional[int] = None
    task_group_id: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('session_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return v
        return UUID(str(v))


class AgentUpdate(BaseModel):
    """DTO for updating agent fields"""
    sdk_session_id: Optional[str] = None
    status: Optional[AgentStatus] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentLogCreate(BaseModel):
    """DTO for creating a new log entry"""
    agent_id: UUID
    session_id: UUID
    sdk_session_id: Optional[str] = None
    event_category: EventCategory
    event_type: str
    content: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    entry_index: Optional[int] = None
    checkpoint_id: Optional[int] = None
    duration_ms: Optional[int] = None

    @field_validator('agent_id', 'session_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return v
        return UUID(str(v))
```

---

## Exports

```python
# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Type aliases
    "SessionStatus",
    "AgentType",
    "AgentStatus",
    "EventCategory",
    "HookEventType",
    "ResponseEventType",
    "PhaseEventType",

    # Core models
    "Session",
    "Agent",
    "AgentLog",
    "InteractiveMessage",

    # Summary models
    "SessionSummary",
    "AgentSummary",
    "SessionWithAgents",

    # DTOs
    "SessionCreate",
    "SessionUpdate",
    "AgentCreate",
    "AgentUpdate",
    "AgentLogCreate",
    "InteractiveMessageCreate",
    "InteractiveMessageSummary",
]
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              sessions                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ id (UUID) PK                                                           │ │
│  │ session_slug (TEXT) UNIQUE                                             │ │
│  │ status (TEXT) → created|spec|plan|build|docs|complete|failed|paused    │ │
│  │ session_type (TEXT) → full|quick|research                              │ │
│  │ working_dir (TEXT)                                                     │ │
│  │ ...                                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                agents                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ id (UUID) PK                                                           │ │
│  │ session_id (UUID) FK → sessions.id                                     │ │
│  │ agent_type (TEXT) → spec|plan|quick-plan|build|research|docs|debug     │ │
│  │ sdk_session_id (TEXT) ← For Claude SDK resume                          │ │
│  │ status (TEXT) → pending|executing|waiting|complete|failed|interrupted  │ │
│  │ model (TEXT)                                                           │ │
│  │ checkpoint_id (INT) ← For build agents                                 │ │
│  │ ...                                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              agent_logs                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ id (UUID) PK                                                           │ │
│  │ agent_id (UUID) FK → agents.id                                         │ │
│  │ session_id (UUID) FK → sessions.id (denormalized for quick queries)    │ │
│  │ event_category (TEXT) → hook|response|phase                            │ │
│  │ event_type (TEXT) → PreToolUse|PostToolUse|TextBlock|...               │ │
│  │ tool_name (TEXT)                                                       │ │
│  │ payload (JSONB)                                                        │ │
│  │ timestamp (TIMESTAMPTZ)                                                │ │
│  │ ...                                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    │ 1:N (via session_id)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         interactive_messages                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ id (UUID) PK                                                           │ │
│  │ session_id (UUID) FK → sessions.id                                     │ │
│  │ agent_id (UUID) FK → agents.id (nullable)                              │ │
│  │ phase (TEXT) → spec | plan                                             │ │
│  │ role (TEXT) → user | assistant | tool_use | tool_result                 │ │
│  │ block_type (TEXT) → text | tool_use | tool_result | thinking           │ │
│  │ content (TEXT)                                                         │ │
│  │ tool_name (TEXT)                                                       │ │
│  │ turn_index (INT)                                                       │ │
│  │ block_index (INT)                                                      │ │
│  │ timestamp (TIMESTAMPTZ)                                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SQL Schema (SQLite)

```sql
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,  -- UUID as TEXT for SQLite
    session_slug TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'created'
        CHECK (status IN ('created', 'spec', 'spec_done', 'plan', 'plan_done',
                          'build', 'docs', 'complete', 'failed', 'paused')),
    session_type TEXT NOT NULL DEFAULT 'full'
        CHECK (session_type IN ('full', 'quick', 'research')),
    working_dir TEXT NOT NULL,
    session_dir TEXT,
    git_worktree TEXT,
    git_branch TEXT,
    spec_exists INTEGER DEFAULT 0,  -- BOOLEAN as INTEGER for SQLite
    plan_exists INTEGER DEFAULT 0,
    checkpoints_total INTEGER DEFAULT 0,
    checkpoints_completed INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    error_message TEXT,
    error_phase TEXT,
    metadata TEXT DEFAULT '{}',  -- JSON as TEXT for SQLite
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL
        CHECK (agent_type IN ('spec', 'plan', 'quick-plan', 'build', 'research', 'docs', 'debug')),
    name TEXT,
    sdk_session_id TEXT,
    model TEXT NOT NULL,
    model_alias TEXT,
    system_prompt TEXT,
    working_dir TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'executing', 'waiting', 'complete', 'failed', 'interrupted')),
    checkpoint_id INTEGER,
    task_group_id TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    error_message TEXT,
    allowed_tools TEXT,  -- JSON array as TEXT
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Agent logs table
CREATE TABLE IF NOT EXISTS agent_logs (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    sdk_session_id TEXT,
    event_category TEXT NOT NULL CHECK (event_category IN ('hook', 'response', 'phase')),
    event_type TEXT NOT NULL,
    content TEXT,
    payload TEXT DEFAULT '{}',
    summary TEXT,
    tool_name TEXT,
    tool_input TEXT,
    tool_output TEXT,
    entry_index INTEGER,
    checkpoint_id INTEGER,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    duration_ms INTEGER
);

-- Interactive messages table (chat UI rendering for spec/plan phases)
CREATE TABLE IF NOT EXISTS interactive_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
    phase TEXT NOT NULL CHECK (phase IN ('spec', 'plan')),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool_use', 'tool_result')),
    block_type TEXT NOT NULL CHECK (block_type IN ('text', 'tool_use', 'tool_result', 'thinking')),
    content TEXT,
    tool_name TEXT,
    turn_index INTEGER NOT NULL,
    block_index INTEGER NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agents_session ON agents(session_id);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_logs_agent ON agent_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_logs_session ON agent_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON agent_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_category_type ON agent_logs(event_category, event_type);
CREATE INDEX IF NOT EXISTS idx_messages_session ON interactive_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_agent ON interactive_messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_messages_phase ON interactive_messages(phase);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON interactive_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_tool ON interactive_messages(tool_name);
```

---

## Open Questions

- [ ] Do we need a separate `checkpoints` table or track in plan.json + session?
- [ ] Should `agent_logs.session_id` be denormalized or join through agents?
- [ ] How to handle research sessions that may not have spec/plan?
- [ ] Do we need `prompts` table like orchestrator_db for tracking user inputs?

---

*Draft - iterate as implementation progresses*
