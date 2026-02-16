"""
SQLModel Database Models for Session Management

These models define the database schema for tracking:
- Projects: Managed codebases with onboarding status
- Sessions: Workflow containers (spec -> plan -> build -> docs)
- Agents: Individual agent invocations with Claude SDK session tracking
- AgentLogs: Execution events for observability

Architecture:
- Session artifacts (spec.md, plan.json) live in the filesystem
- Database tracks execution state, timing, costs, and events
- Agents store sdk_session_id for Claude conversation resumption

Re-exports all models for backward compatibility with:
    from database.models import Session, Agent, AgentLog, Project
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════════════════
from .agent import (
    Agent,
    AgentCreate,
    AgentStatus,
    AgentSummary,
    AgentType,
    AgentUpdate,
)

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT LOG
# ═══════════════════════════════════════════════════════════════════════════════
from .agent_log import (
    AgentLog,
    AgentLogCreate,
    AgentLogSummary,
    EventCategory,
)
from .project import (
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectSummary,
    ProjectUpdate,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION
# ═══════════════════════════════════════════════════════════════════════════════
from .session import (
    Session,
    SessionCreate,
    SessionStatus,
    SessionSummary,
    SessionType,
    SessionUpdate,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Project
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectSummary",
    "ProjectStatus",
    # Session
    "Session",
    "SessionCreate",
    "SessionUpdate",
    "SessionSummary",
    "SessionStatus",
    "SessionType",
    # Agent
    "Agent",
    "AgentCreate",
    "AgentUpdate",
    "AgentSummary",
    "AgentType",
    "AgentStatus",
    # AgentLog
    "AgentLog",
    "AgentLogCreate",
    "AgentLogSummary",
    "EventCategory",
]
