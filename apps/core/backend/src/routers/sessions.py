"""
Sessions Router - Endpoints for session lifecycle management.

Provides session creation endpoint that:
- Creates filesystem directory + state.json
- Creates database record via CRUD
- Returns session info for frontend navigation
"""

from __future__ import annotations

import json
import logging
import re
import string
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.connection import get_async_session
from database.crud import create_session, get_project_by_slug
from database.models import SessionCreate

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class SessionCreateRequest(BaseModel):
    """Request body for creating a new session."""

    project_path: str
    topic: Optional[str] = None


class SessionCreateResponse(BaseModel):
    """Response body after session creation."""

    session_slug: str
    session_id: UUID
    session_dir: str


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_length]


def _generate_session_slug(topic: Optional[str]) -> str:
    """Generate session slug: YYYY-MM-DD_{slugified_topic}_{6-char-random}."""
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    topic_part = _slugify(topic) if topic else "session"
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{date_prefix}_{topic_part}_{random_suffix}"


def _build_initial_state(session_slug: str, topic: Optional[str]) -> dict:
    """Build initial state.json for a new session."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "$schema": "Session state manifest v2 - programmatic updates only",
        "session_id": session_slug,
        "topic": topic or "New Session",
        "description": None,
        "granularity": "feature",
        "session_type": "full",
        "created_at": now,
        "updated_at": now,
        "current_phase": "spec",
        "status": "active",
        "phase_history": {
            "spec_started_at": now,
            "spec_completed_at": None,
            "plan_started_at": None,
            "plan_completed_at": None,
            "build_started_at": None,
            "build_completed_at": None,
            "docs_started_at": None,
            "docs_completed_at": None,
        },
        "build_progress": {
            "checkpoints_total": 0,
            "checkpoints_completed": [],
            "current_checkpoint": None,
        },
        "git": {
            "branch": None,
            "worktree": None,
            "base_branch": None,
        },
        "commits": [],
        "artifacts": {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/create", response_model=SessionCreateResponse)
async def create_new_session(request: SessionCreateRequest) -> SessionCreateResponse:
    """
    Create a new session with filesystem directory and database record.

    Generates a unique session slug, creates the directory structure with
    an initial state.json, and persists a DB record for frontend queries.

    Args:
        request: Project path and optional topic

    Returns:
        Session slug, database ID, and directory path

    Raises:
        HTTPException 400: Invalid project path or directory creation failure
        HTTPException 404: Project not found in database
    """
    project_path = Path(request.project_path)

    # Validate project path exists
    if not project_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Project path does not exist: {request.project_path}",
        )

    # Generate session slug and directory
    session_slug = _generate_session_slug(request.topic)
    sessions_base = project_path / "agents" / "sessions"
    session_dir = sessions_base / session_slug

    # Create directory structure
    try:
        session_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise HTTPException(
            status_code=400,
            detail=f"Session directory already exists: {session_slug}",
        )
    except OSError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create session directory: {e}",
        )

    # Write initial state.json
    state = _build_initial_state(session_slug, request.topic)
    state_file = session_dir / "state.json"
    state_file.write_text(json.dumps(state, indent=2) + "\n")

    logger.info("Created session directory: %s", session_dir)

    # Look up project in DB by path to get project_id
    project_id = None
    async with get_async_session() as db:
        # Find project by path match
        from sqlmodel import select
        from database.models import Project

        result = await db.exec(select(Project).where(Project.path == str(project_path)))
        project = result.first()
        if project:
            project_id = project.id

    # Create DB record
    now_str = datetime.now(timezone.utc).isoformat()
    session_data = SessionCreate(
        session_slug=session_slug,
        title=request.topic,
        session_type="full",
        working_dir=str(project_path),
        session_dir=str(session_dir),
        project_id=project_id,
        current_phase="spec",
        status="active",
        phase_history={
            "spec_started_at": now_str,
        },
    )

    async with get_async_session() as db:
        session = await create_session(db, session_data)
        session_id = session.id

    logger.info("Created session DB record: slug=%s id=%s", session_slug, session_id)

    return SessionCreateResponse(
        session_slug=session_slug,
        session_id=session_id,
        session_dir=str(session_dir),
    )
