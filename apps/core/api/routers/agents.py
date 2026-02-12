"""
Agents Router

Endpoints for listing and retrieving agent information and logs.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from session_db import (
    Agent,
    AgentLog,
    AgentSummary,
    AgentLogSummary,
    get_agent,
    get_session,
    list_agent_summaries_for_session,
    list_logs_for_agent,
)

from ..dependencies import get_db


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/session/{session_id}", response_model=list[AgentSummary])
async def list_session_agents_endpoint(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AgentSummary]:
    """
    List agents for a specific session.

    Returns agent summaries with:
    - Agent type (spec, plan, build, etc.)
    - Status (pending, executing, complete, failed)
    - Checkpoint/task group context
    - Token counts and cost

    Raises 404 if session not found.
    """
    # Verify session exists
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return await list_agent_summaries_for_session(db, session_id)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent_endpoint(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """
    Get an agent by ID.

    Returns full agent details including:
    - Model configuration
    - System prompt
    - Token counts and cost
    - Timing information
    - Error details (if failed)

    Raises 404 if agent not found.
    """
    agent = await get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    return agent


@router.get("/{agent_id}/logs", response_model=list[AgentLogSummary])
async def list_agent_logs_endpoint(
    agent_id: UUID,
    event_category: Optional[str] = Query(
        None, description="Filter by event category: hook, response, phase"
    ),
    event_type: Optional[str] = Query(
        None, description="Filter by specific event type"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of logs to return"
    ),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[AgentLogSummary]:
    """
    List logs/events for an agent.

    Returns a timeline of events including:
    - Hook events (tool calls, notifications)
    - Response blocks (text, thinking)
    - Phase transitions

    Events are ordered chronologically (oldest first).

    Raises 404 if agent not found.
    """
    # Verify agent exists
    agent = await get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    logs = await list_logs_for_agent(
        db,
        agent_id,
        event_category=event_category,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )

    # Convert to summary format
    return [
        AgentLogSummary(
            id=log.id,
            agent_id=log.agent_id,
            session_id=log.session_id,
            event_category=log.event_category,
            event_type=log.event_type,
            tool_name=log.tool_name,
            content=log.content,
            summary=log.summary,
            timestamp=log.timestamp,
            duration_ms=log.duration_ms,
        )
        for log in logs
    ]


@router.get("/{agent_id}/logs/{log_id}", response_model=AgentLog)
async def get_agent_log_endpoint(
    agent_id: UUID,
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AgentLog:
    """
    Get a specific log entry with full payload.

    Returns complete log details including:
    - Full payload JSON
    - Tool input/output
    - Entry index
    - All metadata

    Raises 404 if agent or log not found.
    """
    from session_db import get_agent_log

    # Verify agent exists
    agent = await get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    log = await get_agent_log(db, log_id)
    if not log or log.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log {log_id} not found for agent {agent_id}",
        )

    return log
