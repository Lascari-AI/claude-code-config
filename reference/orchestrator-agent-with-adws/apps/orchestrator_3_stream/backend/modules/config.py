#!/usr/bin/env python3
"""
Configuration module for Orchestrator 3 Stream
Central location for application-wide settings and constants
Uses classic Python logging (not Rich) for configuration loading
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Set up classic Python logging for config loading
logging.basicConfig(
    level=logging.INFO, format="[CONFIG] %(levelname)s: %(message)s", force=True
)
config_logger = logging.getLogger(__name__)

# Get the project root (orchestrator_3_stream/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
    config_logger.info(f"Loaded environment variables from {ENV_FILE}")
else:
    config_logger.warning(f".env file not found at {ENV_FILE}, using defaults")
    load_dotenv()  # Try to load from current directory

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent.resolve()

# Default codebase path for agents to work within
DEFAULT_CODEBASE_PATH = str(BACKEND_DIR.parent.parent.parent)

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

# Backend Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "9403"))

# Frontend Configuration
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5175"))

# WebSocket Configuration
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws")

# Computed URLs
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/orchestrator")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = Path(os.getenv("LOG_DIR", "backend/logs"))

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
).split(",")

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Default model for agents (Opus is the primary model)
DEFAULT_MODEL = "claude-opus-4-5-20251101"

FAST_MODEL = "claude-haiku-4-5-20251001"

# Available models
AVAILABLE_MODELS = ["claude-opus-4-5-20251101", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"]

# ============================================================================
# ORCHESTRATOR CONFIGURATION
# ============================================================================

# Orchestrator agent model
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)

# Orchestrator system prompt path
ORCHESTRATOR_SYSTEM_PROMPT_PATH = os.getenv(
    "ORCHESTRATOR_SYSTEM_PROMPT_PATH",
    str(BACKEND_DIR / "prompts" / "orchestrator_agent_system_prompt.md"),
)

# Orchestrator working directory (can be overridden via --cwd CLI flag)
ORCHESTRATOR_WORKING_DIR = os.getenv("ORCHESTRATOR_WORKING_DIR", DEFAULT_CODEBASE_PATH)

# Current working directory (runtime override)
_current_working_dir = ORCHESTRATOR_WORKING_DIR


def set_working_dir(path: str) -> None:
    """
    Dynamically override the working directory at runtime.

    Used when --cwd CLI flag is provided to override default.

    Args:
        path: Absolute path to working directory
    """
    global _current_working_dir
    _current_working_dir = path
    config_logger.info(f"Working directory overridden: {path}")


def get_working_dir() -> str:
    """
    Get the current working directory.

    Returns:
        Current working directory path
    """
    return _current_working_dir


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Default model for managed agents
DEFAULT_AGENT_MODEL = os.getenv("DEFAULT_AGENT_MODEL", DEFAULT_MODEL)

# Agent system prompt template path
AGENT_SYSTEM_PROMPT_TEMPLATE_PATH = os.getenv(
    "AGENT_SYSTEM_PROMPT_TEMPLATE_PATH",
    str(BACKEND_DIR / "prompts" / "managed_agent_system_prompt_template.md"),
)

# Maximum turns for agent execution
MAX_AGENT_TURNS = int(os.getenv("MAX_AGENT_TURNS", "500"))

# ============================================================================
# LOG QUERY LIMITS
# ============================================================================

# Default limit for agent log queries
DEFAULT_AGENT_LOG_LIMIT = int(os.getenv("DEFAULT_AGENT_LOG_LIMIT", "50"))

# Default limit for system log queries
DEFAULT_SYSTEM_LOG_LIMIT = int(os.getenv("DEFAULT_SYSTEM_LOG_LIMIT", "50"))

# Default limit for chat history queries
DEFAULT_CHAT_HISTORY_LIMIT = int(os.getenv("DEFAULT_CHAT_HISTORY_LIMIT", "300"))

# ============================================================================
# IDE INTEGRATION CONFIGURATION
# ============================================================================

# IDE command for opening files (supports 'cursor' or 'code')
# Format: cursor {file} or code {file}
IDE_COMMAND = os.getenv("IDE_COMMAND", "code")
IDE_ENABLED = os.getenv("IDE_ENABLED", "true").lower() in ["true", "1", "yes"]

# ============================================================================
# STARTUP CONFIGURATION LOGGING
# ============================================================================

config_logger.info("=" * 70)
config_logger.info("ORCHESTRATOR 3 STREAM CONFIGURATION")
config_logger.info("=" * 70)
config_logger.info(f"Backend URL:     {BACKEND_URL}")
config_logger.info(f"Frontend URL:    {FRONTEND_URL}")
config_logger.info(f"WebSocket URL:   {WEBSOCKET_URL}")
config_logger.info(
    f"Database URL:    {DATABASE_URL[:40]}..."
    if len(DATABASE_URL) > 40
    else f"Database URL:    {DATABASE_URL}"
)
config_logger.info(f"Log Level:       {LOG_LEVEL}")
config_logger.info(f"Log Directory:   {LOG_DIR}")
config_logger.info(f"CORS Origins:    {', '.join(CORS_ORIGINS)}")
config_logger.info("=" * 70)
