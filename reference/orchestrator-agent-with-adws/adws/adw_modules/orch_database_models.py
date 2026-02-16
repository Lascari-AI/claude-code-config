"""
Pydantic Database Models for Multi-Agent Orchestration

These models map directly to the PostgreSQL tables defined in schema_orchestrator.sql.
They provide:
- Automatic UUID handling (converts asyncpg UUID objects to Python UUID)
- Type safety and validation
- Automatic JSON serialization/deserialization
- Field validation and defaults

Usage:
    from models import Agent, OrchestratorAgent, Prompt, AgentLog, SystemLog

    # Automatically handles UUID conversion from database
    agent = Agent(**row_dict)
    print(agent.id)  # Works with both UUID objects and strings
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR_AGENT MODEL
# ═══════════════════════════════════════════════════════════


class OrchestratorAgent(BaseModel):
    """
    Singleton orchestrator agent that manages other agents.

    Maps to: orchestrator_agents table
    """
    id: UUID
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[Literal['idle', 'executing', 'waiting', 'blocked', 'complete']] = None
    working_dir: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    archived: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
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
        """Parse JSON string metadata to dict"""
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


# ═══════════════════════════════════════════════════════════
# AGENT MODEL
# ═══════════════════════════════════════════════════════════


class Agent(BaseModel):
    """
    Agent registry and configuration for managed agents.

    Maps to: agents table
    """
    id: UUID
    orchestrator_agent_id: UUID
    name: str
    model: str
    system_prompt: Optional[str] = None
    working_dir: Optional[str] = None
    git_worktree: Optional[str] = None
    status: Optional[Literal['idle', 'executing', 'waiting', 'blocked', 'complete']] = None
    session_id: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    archived: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
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
        """Parse JSON string metadata to dict"""
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


# ═══════════════════════════════════════════════════════════
# PROMPT MODEL
# ═══════════════════════════════════════════════════════════


class Prompt(BaseModel):
    """
    Prompts sent to agents from engineers or orchestrator.

    Maps to: prompts table
    """
    id: UUID
    agent_id: Optional[UUID] = None
    task_slug: Optional[str] = None
    author: Literal['engineer', 'orchestrator_agent']
    prompt_text: str
    summary: Optional[str] = None
    timestamp: datetime
    session_id: Optional[str] = None

    @field_validator('id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# AGENT_LOG MODEL
# ═══════════════════════════════════════════════════════════


class AgentLog(BaseModel):
    """
    Unified event log for hooks and agent responses during task execution.

    Maps to: agent_logs table
    """
    id: UUID
    agent_id: UUID
    session_id: Optional[str] = None
    task_slug: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    entry_index: Optional[int] = None
    event_category: Literal['hook', 'response', 'adw_step']
    event_type: str
    content: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    timestamp: datetime

    @field_validator('id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('payload', mode='before')
    @classmethod
    def parse_payload(cls, v):
        """Parse JSON string payload to dict"""
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


# ═══════════════════════════════════════════════════════════
# SYSTEM_LOG MODEL
# ═══════════════════════════════════════════════════════════


class SystemLog(BaseModel):
    """
    Application-level system logs (global application events only).

    For agent-related logs, use agent_logs table instead.

    Maps to: system_logs table
    """
    id: UUID
    file_path: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']
    message: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
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


# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR_CHAT MODEL
# ═══════════════════════════════════════════════════════════


class OrchestratorChat(BaseModel):
    """
    Append-only conversation log capturing 3-way communication: user ↔ orchestrator ↔ agents.

    Maps to: orchestrator_chat table
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    orchestrator_agent_id: UUID
    sender_type: Literal['user', 'orchestrator', 'agent']
    receiver_type: Literal['user', 'orchestrator', 'agent']
    message: str
    summary: Optional[str] = None
    agent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('id', 'orchestrator_agent_id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
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


# ═══════════════════════════════════════════════════════════
# AI_DEVELOPER_WORKFLOW MODEL
# ═══════════════════════════════════════════════════════════


class AiDeveloperWorkflow(BaseModel):
    """
    Tracks AI Developer Workflow executions in the system.

    Maps to: ai_developer_workflows table
    """
    id: UUID
    orchestrator_agent_id: Optional[UUID] = None
    adw_name: str
    workflow_type: str
    description: Optional[str] = None
    status: Literal['pending', 'in_progress', 'completed', 'failed', 'cancelled'] = 'pending'
    current_step: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_step: Optional[str] = None
    error_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('input_data', 'output_data', 'metadata', mode='before')
    @classmethod
    def parse_jsonb(cls, v):
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


# ═══════════════════════════════════════════════════════════
# EXPORT PUBLIC API
# ═══════════════════════════════════════════════════════════

__all__ = [
    "OrchestratorAgent",
    "Agent",
    "Prompt",
    "AgentLog",
    "SystemLog",
    "OrchestratorChat",
    "AiDeveloperWorkflow",
]
