"""
Task Pool Module

Provides background task management for non-blocking database sync operations.
Uses asyncio task management with configurable concurrency limits.

Usage:
    from task_pool import default_pool, SyncTaskPool, make_pooled_sync_callback

    # Use the default singleton pool
    default_pool.submit(some_coroutine())

    # Or create a custom pool
    pool = SyncTaskPool(max_concurrent=5)
    pool.submit(some_coroutine())

    # Create a callback for StateManager
    callback = make_pooled_sync_callback("/path/to/project")
"""

from .callbacks import make_pooled_sync_callback
from .task_pool import SyncTaskPool, default_pool

__all__ = ["SyncTaskPool", "default_pool", "make_pooled_sync_callback"]
