"""
Projects Router

CRUD endpoints for managing projects.
"""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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


# Request model for onboarding
class OnboardProjectRequest(BaseModel):
    """Request body for onboarding a new project."""

    name: str
    path: str


# Response model for onboarding validation
class OnboardingValidation(BaseModel):
    """Validation results for onboarding."""

    path_validated: bool
    claude_dir_exists: bool
    path_error: str | None = None


# Response model for directory browsing
class DirectoryEntry(BaseModel):
    """A directory entry for browsing."""

    name: str
    path: str
    is_directory: bool
    has_claude_dir: bool = False


class BrowseResponse(BaseModel):
    """Response for directory browsing."""

    current_path: str
    parent_path: str | None
    entries: list[DirectoryEntry]
    error: str | None = None


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


@router.post("/onboard", response_model=Project, status_code=status.HTTP_201_CREATED)
async def onboard_project_endpoint(
    data: OnboardProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Onboard a new project with path validation.

    Validates:
    - Path exists and is accessible
    - Checks for .claude directory

    Creates the project with onboarding_status tracking the validation results.
    """
    # Validate the path
    path = os.path.expanduser(data.path)
    path_validated = os.path.isdir(path)
    path_error = None

    if not path_validated:
        if not os.path.exists(path):
            path_error = "Path does not exist"
        elif not os.path.isdir(path):
            path_error = "Path is not a directory"

    # Check for .claude directory
    claude_dir_path = os.path.join(path, ".claude")
    claude_dir_exists = os.path.isdir(claude_dir_path) if path_validated else False

    # Build onboarding status
    onboarding_status = {
        "path_validated": path_validated,
        "claude_dir_exists": claude_dir_exists,
        "settings_configured": False,
        "skills_linked": False,
        "agents_linked": False,
        "docs_foundation": False,
    }

    # Determine project status based on validation
    if path_validated and claude_dir_exists:
        project_status = "active"
    elif path_validated:
        project_status = "onboarding"
    else:
        project_status = "pending"

    # Generate slug from name
    slug = data.name.lower().replace(" ", "-").replace("_", "-")
    # Remove any non-alphanumeric characters except hyphens
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    # Check if slug already exists
    existing = await get_project_by_slug(db, slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with slug '{slug}' already exists",
        )

    # Create the project
    project_data = ProjectCreate(
        name=data.name,
        slug=slug,
        path=path,
        status=project_status,
        onboarding_status=onboarding_status,
    )

    project = await create_project(db, project_data)
    await db.commit()

    return project


@router.post("/validate-path", response_model=OnboardingValidation)
async def validate_project_path(
    data: OnboardProjectRequest,
) -> OnboardingValidation:
    """
    Validate a project path without creating a project.

    Useful for checking path validity before onboarding.
    """
    path = os.path.expanduser(data.path)
    path_validated = os.path.isdir(path)
    path_error = None

    if not path_validated:
        if not os.path.exists(path):
            path_error = "Path does not exist"
        elif not os.path.isdir(path):
            path_error = "Path is not a directory"

    claude_dir_path = os.path.join(path, ".claude")
    claude_dir_exists = os.path.isdir(claude_dir_path) if path_validated else False

    return OnboardingValidation(
        path_validated=path_validated,
        claude_dir_exists=claude_dir_exists,
        path_error=path_error,
    )


@router.get("/browse", response_model=BrowseResponse)
async def browse_directories(
    path: str = "~",
) -> BrowseResponse:
    """
    Browse directories for project selection.

    Lists directories at the given path. Only shows directories (not files)
    to help users navigate to their project folder.

    Query params:
    - path: Directory path to browse (default: home directory)
    """
    # Expand user home directory
    expanded_path = os.path.expanduser(path)

    # Normalize the path
    expanded_path = os.path.normpath(expanded_path)

    # Security check: don't allow browsing certain system directories
    blocked_prefixes = ["/proc", "/sys", "/dev"]
    for blocked in blocked_prefixes:
        if expanded_path.startswith(blocked):
            return BrowseResponse(
                current_path=expanded_path,
                parent_path=None,
                entries=[],
                error="Access to system directories is not allowed",
            )

    # Check if path exists
    if not os.path.exists(expanded_path):
        return BrowseResponse(
            current_path=expanded_path,
            parent_path=os.path.dirname(expanded_path),
            entries=[],
            error="Path does not exist",
        )

    if not os.path.isdir(expanded_path):
        return BrowseResponse(
            current_path=expanded_path,
            parent_path=os.path.dirname(expanded_path),
            entries=[],
            error="Path is not a directory",
        )

    # Get parent path (None if at root)
    parent_path = os.path.dirname(expanded_path)
    if parent_path == expanded_path:  # At root
        parent_path = None

    # List directory contents
    entries: list[DirectoryEntry] = []
    try:
        for entry_name in sorted(os.listdir(expanded_path)):
            # Skip hidden files/dirs (except .claude which we check for)
            if entry_name.startswith("."):
                continue

            entry_path = os.path.join(expanded_path, entry_name)

            # Only include directories
            if os.path.isdir(entry_path):
                # Check if this directory has a .claude subdirectory
                claude_dir = os.path.join(entry_path, ".claude")
                has_claude = os.path.isdir(claude_dir)

                entries.append(
                    DirectoryEntry(
                        name=entry_name,
                        path=entry_path,
                        is_directory=True,
                        has_claude_dir=has_claude,
                    )
                )
    except PermissionError:
        return BrowseResponse(
            current_path=expanded_path,
            parent_path=parent_path,
            entries=[],
            error="Permission denied",
        )

    return BrowseResponse(
        current_path=expanded_path,
        parent_path=parent_path,
        entries=entries,
        error=None,
    )
