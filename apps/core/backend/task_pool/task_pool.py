"""
Sync Task Pool

Manages a pool of background asyncio tasks with configurable concurrency limits.
Provides fire-and-forget task submission for database sync operations.
"""

import asyncio
import logging
from typing import Any, Coroutine, Set

logger = logging.getLogger(__name__)


class SyncTaskPool:
    """
    Manages a pool of background sync tasks with concurrency limiting.

    Tasks are fire-and-forget: errors are logged but don't propagate.
    Uses a semaphore to limit concurrent task execution.

    Example:
        pool = SyncTaskPool(max_concurrent=3)
        pool.submit(some_async_work())
        pool.submit(more_async_work())

        # Later, at shutdown:
        await pool.shutdown()
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        """
        Initialize the task pool.

        Args:
            max_concurrent: Maximum number of tasks that can run simultaneously.
                           Default is 5 to avoid overwhelming the database.
        """
        self._max_concurrent = max_concurrent
        self._semaphore: asyncio.Semaphore | None = None
        self._tasks: Set[asyncio.Task[Any]] = set()
        self._shutting_down = False

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create the semaphore (lazy initialization for event loop)."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    @property
    def active_count(self) -> int:
        """Return the number of currently running tasks."""
        return len([t for t in self._tasks if not t.done()])

    @property
    def pending_count(self) -> int:
        """Return the total number of tracked tasks (including waiting)."""
        return len(self._tasks)

    def submit(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any] | None:
        """
        Submit a coroutine to run in the background.

        Fire-and-forget: returns immediately, task runs asynchronously.
        If no event loop is running, logs a warning and returns None.
        If pool is shutting down, rejects the task.

        Args:
            coro: The coroutine to execute

        Returns:
            The created Task, or None if submission failed
        """
        if self._shutting_down:
            logger.warning("Task pool is shutting down, rejecting new task")
            coro.close()  # Properly close the unawaited coroutine
            return None

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("No event loop available, cannot submit task to pool")
            coro.close()
            return None

        async def _run_with_semaphore() -> Any:
            """Wrapper that acquires semaphore before running."""
            async with self._get_semaphore():
                try:
                    return await coro
                except Exception as e:
                    logger.exception("Background task failed: %s", e)
                    return None

        task = loop.create_task(_run_with_semaphore())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        logger.debug(
            "Submitted task to pool (active=%d, pending=%d)",
            self.active_count,
            self.pending_count,
        )

        return task

    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown the pool, waiting for running tasks.

        Args:
            timeout: Maximum seconds to wait for tasks to complete.
                    After timeout, remaining tasks are cancelled.
        """
        self._shutting_down = True

        if not self._tasks:
            logger.debug("Task pool shutdown: no pending tasks")
            return

        logger.info(
            "Task pool shutdown: waiting for %d tasks (timeout=%ds)",
            len(self._tasks),
            timeout,
        )

        # Wait for all tasks with timeout
        pending = list(self._tasks)
        done, not_done = await asyncio.wait(
            pending, timeout=timeout, return_when=asyncio.ALL_COMPLETED
        )

        # Cancel any tasks that didn't complete in time
        if not_done:
            logger.warning(
                "Task pool shutdown: cancelling %d tasks that didn't complete",
                len(not_done),
            )
            for task in not_done:
                task.cancel()

            # Wait briefly for cancellations to complete
            await asyncio.wait(not_done, timeout=5.0)

        logger.info("Task pool shutdown complete")

    def reset(self) -> None:
        """
        Reset the pool state after shutdown.

        Allows the pool to accept new tasks again.
        Should only be called after shutdown() completes.
        """
        self._shutting_down = False
        self._tasks.clear()
        self._semaphore = None


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

# Default pool with sensible concurrency limit
# Used by the backend for all sync operations
default_pool = SyncTaskPool(max_concurrent=5)
