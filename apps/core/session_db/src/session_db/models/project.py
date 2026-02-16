"""
Project models - Database schema and DTOs for managed codebases.

A Project represents a repository/codebase that has been onboarded
into the managed system and can have sessions.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .session import Session


# ═══════════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

ProjectStatus = Literal[
    "pending",  # Registered but not yet set up
    "onboarding",  # Setup in progress
    "active",  # Fully managed, sessions can be created
    "paused",  # Temporarily inactive
    "archived",  # No longer managed
]


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT MODEL
# ═══════════════════════════════════════════════════════════════════════════════


class Project(SQLModel, table=True):
    """
    A codebase that has been onboarded into the managed system.

    Each project represents a repository/codebase that can have sessions.
    Projects track onboarding status and configuration for agent management.
    """

    __tablename__ = "projects"

    # ─── Identity ───────────────────────────────────────────────────────────────
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique project identifier",
    )
    name: str = Field(
        description="Human-friendly project name",
    )
    slug: str = Field(
        unique=True,
        index=True,
        description="URL-safe identifier for the project",
    )

    # ─── Location ───────────────────────────────────────────────────────────────
    path: str = Field(
        description="Absolute path to codebase root",
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="GitHub/GitLab URL if applicable",
    )

    # ─── Status ─────────────────────────────────────────────────────────────────
    status: str = Field(
        default="pending",
        index=True,
        description="Project lifecycle status",
    )
    onboarding_status: dict[str, Any] = Field(
        default_factory=lambda: {
            "path_validated": False,
            "claude_dir_exists": False,
            "settings_configured": False,
            "skills_linked": False,
            "agents_linked": False,
            "docs_foundation": False,
        },
        sa_column=Column(JSON),
        description="Track onboarding steps completed",
    )

    # ─── Metadata ───────────────────────────────────────────────────────────────
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON),
        description="Additional project configuration",
    )

    # ─── Timestamps ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When project was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )

    # ─── Relationships ──────────────────────────────────────────────────────────
    sessions: list["Session"] = Relationship(back_populates="project")


# ═══════════════════════════════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════════════════════════════


class ProjectSummary(SQLModel):
    """Lightweight project info for list views."""

    id: UUID
    name: str
    slug: str
    status: str
    path: str
    created_at: datetime
    updated_at: datetime


class ProjectCreate(SQLModel):
    """DTO for creating a new project."""

    name: str
    slug: str
    path: str
    repo_url: Optional[str] = None
    status: str = "pending"
    onboarding_status: dict[str, Any] = Field(default_factory=dict)
    metadata_: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(SQLModel):
    """DTO for updating project fields."""

    name: Optional[str] = None
    slug: Optional[str] = None
    path: Optional[str] = None
    repo_url: Optional[str] = None
    status: Optional[str] = None
    onboarding_status: Optional[dict[str, Any]] = None
    metadata_: Optional[dict[str, Any]] = None
