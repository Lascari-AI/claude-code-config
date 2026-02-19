"""
Database Connection and Session Management

Provides async database engine and session factory for SQLModel operations.
Uses asyncpg for async PostgreSQL support.

Usage:
    from database.connection import get_engine, get_async_session, init_db

    # Initialize database (creates tables)
    await init_db()

    # Use session in async context
    async with get_async_session() as session:
        result = await session.exec(select(Session))
        sessions = result.all()
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import (  # noqa: F401 - needed for table creation
    Agent,
    AgentLog,
    InteractiveMessage,
    Project,
    Session,
)

# Load environment variables from .env file
# Use explicit path relative to this file (backend/.env)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_ENV_FILE)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Default PostgreSQL URL (can be overridden via environment variable)
DEFAULT_DB_URL = "postgresql+asyncpg://localhost/session_db"


def get_database_url() -> str:
    """
    Get the database URL from environment or use default.

    Environment variable: SESSION_DB_URL
    Default: postgresql+asyncpg://localhost/session_db
    """
    return os.environ.get("SESSION_DB_URL", DEFAULT_DB_URL)


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINE AND SESSION FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

_engine: AsyncEngine | None = None
_async_session_factory: sessionmaker | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.

    Returns a singleton engine instance.
    """
    global _engine

    if _engine is None:
        database_url = get_database_url()
        _engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            future=True,
        )

    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the async session factory.

    Returns a singleton session factory.
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_async_session() as session:
            result = await session.exec(select(Session))
            sessions = result.all()
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This is safe to call multiple times - it will only create
    tables that don't exist.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data!
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def reset_db() -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data!
    """
    await drop_db()
    await init_db()


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════


async def close_db() -> None:
    """
    Close the database engine and cleanup connections.

    Call this when shutting down the application.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
