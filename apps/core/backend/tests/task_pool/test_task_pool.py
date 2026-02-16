"""Tests for SyncTaskPool class.

Tests task submission, concurrency limits, and graceful shutdown.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from task_pool import SyncTaskPool


class TestSyncTaskPool:
    """Tests for SyncTaskPool class."""

    @pytest.fixture
    def pool(self) -> SyncTaskPool:
        """Create a fresh pool for each test."""
        return SyncTaskPool(max_concurrent=3)

    @pytest.mark.asyncio
    async def test_pool_submits_task(self, pool: SyncTaskPool) -> None:
        """submit() should create a task that runs the coroutine."""
        result = []

        async def work() -> None:
            result.append("done")

        task = pool.submit(work())
        assert task is not None

        # Wait for task to complete
        await task
        assert result == ["done"]

    @pytest.mark.asyncio
    async def test_pool_returns_task_result(self, pool: SyncTaskPool) -> None:
        """submitted coroutine's return value should be accessible via task."""

        async def work() -> int:
            return 42

        task = pool.submit(work())
        assert task is not None

        result = await task
        assert result == 42

    @pytest.mark.asyncio
    async def test_pool_limits_concurrency(self) -> None:
        """Only max_concurrent tasks should run simultaneously."""
        pool = SyncTaskPool(max_concurrent=2)
        concurrent_count = 0
        max_observed = 0
        results = []

        async def work(task_id: int) -> None:
            nonlocal concurrent_count, max_observed
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)

            # Simulate work
            await asyncio.sleep(0.05)
            results.append(task_id)

            concurrent_count -= 1

        # Submit more tasks than max_concurrent
        tasks = []
        for i in range(5):
            task = pool.submit(work(i))
            if task:
                tasks.append(task)

        # Wait for all tasks
        await asyncio.gather(*tasks)

        # Should never exceed max_concurrent
        assert max_observed <= 2
        # All tasks should complete
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_pool_tracks_active_count(self, pool: SyncTaskPool) -> None:
        """active_count property should reflect running tasks."""
        started = asyncio.Event()
        release = asyncio.Event()

        async def blocking_work() -> None:
            started.set()
            await release.wait()

        task = pool.submit(blocking_work())
        assert task is not None

        # Wait for task to start
        await started.wait()
        assert pool.active_count >= 1

        # Release and wait
        release.set()
        await task
        # Allow cleanup
        await asyncio.sleep(0.01)
        assert pool.active_count == 0

    @pytest.mark.asyncio
    async def test_pool_shutdown_waits_for_tasks(self, pool: SyncTaskPool) -> None:
        """shutdown() should wait for running tasks to complete."""
        completed = []

        async def work(task_id: int) -> None:
            await asyncio.sleep(0.05)
            completed.append(task_id)

        pool.submit(work(1))
        pool.submit(work(2))

        # Small delay to let tasks start
        await asyncio.sleep(0.01)

        # Shutdown should wait for completion
        await pool.shutdown(timeout=5.0)

        assert len(completed) == 2

    @pytest.mark.asyncio
    async def test_pool_shutdown_cancels_on_timeout(self) -> None:
        """shutdown() should cancel tasks that don't complete in time."""
        pool = SyncTaskPool(max_concurrent=1)
        cancelled = []

        async def long_work() -> None:
            try:
                await asyncio.sleep(10)  # Very long
            except asyncio.CancelledError:
                cancelled.append("cancelled")
                raise

        pool.submit(long_work())
        await asyncio.sleep(0.01)  # Let it start

        # Very short timeout
        await pool.shutdown(timeout=0.1)

        assert "cancelled" in cancelled

    @pytest.mark.asyncio
    async def test_pool_rejects_after_shutdown(self, pool: SyncTaskPool) -> None:
        """submit() should reject tasks after shutdown starts."""
        await pool.shutdown()

        async def work() -> None:
            pass

        task = pool.submit(work())
        assert task is None

    @pytest.mark.asyncio
    async def test_pool_reset_allows_reuse(self, pool: SyncTaskPool) -> None:
        """reset() should allow the pool to accept tasks again."""
        await pool.shutdown()

        # Can't submit after shutdown
        async def work1() -> int:
            return 1

        assert pool.submit(work1()) is None

        # Reset allows new submissions
        pool.reset()

        async def work2() -> int:
            return 2

        task = pool.submit(work2())
        assert task is not None
        result = await task
        assert result == 2

    @pytest.mark.asyncio
    async def test_pool_logs_task_exceptions(
        self, pool: SyncTaskPool, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Task exceptions should be logged but not propagate."""

        async def failing_work() -> None:
            raise ValueError("Task failed!")

        task = pool.submit(failing_work())
        assert task is not None

        # Task completes (with logged error), doesn't raise
        await task

        # Exception was logged
        assert "Task failed!" in caplog.text or "Background task failed" in caplog.text

    @pytest.mark.asyncio
    async def test_pool_pending_count(self, pool: SyncTaskPool) -> None:
        """pending_count should track all tasks including waiting ones."""
        started = asyncio.Event()
        release = asyncio.Event()

        async def blocking_work() -> None:
            started.set()
            await release.wait()

        task = pool.submit(blocking_work())
        assert task is not None

        await started.wait()
        assert pool.pending_count >= 1

        release.set()
        await task
        await asyncio.sleep(0.01)  # Allow cleanup
        assert pool.pending_count == 0


class TestDefaultPool:
    """Tests for the default_pool singleton."""

    def test_default_pool_exists(self) -> None:
        """default_pool should be available from module."""
        from task_pool import default_pool

        assert default_pool is not None
        assert isinstance(default_pool, SyncTaskPool)

    def test_default_pool_has_sensible_limit(self) -> None:
        """default_pool should have a reasonable concurrency limit."""
        from task_pool import default_pool

        # Should be between 1 and 20 (sensible range)
        assert 1 <= default_pool._max_concurrent <= 20
