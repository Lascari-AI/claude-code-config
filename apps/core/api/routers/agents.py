"""
Agents Router

Endpoints for listing and retrieving agent information.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from session_db import (
    Agent,
    AgentSummary,
    get_agent,
    get_session,
    list_agent_summaries_for_session,
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
