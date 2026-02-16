"""
Pooled Sync Callbacks

Factory functions that create StateManager-compatible callbacks
which submit sync tasks to the background task pool.
"""

import logging
from pathlib import Path
from typing import Callable

from .task_pool import default_pool

# Import async sync functions from session_db
# Note: This creates a dependency on session_db package
import sys

logger = logging.getLogger(__name__)


async def _sync_session_to_db(session_dir: Path, working_dir: str) -> None:
    """
    Async function that syncs a session to the database.

    Uses the session_db sync infrastructure.
    """
    # Lazy import to avoid circular dependencies at module load time
    try:
        from session_db.async_sync import _sync_session_async
    except ImportError:
        # Fallback: try relative import path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "session_db"))
        from async_sync import _sync_session_async

    await _sync_session_async(session_dir, working_dir)


def make_pooled_sync_callback(working_dir: str) -> Callable[[Path], None]:
    """
    Create a StateManager callback that submits sync tasks to the pool.

    The returned callback, when invoked with a session directory, submits
    an async sync task to the default task pool. This is fire-and-forget:
    the callback returns immediately while sync happens in background.

    Args:
        working_dir: Project root directory (absolute path)

    Returns:
        A callback function compatible with SessionStateManager.on_save_callback

    Example:
        callback = make_pooled_sync_callback("/path/to/project")
        manager = SessionStateManager(session_dir, on_save_callback=callback)
        manager.save()  # Triggers callback -> submits to pool -> async sync
    """

    def callback(session_dir: Path) -> None:
        """Submit sync task to pool when StateManager saves."""
        logger.debug("Callback invoked for session %s, submitting to pool", session_dir.name)
        default_pool.submit(_sync_session_to_db(session_dir, working_dir))

    return callback
