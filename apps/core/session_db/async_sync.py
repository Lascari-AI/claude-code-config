"""
Async Sync Task Module

Provides fire-and-forget async functions for syncing sessions to the database.
These functions are designed to be called from StateManager callbacks without
blocking the main save operation.

Usage:
    from session_db.async_sync import make_sync_callback

    # Create a callback for StateManager
    callback = make_sync_callback(working_dir="/path/to/project")
    manager = SessionStateManager(session_dir, on_save_callback=callback)
"""

import asyncio
import logging
from pathlib import Path
from typing import Callable

from .database import get_async_session
from .sync import sync_session_from_filesystem

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC SYNC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


async def _sync_session_async(session_dir: Path, working_dir: str) -> None:
    """
    Async wrapper that gets db session and calls sync_session_from_filesystem.

    This is the actual async work that runs in the background task.
    """
    session_slug = session_dir.name

    try:
        async with get_async_session() as db:
            await sync_session_from_filesystem(db, working_dir, session_slug)
            logger.debug("Synced session %s to database", session_slug)
    except Exception as e:
        logger.exception("Failed to sync session %s: %s", session_slug, e)


def queue_sync_task(session_dir: Path, working_dir: str | None = None) -> None:
    """
    Queue an async task to sync the session to the database.

    Fire-and-forget: returns immediately, task runs in background.
    Errors are logged but not raised.

    Args:
        session_dir: Path to the session directory containing state.json
        working_dir: Project root directory. If not provided, derived from session_dir
            assuming standard structure: {working_dir}/agents/sessions/{slug}
    """
    if working_dir is None:
        # Derive from session_dir: go up 3 levels (slug -> sessions -> agents -> project)
        working_dir = str(session_dir.parent.parent.parent)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_sync_session_async(session_dir, working_dir))
    except RuntimeError:
        # No running event loop - log and skip
        logger.warning("No event loop available to sync session %s", session_dir.name)


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK FACTORY
# ═══════════════════════════════════════════════════════════════════════════════


def make_sync_callback(working_dir: str) -> Callable[[Path], None]:
    """
    Create a SaveCallback-compatible function for StateManager.

    Returns a callback that, when invoked with a session directory,
    queues an async task to sync that session to the database.

    Args:
        working_dir: Project root directory (absolute path)

    Returns:
        A callback function compatible with SessionStateManager.on_save_callback

    Example:
        callback = make_sync_callback("/path/to/project")
        manager = SessionStateManager(session_dir, on_save_callback=callback)
        manager.save()  # Triggers callback -> queues sync task
    """

    def callback(session_dir: Path) -> None:
        queue_sync_task(session_dir, working_dir)

    return callback


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH SYNC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


async def _batch_sync_async(working_dir: str, project_id: str | None = None) -> None:
    """
    Async wrapper for sync_all_sessions_in_project.

    This is the actual async work that runs in the background task.
    """
    from uuid import UUID

    from .sync import sync_all_sessions_in_project

    try:
        async with get_async_session() as db:
            pid = UUID(project_id) if project_id else None
            result = await sync_all_sessions_in_project(db, working_dir, pid)
            logger.info(
                "Batch sync complete for %s: %d synced, %d failed",
                working_dir,
                len(result["synced"]),
                len(result["failed"]),
            )
    except Exception as e:
        logger.exception("Failed to batch sync project %s: %s", working_dir, e)


def queue_batch_sync_task(working_dir: str, project_id: str | None = None) -> None:
    """
    Queue an async task to sync all sessions in a project.

    Fire-and-forget: returns immediately, task runs in background.
    Errors are logged but not raised.

    Args:
        working_dir: Project root directory (absolute path)
        project_id: Optional project UUID as string
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_batch_sync_async(working_dir, project_id))
    except RuntimeError:
        # No running event loop - log and skip
        logger.warning("No event loop available to batch sync %s", working_dir)
