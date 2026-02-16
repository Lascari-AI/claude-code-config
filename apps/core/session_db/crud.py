"""
CRUD Operations for Session Database

Provides async functions for creating, reading, updating, and deleting
sessions, agents, and logs.

Usage:
    from session_db.crud import create_session, get_session, list_sessions
    from session_db.database import get_async_session

    async with get_async_session() as db:
        session = await create_session(db, SessionCreate(...))
        sessions = await list_sessions(db)
"""

from datetime import datetime
from typing import Sequence
from uuid import UUID
import json

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionSummary,
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectSummary,
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentSummary,
    AgentLog,
    AgentLogCreate,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT CRUD
# ═══════════════════════════════════════════════════════════════════════════════


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    """
    Create a new project.

    Args:
        db: Database session
        data: Project creation data

    Returns:
        The created project
    """
    project = Project(
        name=data.name,
        slug=data.slug,
        path=data.path,
        repo_url=data.repo_url,
        status=data.status,
        onboarding_status=data.onboarding_status,
        metadata_=data.metadata_,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def get_project(db: AsyncSession, project_id: UUID) -> Project | None:
    """
    Get a project by ID.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        The project or None if not found
    """
    return await db.get(Project, project_id)


async def get_project_by_slug(db: AsyncSession, slug: str) -> Project | None:
    """
    Get a project by its slug.

    Args:
        db: Database session
        slug: Project slug

    Returns:
        The project or None if not found
    """
    result = await db.exec(select(Project).where(Project.slug == slug))
    return result.first()


async def list_projects(
    db: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Project]:
    """
    List projects with optional filtering.

    Args:
        db: Database session
        status: Filter by status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of projects
    """
    query = select(Project).order_by(Project.created_at.desc())

    if status:
        query = query.where(Project.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.exec(query)
    return result.all()


async def list_project_summaries(
    db: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ProjectSummary]:
    """
    List project summaries (lightweight view).

    Args:
        db: Database session
        status: Filter by status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of project summaries
    """
    projects = await list_projects(db, status=status, limit=limit, offset=offset)
    return [
        ProjectSummary(
            id=p.id,
            name=p.name,
            slug=p.slug,
            status=p.status,
            path=p.path,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    data: ProjectUpdate,
) -> Project | None:
    """
    Update a project.

    Args:
        db: Database session
        project_id: Project UUID
        data: Update data (only non-None fields are updated)

    Returns:
        The updated project or None if not found
    """
    project = await db.get(Project, project_id)
    if not project:
        return None

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in update_data.items():
        setattr(project, key, value)

    project.updated_at = datetime.utcnow()
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: UUID) -> bool:
    """
    Delete a project.

    Note: This will fail if sessions reference this project.
    Consider archiving instead of deleting.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        True if deleted, False if not found
    """
    project = await db.get(Project, project_id)
    if not project:
        return False

    await db.delete(project)
    await db.flush()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION CRUD
# ═══════════════════════════════════════════════════════════════════════════════


async def create_session(db: AsyncSession, data: SessionCreate) -> Session:
    """
    Create a new session.

    Args:
        db: Database session
        data: Session creation data

    Returns:
        The created session
    """
    session = Session(
        session_slug=data.session_slug,
        title=data.title,
        description=data.description,
        session_type=data.session_type,
        working_dir=data.working_dir,
        session_dir=data.session_dir,
        project_id=data.project_id,
        # Git context (v2)
        git_worktree=data.git_worktree,
        git_branch=data.git_branch,
        git_base_branch=data.git_base_branch,
        # Phase tracking (v2)
        current_phase=data.current_phase,
        status=data.status,
        phase_history=data.phase_history,
        # Build progress (v2)
        checkpoints_total=data.checkpoints_total,
        checkpoints_completed=len(data.checkpoints_completed_list),
        checkpoints_completed_list=data.checkpoints_completed_list,
        current_checkpoint=data.current_checkpoint,
        # Commits and artifacts (v2)
        commits_list=data.commits_list,
        artifacts=data.artifacts,
        metadata_=data.metadata_,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> Session | None:
    """
    Get a session by ID.

    Args:
        db: Database session
        session_id: Session UUID

    Returns:
        The session or None if not found
    """
    return await db.get(Session, session_id)


async def get_session_by_slug(db: AsyncSession, slug: str) -> Session | None:
    """
    Get a session by its slug.

    Args:
        db: Database session
        slug: Session slug (folder name)

    Returns:
        The session or None if not found
    """
    result = await db.exec(select(Session).where(Session.session_slug == slug))
    return result.first()


async def list_sessions(
    db: AsyncSession,
    *,
    status: str | None = None,
    session_type: str | None = None,
    project_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Session]:
    """
    List sessions with optional filtering.

    Args:
        db: Database session
        status: Filter by status
        session_type: Filter by session type
        project_id: Filter by project
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of sessions
    """
    query = select(Session).order_by(Session.created_at.desc())

    if status:
        query = query.where(Session.status == status)
    if session_type:
        query = query.where(Session.session_type == session_type)
    if project_id:
        query = query.where(Session.project_id == project_id)

    query = query.limit(limit).offset(offset)
    result = await db.exec(query)
    return result.all()


async def list_session_summaries(
    db: AsyncSession,
    *,
    status: str | None = None,
    session_type: str | None = None,
    project_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SessionSummary]:
    """
    List session summaries (lightweight view).

    Args:
        db: Database session
        status: Filter by status
        session_type: Filter by session type
        project_id: Filter by project
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of session summaries
    """
    sessions = await list_sessions(
        db,
        status=status,
        session_type=session_type,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return [
        SessionSummary(
            id=s.id,
            session_slug=s.session_slug,
            title=s.title,
            status=s.status,
            current_phase=s.current_phase,
            session_type=s.session_type,
            project_id=s.project_id,
            checkpoints_completed=s.checkpoints_completed,
            checkpoints_total=s.checkpoints_total,
            current_checkpoint=s.current_checkpoint,
            total_cost=s.total_cost,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


async def update_session(
    db: AsyncSession,
    session_id: UUID,
    data: SessionUpdate,
) -> Session | None:
    """
    Update a session.

    Args:
        db: Database session
        session_id: Session UUID
        data: Update data (only non-None fields are updated)

    Returns:
        The updated session or None if not found
    """
    session = await db.get(Session, session_id)
    if not session:
        return None

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in update_data.items():
        setattr(session, key, value)

    session.updated_at = datetime.utcnow()
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: UUID) -> bool:
    """
    Delete a session and all related agents/logs.

    Args:
        db: Database session
        session_id: Session UUID

    Returns:
        True if deleted, False if not found
    """
    session = await db.get(Session, session_id)
    if not session:
        return False

    await db.delete(session)
    await db.flush()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT CRUD
# ═══════════════════════════════════════════════════════════════════════════════


async def create_agent(db: AsyncSession, data: AgentCreate) -> Agent:
    """
    Create a new agent.

    Args:
        db: Database session
        data: Agent creation data

    Returns:
        The created agent
    """
    agent = Agent(
        session_id=data.session_id,
        agent_type=data.agent_type,
        name=data.name,
        model=data.model,
        model_alias=data.model_alias,
        system_prompt=data.system_prompt,
        working_dir=data.working_dir,
        checkpoint_id=data.checkpoint_id,
        task_group_id=data.task_group_id,
        metadata_=data.metadata_,
    )

    if data.allowed_tools:
        agent.set_allowed_tools(data.allowed_tools)

    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: UUID) -> Agent | None:
    """
    Get an agent by ID.

    Args:
        db: Database session
        agent_id: Agent UUID

    Returns:
        The agent or None if not found
    """
    return await db.get(Agent, agent_id)


async def list_agents_for_session(
    db: AsyncSession,
    session_id: UUID,
    *,
    agent_type: str | None = None,
    status: str | None = None,
) -> Sequence[Agent]:
    """
    List agents for a session.

    Args:
        db: Database session
        session_id: Session UUID
        agent_type: Filter by agent type
        status: Filter by status

    Returns:
        List of agents
    """
    query = select(Agent).where(Agent.session_id == session_id).order_by(Agent.created_at.asc())

    if agent_type:
        query = query.where(Agent.agent_type == agent_type)
    if status:
        query = query.where(Agent.status == status)

    result = await db.exec(query)
    return result.all()


async def list_agent_summaries_for_session(
    db: AsyncSession,
    session_id: UUID,
) -> list[AgentSummary]:
    """
    List agent summaries for a session.

    Args:
        db: Database session
        session_id: Session UUID

    Returns:
        List of agent summaries
    """
    agents = await list_agents_for_session(db, session_id)
    return [
        AgentSummary(
            id=a.id,
            agent_type=a.agent_type,
            name=a.name,
            model_alias=a.model_alias,
            status=a.status,
            checkpoint_id=a.checkpoint_id,
            input_tokens=a.input_tokens,
            output_tokens=a.output_tokens,
            cost=a.cost,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in agents
    ]


async def update_agent(
    db: AsyncSession,
    agent_id: UUID,
    data: AgentUpdate,
) -> Agent | None:
    """
    Update an agent.

    Args:
        db: Database session
        agent_id: Agent UUID
        data: Update data

    Returns:
        The updated agent or None if not found
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        return None

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in update_data.items():
        setattr(agent, key, value)

    agent.updated_at = datetime.utcnow()
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent_id: UUID) -> bool:
    """
    Delete an agent and all related logs.

    Args:
        db: Database session
        agent_id: Agent UUID

    Returns:
        True if deleted, False if not found
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        return False

    await db.delete(agent)
    await db.flush()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT LOG CRUD
# ═══════════════════════════════════════════════════════════════════════════════


async def create_agent_log(db: AsyncSession, data: AgentLogCreate) -> AgentLog:
    """
    Create a new agent log entry.

    Args:
        db: Database session
        data: Log entry data

    Returns:
        The created log entry
    """
    log = AgentLog(
        agent_id=data.agent_id,
        session_id=data.session_id,
        sdk_session_id=data.sdk_session_id,
        event_category=data.event_category,
        event_type=data.event_type,
        content=data.content,
        payload=data.payload,
        summary=data.summary,
        tool_name=data.tool_name,
        tool_output=data.tool_output,
        entry_index=data.entry_index,
        checkpoint_id=data.checkpoint_id,
        duration_ms=data.duration_ms,
    )

    if data.tool_input:
        log.set_tool_input(data.tool_input)

    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def get_agent_log(db: AsyncSession, log_id: UUID) -> AgentLog | None:
    """
    Get a log entry by ID.

    Args:
        db: Database session
        log_id: Log entry UUID

    Returns:
        The log entry or None if not found
    """
    return await db.get(AgentLog, log_id)


async def list_logs_for_agent(
    db: AsyncSession,
    agent_id: UUID,
    *,
    event_category: str | None = None,
    event_type: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> Sequence[AgentLog]:
    """
    List logs for an agent.

    Args:
        db: Database session
        agent_id: Agent UUID
        event_category: Filter by category
        event_type: Filter by event type
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of log entries
    """
    query = select(AgentLog).where(AgentLog.agent_id == agent_id).order_by(AgentLog.timestamp.asc())

    if event_category:
        query = query.where(AgentLog.event_category == event_category)
    if event_type:
        query = query.where(AgentLog.event_type == event_type)

    query = query.limit(limit).offset(offset)
    result = await db.exec(query)
    return result.all()


async def list_logs_for_session(
    db: AsyncSession,
    session_id: UUID,
    *,
    event_category: str | None = None,
    event_type: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> Sequence[AgentLog]:
    """
    List logs for a session (across all agents).

    Args:
        db: Database session
        session_id: Session UUID
        event_category: Filter by category
        event_type: Filter by event type
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of log entries
    """
    query = (
        select(AgentLog).where(AgentLog.session_id == session_id).order_by(AgentLog.timestamp.asc())
    )

    if event_category:
        query = query.where(AgentLog.event_category == event_category)
    if event_type:
        query = query.where(AgentLog.event_type == event_type)

    query = query.limit(limit).offset(offset)
    result = await db.exec(query)
    return result.all()


async def count_logs_for_session(
    db: AsyncSession,
    session_id: UUID,
    *,
    event_category: str | None = None,
) -> int:
    """
    Count logs for a session.

    Args:
        db: Database session
        session_id: Session UUID
        event_category: Filter by category

    Returns:
        Number of log entries
    """
    from sqlalchemy import func

    query = select(func.count(AgentLog.id)).where(AgentLog.session_id == session_id)

    if event_category:
        query = query.where(AgentLog.event_category == event_category)

    result = await db.exec(query)
    return result.one()


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


async def update_session_stats(db: AsyncSession, session_id: UUID) -> Session | None:
    """
    Recalculate and update session aggregated stats from agents.

    Args:
        db: Database session
        session_id: Session UUID

    Returns:
        The updated session or None if not found
    """
    session = await db.get(Session, session_id)
    if not session:
        return None

    agents = await list_agents_for_session(db, session_id)

    session.total_input_tokens = sum(a.input_tokens for a in agents)
    session.total_output_tokens = sum(a.output_tokens for a in agents)
    session.total_cost = sum(a.cost for a in agents)
    session.updated_at = datetime.utcnow()

    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session
