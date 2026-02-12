"""
Projects Router

CRUD endpoints for managing projects.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from session_db import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectSummary,
    SessionSummary,
    create_project,
    get_project,
    get_project_by_slug,
    list_project_summaries,
    list_session_summaries,
    update_project,
    delete_project,
)

from ..dependencies import get_db


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectSummary])
async def list_projects_endpoint(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectSummary]:
    """
    List all projects.

    Optional filters:
    - status: Filter by project status
    - limit: Maximum number of results (default 100)
    - offset: Number of results to skip (default 0)
    """
    return await list_project_summaries(db, status=status, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=Project)
async def get_project_endpoint(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Get a project by ID.

    Raises 404 if project not found.
    """
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.get("/slug/{slug}", response_model=Project)
async def get_project_by_slug_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Get a project by its slug.

    Raises 404 if project not found.
    """
    project = await get_project_by_slug(db, slug)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with slug '{slug}' not found",
        )
    return project


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Create a new project.

    Required fields:
    - name: Human-friendly project name
    - slug: URL-safe identifier (must be unique)
    - path: Absolute path to codebase root
    """
    # Check if slug already exists
    existing = await get_project_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with slug '{data.slug}' already exists",
        )

    project = await create_project(db, data)
    await db.commit()
    return project


@router.patch("/{project_id}", response_model=Project)
async def update_project_endpoint(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Update a project.

    Only provided fields are updated.
    Raises 404 if project not found.
    """
    # If updating slug, check for conflicts
    if data.slug:
        existing = await get_project_by_slug(db, data.slug)
        if existing and existing.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with slug '{data.slug}' already exists",
            )

    project = await update_project(db, project_id, data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    await db.commit()
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a project.

    Raises 404 if project not found.
    Note: This will fail if sessions reference this project.
    """
    deleted = await delete_project(db, project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    await db.commit()


@router.get("/{project_id}/sessions", response_model=list[SessionSummary])
async def list_project_sessions_endpoint(
    project_id: UUID,
    status_filter: str | None = None,
    session_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[SessionSummary]:
    """
    List sessions for a specific project.

    Optional filters:
    - status_filter: Filter by session status
    - session_type: Filter by type (full, quick, research)
    - limit: Maximum number of results (default 100)
    - offset: Number of results to skip (default 0)
    """
    # First verify the project exists
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return await list_session_summaries(
        db,
        status=status_filter,
        session_type=session_type,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
