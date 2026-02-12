"""
Sessions Router

CRUD endpoints for managing sessions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from session_db import (
    Session,
    SessionSummary,
    get_session,
    get_session_by_slug,
    list_session_summaries,
)

from ..dependencies import get_db


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=list[SessionSummary])
async def list_sessions_endpoint(
    status_filter: str | None = None,
    session_type: str | None = None,
    project_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[SessionSummary]:
    """
    List all sessions.

    Optional filters:
    - status_filter: Filter by session status (created, spec, plan, build, etc.)
    - session_type: Filter by type (full, quick, research)
    - project_id: Filter by parent project
    - limit: Maximum number of results (default 100)
    - offset: Number of results to skip (default 0)
    """
    return await list_session_summaries(
        db,
        status=status_filter,
        session_type=session_type,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{session_id}", response_model=Session)
async def get_session_endpoint(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Session:
    """
    Get a session by ID.

    Raises 404 if session not found.
    """
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    return session


@router.get("/slug/{slug}", response_model=Session)
async def get_session_by_slug_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> Session:
    """
    Get a session by its slug.

    Raises 404 if session not found.
    """
    session = await get_session_by_slug(db, slug)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with slug '{slug}' not found",
        )
    return session
