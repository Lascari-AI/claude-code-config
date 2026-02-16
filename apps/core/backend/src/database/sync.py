"""
Filesystem → Database Sync Functions

Provides functions to onboard sessions from the filesystem (state.json v2)
into the database. The filesystem is the source of truth - the database
is a reconstructable index for UI visibility and querying.

Usage:
    from database.sync import sync_session_from_filesystem, onboard_project_sessions
    from database.connection import get_async_session

    async with get_async_session() as db:
        # Sync a single session
        session = await sync_session_from_filesystem(db, working_dir, session_slug)

        # Onboard all sessions in a project
        sessions = await onboard_project_sessions(db, working_dir, project_id)
"""

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from .crud import create_session, get_session_by_slug, update_session
from .models import Session, SessionCreate, SessionUpdate

# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════


class SessionNotFoundOnFilesystem(Exception):
    """Raised when state.json doesn't exist for a session."""

    def __init__(self, session_slug: str, path: Path):
        self.session_slug = session_slug
        self.path = path
        super().__init__(f"Session '{session_slug}' not found at {path}")


class InvalidStateJson(Exception):
    """Raised when state.json cannot be parsed or is invalid."""

    def __init__(self, session_slug: str, error: str):
        self.session_slug = session_slug
        self.error = error
        super().__init__(f"Invalid state.json for '{session_slug}': {error}")


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MAPPING
# ═══════════════════════════════════════════════════════════════════════════════


