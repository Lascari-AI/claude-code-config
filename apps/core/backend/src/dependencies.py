"""
FastAPI Dependencies

Provides dependency injection functions for database sessions
and other common dependencies across routes.
"""

from typing import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from database.connection import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Yields an async database session and ensures proper cleanup.
    Use with FastAPI's Depends():

        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with get_async_session() as session:
        yield session
