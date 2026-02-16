"""
Session Database Package

SQLModel-based database for tracking session workflows and agent execution.

Usage:
    from database import Session, Agent, AgentLog
    from database.connection import get_async_session, init_db
    from database.crud import create_session, list_sessions
"""

from .async_sync import (
    make_sync_callback,
    queue_batch_sync_task,
    queue_sync_task,
)
from .crud import (
    count_logs_for_session,
    # Agent CRUD
    create_agent,
    # AgentLog CRUD
    create_agent_log,
    # Project CRUD
    create_project,
    # Session CRUD
    create_session,
    delete_agent,
    delete_project,
    delete_session,
    get_agent,
    get_agent_log,
    get_project,
    get_project_by_slug,
    get_session,
    get_session_by_slug,
    list_agent_summaries_for_session,
    list_agents_for_session,
    list_logs_for_agent,
    list_logs_for_session,
    list_project_summaries,
    list_projects,
    list_session_summaries,
    list_sessions,
    update_agent,
    update_project,
    update_session,
    # Helpers
    update_session_stats,
)
from .connection import (
    close_db,
    drop_db,
    get_async_session,
    get_engine,
    init_db,
    reset_db,
)
from .models import (
    Agent,
    AgentCreate,
    AgentLog,
    AgentLogCreate,
    AgentLogSummary,
    AgentStatus,
    AgentSummary,
    AgentType,
    AgentUpdate,
    EventCategory,
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectSummary,
    ProjectUpdate,
    # Core models
    Session,
    # DTOs
    SessionCreate,
    # Type aliases
    SessionStatus,
    # Summary models
    SessionSummary,
    SessionType,
    SessionUpdate,
)

__all__ = [
    # Type aliases
    "SessionStatus",
    "SessionType",
    "AgentType",
    "AgentStatus",
    "EventCategory",
    "ProjectStatus",
    # Core models
    "Session",
    "Agent",
    "AgentLog",
    "Project",
    # Summary models
    "SessionSummary",
    "AgentSummary",
    "AgentLogSummary",
    "ProjectSummary",
    # DTOs
    "SessionCreate",
    "SessionUpdate",
    "ProjectCreate",
    "ProjectUpdate",
    "AgentCreate",
    "AgentUpdate",
    "AgentLogCreate",
    # Async sync
    "make_sync_callback",
    "queue_sync_task",
    "queue_batch_sync_task",
    # Database
    "get_engine",
    "get_async_session",
    "init_db",
    "drop_db",
    "reset_db",
    "close_db",
    # Project CRUD
    "create_project",
    "get_project",
    "get_project_by_slug",
    "list_projects",
    "list_project_summaries",
    "update_project",
    "delete_project",
    # Session CRUD
    "create_session",
    "get_session",
    "get_session_by_slug",
    "list_sessions",
    "list_session_summaries",
    "update_session",
    "delete_session",
    # Agent CRUD
    "create_agent",
    "get_agent",
    "list_agents_for_session",
    "list_agent_summaries_for_session",
    "update_agent",
    "delete_agent",
    # AgentLog CRUD
    "create_agent_log",
    "get_agent_log",
    "list_logs_for_agent",
    "list_logs_for_session",
    "count_logs_for_session",
    # Helpers
    "update_session_stats",
]