def map_state_to_session_create(
    state: dict[str, Any],
    session_slug: str,
    working_dir: str,
    session_dir: str,
    project_id: UUID | None = None,
) -> SessionCreate:
    """
    Map state.json v2 fields to SessionCreate DTO.

    Handles both v1 (legacy) and v2 state.json formats for backwards compatibility.

    Args:
        state: Parsed state.json content
        session_slug: Session folder name
        working_dir: Absolute path to project root
        session_dir: Absolute path to session folder
        project_id: Optional project UUID

    Returns:
        SessionCreate DTO ready for database insertion
    """
    # ─── Handle v1 vs v2 schema differences ─────────────────────────────────────
    # v1 uses: current_phase in phases.*.status, plan_state for build progress
    # v2 uses: current_phase directly, build_progress for checkpoints

    # Detect schema version
    is_v2 = "phase_history" in state or "build_progress" in state

    # Current phase
    if is_v2:
        current_phase = state.get("current_phase", "spec")
    else:
        # v1: derive from phases
        current_phase = state.get("current_phase", "spec")

    # Status
    status = state.get("status", "active")
    if not is_v2:
        # v1 didn't have separate status, map from phase status
        phases = state.get("phases", {})
        if phases.get("build", {}).get("status") == "in_progress":
            status = "active"

    # Phase history
    if is_v2:
        phase_history = state.get("phase_history", {})
    else:
        # v1: construct from phases
        phases = state.get("phases", {})
        phase_history = {
            "spec_started_at": phases.get("spec", {}).get("started_at"),
            "spec_completed_at": phases.get("spec", {}).get("finalized_at"),
            "plan_started_at": phases.get("plan", {}).get("started_at"),
            "plan_completed_at": phases.get("plan", {}).get("finalized_at"),
            "build_started_at": phases.get("build", {}).get("started_at"),
            "build_completed_at": phases.get("build", {}).get("completed_at"),
            "docs_started_at": None,
            "docs_completed_at": None,
        }

    # Build progress
    if is_v2:
        build_progress = state.get("build_progress", {})
        checkpoints_total = build_progress.get("checkpoints_total") or 0
        checkpoints_completed_list = build_progress.get("checkpoints_completed") or []
        current_checkpoint = build_progress.get("current_checkpoint")
    else:
        # v1: use plan_state
        plan_state = state.get("plan_state", {})
        checkpoints_total = plan_state.get("checkpoints_total") or 0
        checkpoints_completed_list = plan_state.get("checkpoints_completed") or []
        current_checkpoint = plan_state.get("current_checkpoint")

    # Git context
    if is_v2:
        git = state.get("git", {})
        git_branch = git.get("branch")
        git_worktree = git.get("worktree")
        git_base_branch = git.get("base_branch")
    else:
        git_branch = None
        git_worktree = None
        git_base_branch = None

    # Commits
    if is_v2:
        commits_list = state.get("commits", [])
    else:
        # v1: commits array exists but with checkpoint_id instead of checkpoint
        raw_commits = state.get("commits", [])
        commits_list = [
            {
                "sha": c.get("sha"),
                "message": c.get("message"),
                "checkpoint": c.get("checkpoint_id") or c.get("checkpoint"),
                "created_at": c.get("created_at"),
            }
            for c in raw_commits
        ]

    # Artifacts
    artifacts = state.get(
        "artifacts",
        {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
    )

    # Session type
    session_type = state.get("session_type", state.get("granularity", "full"))

    return SessionCreate(
        session_slug=session_slug,
        title=state.get("topic"),
        description=state.get("description"),
        session_type=session_type,
        working_dir=working_dir,
        session_dir=session_dir,
        project_id=project_id,
        # Git context
        git_branch=git_branch,
        git_worktree=git_worktree,
        git_base_branch=git_base_branch,
        # Phase tracking
        current_phase=current_phase,
        status=status,
        phase_history=phase_history,
        # Build progress
        checkpoints_total=checkpoints_total,
        checkpoints_completed_list=checkpoints_completed_list,
        current_checkpoint=current_checkpoint,
        # Commits and artifacts
        commits_list=commits_list,
        artifacts=artifacts,
        # Metadata - no longer includes goals/questions (those are in spec.md now)
        metadata_={},
    )


def map_state_to_session_update(
    state: dict[str, Any],
    session_dir: str,
) -> SessionUpdate:
    """
    Map state.json v2 fields to SessionUpdate DTO for upsert.

    Args:
        state: Parsed state.json content
        session_dir: Absolute path to session folder

    Returns:
        SessionUpdate DTO for updating existing session
    """
    session_dir_path = Path(session_dir)

    # Detect schema version
    is_v2 = "phase_history" in state or "build_progress" in state

    # Current phase
    current_phase = state.get("current_phase", "spec")

    # Status
    status = state.get("status", "active")

    # Phase history
    if is_v2:
        phase_history = state.get("phase_history", {})
    else:
        phases = state.get("phases", {})
        phase_history = {
            "spec_started_at": phases.get("spec", {}).get("started_at"),
            "spec_completed_at": phases.get("spec", {}).get("finalized_at"),
            "plan_started_at": phases.get("plan", {}).get("started_at"),
            "plan_completed_at": phases.get("plan", {}).get("finalized_at"),
            "build_started_at": phases.get("build", {}).get("started_at"),
            "build_completed_at": phases.get("build", {}).get("completed_at"),
            "docs_started_at": None,
            "docs_completed_at": None,
        }

    # Build progress
    if is_v2:
        build_progress = state.get("build_progress", {})
        checkpoints_total = build_progress.get("checkpoints_total", 0)
        checkpoints_completed_list = build_progress.get("checkpoints_completed", [])
        current_checkpoint = build_progress.get("current_checkpoint")
    else:
        plan_state = state.get("plan_state", {})
        checkpoints_total = plan_state.get("checkpoints_total", 0)
        checkpoints_completed_list = plan_state.get("checkpoints_completed", [])
        current_checkpoint = plan_state.get("current_checkpoint")

    # Git context
    if is_v2:
        git = state.get("git", {})
        git_branch = git.get("branch")
        git_worktree = git.get("worktree")
        git_base_branch = git.get("base_branch")
    else:
        git_branch = None
        git_worktree = None
        git_base_branch = None

    # Commits
    if is_v2:
        commits_list = state.get("commits", [])
    else:
        raw_commits = state.get("commits", [])
        commits_list = [
            {
                "sha": c.get("sha"),
                "message": c.get("message"),
                "checkpoint": c.get("checkpoint_id") or c.get("checkpoint"),
                "created_at": c.get("created_at"),
            }
            for c in raw_commits
        ]

    # Artifacts
    artifacts = state.get(
        "artifacts",
        {
            "spec": "spec.md",
            "plan": "plan.json",
            "plan_readable": "plan.md",
        },
    )

    return SessionUpdate(
        title=state.get("topic"),
        description=state.get("description"),
        current_phase=current_phase,
        status=status,
        # Git context
        git_branch=git_branch,
        git_worktree=git_worktree,
        git_base_branch=git_base_branch,
        # Artifact status
        spec_exists=(session_dir_path / "spec.md").exists(),
        plan_exists=(session_dir_path / "plan.json").exists(),
        # Build progress
        checkpoints_total=checkpoints_total,
        checkpoints_completed=len(checkpoints_completed_list),
        checkpoints_completed_list=checkpoints_completed_list,
        current_checkpoint=current_checkpoint,
        # Phase history
        phase_history=phase_history,
        # Commits and artifacts
        commits_list=commits_list,
        artifacts=artifacts,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


async def sync_session_from_filesystem(
    db: AsyncSession,
    working_dir: str,
    session_slug: str,
    project_id: UUID | None = None,
) -> Session:
    """
    Read state.json and upsert to database.

    Filesystem is source of truth - database is updated to match.
    Creates a new session if it doesn't exist, updates if it does.

    Args:
        db: Database session
        working_dir: Absolute path to project root
        session_slug: Session folder name (e.g., '2026-02-14_feature-name')
        project_id: Optional project UUID to associate

    Returns:
        The created or updated Session

    Raises:
        SessionNotFoundOnFilesystem: If state.json doesn't exist
        InvalidStateJson: If state.json cannot be parsed
    """
    session_dir = Path(working_dir) / "agents/sessions" / session_slug
    state_path = session_dir / "state.json"

    if not state_path.exists():
        raise SessionNotFoundOnFilesystem(session_slug, state_path)

    try:
        state = json.loads(state_path.read_text())
    except json.JSONDecodeError as e:
        raise InvalidStateJson(session_slug, str(e))

    # Check if session already exists
    existing = await get_session_by_slug(db, session_slug)

    if existing:
        # Update existing session
        update_data = map_state_to_session_update(state, str(session_dir))
        # Also update project_id if provided
        if project_id:
            update_data.project_id = project_id
        session = await update_session(db, existing.id, update_data)
        return session
    else:
        # Create new session
        create_data = map_state_to_session_create(
            state=state,
            session_slug=session_slug,
            working_dir=working_dir,
            session_dir=str(session_dir),
            project_id=project_id,
        )
        # Set session_dir explicitly (not in DTO but needed)
        session = await create_session(db, create_data)
        # Update session_dir and artifact status
        await update_session(
            db,
            session.id,
            SessionUpdate(
                spec_exists=(session_dir / "spec.md").exists(),
                plan_exists=(session_dir / "plan.json").exists(),
            ),
        )
        # Refresh to get updated values
        await db.refresh(session)
        return session


async def onboard_project_sessions(
    db: AsyncSession,
    working_dir: str,
    project_id: UUID,
) -> list[Session]:
    """
    Scan agents/sessions/ directory and sync all sessions to database.

    Args:
        db: Database session
        working_dir: Absolute path to project root
        project_id: Project UUID to associate with sessions

    Returns:
        List of synced Session objects
    """
    sessions_dir = Path(working_dir) / "agents/sessions"

    if not sessions_dir.exists():
        return []

    synced_sessions = []

    # Iterate over session directories
    for session_path in sessions_dir.iterdir():
        if not session_path.is_dir():
            continue

        state_path = session_path / "state.json"
        if not state_path.exists():
            continue

        session_slug = session_path.name

        try:
            session = await sync_session_from_filesystem(
                db=db,
                working_dir=working_dir,
                session_slug=session_slug,
                project_id=project_id,
            )
            synced_sessions.append(session)
        except (SessionNotFoundOnFilesystem, InvalidStateJson):
            # Skip invalid sessions, log warning in production
            continue

    return synced_sessions


async def sync_all_sessions_in_project(
    db: AsyncSession,
    working_dir: str,
    project_id: UUID | None = None,
) -> dict[str, Any]:
    """
    Sync all sessions in a project directory.

    Returns a summary of the sync operation including successes and failures.

    Args:
        db: Database session
        working_dir: Absolute path to project root
        project_id: Optional project UUID

    Returns:
        Dict with sync results: {synced: [...], failed: [...], total: int}
    """
    sessions_dir = Path(working_dir) / "agents/sessions"

    if not sessions_dir.exists():
        return {"synced": [], "failed": [], "total": 0}

    synced = []
    failed = []

    for session_path in sessions_dir.iterdir():
        if not session_path.is_dir():
            continue

        session_slug = session_path.name
        state_path = session_path / "state.json"

        # Count directories without state.json as failed
        if not state_path.exists():
            failed.append(
                {
                    "session_slug": session_slug,
                    "error": "state.json not found",
                    "path": str(state_path),
                }
            )
            continue

        try:
            session = await sync_session_from_filesystem(
                db=db,
                working_dir=working_dir,
                session_slug=session_slug,
                project_id=project_id,
            )
            synced.append(
                {
                    "session_slug": session_slug,
                    "id": str(session.id),
                    "current_phase": session.current_phase,
                    "status": session.status,
                }
            )
        except SessionNotFoundOnFilesystem as e:
            failed.append(
                {
                    "session_slug": session_slug,
                    "error": "state.json not found",
                    "path": str(e.path),
                }
            )
        except InvalidStateJson as e:
            failed.append(
                {
                    "session_slug": session_slug,
                    "error": "invalid state.json",
                    "details": e.error,
                }
            )
        except Exception as e:
            failed.append(
                {
                    "session_slug": session_slug,
                    "error": "unexpected error",
                    "details": str(e),
                }
            )

    return {
        "synced": synced,
        "failed": failed,
        "total": len(synced) + len(failed),
    }
