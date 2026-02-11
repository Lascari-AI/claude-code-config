"""
Session Database Package

SQLModel-based database for tracking session workflows and agent execution.

Usage:
    from session_db import Session, Agent, AgentLog
    from session_db.database import get_async_session, init_db
    from session_db.crud import create_session, list_sessions
"""

from .models import (
    # Type aliases
    SessionStatus,
    SessionType,
    AgentType,
    AgentStatus,
    EventCategory,
    # Core models
    Session,
    Agent,
    AgentLog,
    # Summary models
    SessionSummary,
    AgentSummary,
    # DTOs
    SessionCreate,
    SessionUpdate,
    AgentCreate,
    AgentUpdate,
    AgentLogCreate,
)

from .database import (
    get_engine,
    get_async_session,
    init_db,
    drop_db,
    reset_db,
    close_db,
)

from .crud import (
    # Session CRUD
    create_session,
    get_session,
    get_session_by_slug,
    list_sessions,
    list_session_summaries,
    update_session,
    delete_session,
    # Agent CRUD
    create_agent,
    get_agent,
    list_agents_for_session,
    list_agent_summaries_for_session,
    update_agent,
    delete_agent,
    # AgentLog CRUD
    create_agent_log,
    get_agent_log,
    list_logs_for_agent,
    list_logs_for_session,
    count_logs_for_session,
    # Helpers
    update_session_stats,
)

__all__ = [
    # Type aliases
    "SessionStatus",
    "SessionType",
    "AgentType",
    "AgentStatus",
    "EventCategory",
    # Core models
    "Session",
    "Agent",
    "AgentLog",
    # Summary models
    "SessionSummary",
    "AgentSummary",
    # DTOs
    "SessionCreate",
    "SessionUpdate",
    "AgentCreate",
    "AgentUpdate",
    "AgentLogCreate",
    # Database
    "get_engine",
    "get_async_session",
    "init_db",
    "drop_db",
    "reset_db",
    "close_db",
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
