"""
LAI Session Manager API

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from session_db.database import init_db, close_db

from .routers import projects, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    - On startup: Initialize database connection and create tables
    - On shutdown: Close database connections
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="LAI Session Manager",
    description="REST API for managing projects, sessions, and agent workflows",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(projects.router)
app.include_router(sessions.router)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Health check endpoint for deployment verification.

    Returns status: healthy if the API is running.
    """
    return {"status": "healthy"}
