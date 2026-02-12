"""
Sessions Router

CRUD endpoints for managing sessions and serving session artifacts.
"""

import os
import json
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from session_db import (
    Session,
    SessionSummary,
    get_session,
    get_session_by_slug,
    list_session_summaries,
)

from ..dependencies import get_db


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class SpecContent(BaseModel):
    """Response model for spec.md content."""

    content: str
    exists: bool = True


class ArtifactNotFound(BaseModel):
    """Response model when artifact doesn't exist."""

    detail: str
    exists: bool = False


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


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════════════


def _get_session_dir(session: Session) -> Path | None:
    """
    Get the session directory path.

    Tries session_dir first, then falls back to constructing from working_dir.
    """
    if session.session_dir:
        return Path(session.session_dir)

    # Fallback: construct path from working_dir + agents/sessions/{slug}
    if session.working_dir:
        return Path(session.working_dir) / "agents" / "sessions" / session.session_slug

    return None


@router.get("/{slug}/spec", response_model=SpecContent)
async def get_session_spec(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> SpecContent:
    """
    Get the spec.md content for a session.

    Returns the rendered specification document as markdown text.
    Raises 404 if session or spec file not found.
    """
    session = await get_session_by_slug(db, slug)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with slug '{slug}' not found",
        )

    session_dir = _get_session_dir(session)
    if not session_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session directory not found for '{slug}'",
        )

    spec_path = session_dir / "spec.md"
    if not spec_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"spec.md not found for session '{slug}'",
        )

    try:
        content = spec_path.read_text(encoding="utf-8")
        return SpecContent(content=content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading spec.md: {str(e)}",
        )


@router.get("/{slug}/plan")
async def get_session_plan(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the plan.json content for a session.

    Returns the full plan structure with checkpoints, task groups, and tasks.
    Raises 404 if session or plan file not found.
    """
    session = await get_session_by_slug(db, slug)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with slug '{slug}' not found",
        )

    session_dir = _get_session_dir(session)
    if not session_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session directory not found for '{slug}'",
        )

    plan_path = session_dir / "plan.json"
    if not plan_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"plan.json not found for session '{slug}'",
        )

    try:
        content = plan_path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON in plan.json: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading plan.json: {str(e)}",
        )


@router.get("/{slug}/state")
async def get_session_state(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the state.json content for a session.

    Returns the session state including phase status, progress, and metadata.
    Raises 404 if session or state file not found.
    """
    session = await get_session_by_slug(db, slug)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with slug '{slug}' not found",
        )

    session_dir = _get_session_dir(session)
    if not session_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session directory not found for '{slug}'",
        )

    state_path = session_dir / "state.json"
    if not state_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"state.json not found for session '{slug}'",
        )

    try:
        content = state_path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON in state.json: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading state.json: {str(e)}",
        )
