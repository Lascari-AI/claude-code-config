#!/usr/bin/env python3
"""
Orchestrator 3 Stream Backend
FastAPI server for managing orchestrator agent workflows with PostgreSQL backend
"""

import argparse
import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import our custom modules
from modules import config, database
from modules.agent_manager import AgentManager
from modules.autocomplete_models import (
    AutocompleteGenerateRequest,
    AutocompleteResponse,
    AutocompleteUpdateRequest,
)
from modules.autocomplete_service import AutocompleteService
from modules.logger import get_logger
from modules.orch_database_models import OrchestratorAgent
from modules.orchestrator_service import OrchestratorService, get_orchestrator_tools
from modules.websocket_manager import get_websocket_manager
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

logger = get_logger()
ws_manager = get_websocket_manager()
console = Console()  # For startup table display only

# Parse CLI arguments before creating app
parser = argparse.ArgumentParser(description="Orchestrator 3 Stream Backend")
parser.add_argument(
    "--session", type=str, help="Resume existing orchestrator session (session ID)"
)
parser.add_argument(
    "--cwd", type=str, help="Set working directory for orchestrator and agents"
)
args, unknown = parser.parse_known_args()

# Store parsed args for lifespan
CLI_SESSION_ID = args.session
CLI_WORKING_DIR = args.cwd

# Set working directory (use CLI arg or default from config)
if CLI_WORKING_DIR:
    config.set_working_dir(CLI_WORKING_DIR)
else:
    # Use default from ORCHESTRATOR_WORKING_DIR env var or config
    logger.info(f"Using default working directory: {config.get_working_dir()}")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.startup(
        {
            "Service": "Orchestrator 3 Stream Backend",
            "Description": "PostgreSQL-backed multi-agent orchestration",
            "Backend URL": config.BACKEND_URL,
            "WebSocket URL": config.WEBSOCKET_URL,
            "Database": "PostgreSQL (NeonDB)",
            "Logs Directory": str(config.LOG_DIR),
            "Working Directory": config.get_working_dir(),
        }
    )

    # Initialize database connection pool
    logger.info("Initializing database connection pool...")
    await database.init_pool(database_url=config.DATABASE_URL)
    logger.success("Database connection pool initialized")

    # Validate or load orchestrator
    if CLI_SESSION_ID:
        logger.info(f"Looking up orchestrator with session: {CLI_SESSION_ID}")
        orchestrator_data = await database.get_orchestrator_by_session(CLI_SESSION_ID)

        if not orchestrator_data:
            logger.error(f"❌ Session ID not found: {CLI_SESSION_ID}")
            logger.info("Checking if this is a legacy session or orchestrator ID...")

            # Try to find any orchestrator for debugging
            all_orchestrators = await database.get_orchestrator()
            if all_orchestrators:
                logger.info(f"Found orchestrator in database:")
                logger.info(f"  ID: {all_orchestrators.get('id')}")
                logger.info(f"  Session ID: {all_orchestrators.get('session_id')}")
                logger.info(f"\nTo resume, use: --session {all_orchestrators.get('session_id')}")

            raise ValueError(
                f"Session ID '{CLI_SESSION_ID}' not found in orchestrator_agents.session_id.\n\n"
                f"This usually happens when:\n"
                f"  1. The session_id has not been set yet (run without --session first)\n"
                f"  2. Database tables were recreated (data loss)\n"
                f"  3. Session ID was mistyped\n\n"
                f"Solution: Remove the --session argument to start a fresh session."
            )

        # Parse to Pydantic model
        orchestrator = OrchestratorAgent(**orchestrator_data)
        logger.success(f"✅ Resumed orchestrator with session: {CLI_SESSION_ID}")
        logger.info(f"  Orchestrator ID: {orchestrator.id}")
        logger.info(
            f"  Total tokens: {orchestrator.input_tokens + orchestrator.output_tokens}"
        )
        logger.info(f"  Total cost: ${orchestrator.total_cost:.4f}")
    else:
        # No --session provided: Always create new orchestrator
        logger.info("Creating new orchestrator session...")

        # Read system prompt from file
        system_prompt_content = Path(config.ORCHESTRATOR_SYSTEM_PROMPT_PATH).read_text()

        orchestrator_data = await database.create_new_orchestrator(
            system_prompt=system_prompt_content,
            working_dir=config.get_working_dir(),
        )
        # Parse to Pydantic model
        orchestrator = OrchestratorAgent(**orchestrator_data)
        logger.success(f"✅ New orchestrator created: {orchestrator.id}")
        logger.info(f"  Session ID: {orchestrator.session_id or 'Not set yet (will be set after first interaction)'}")
        logger.info(f"  Status: {orchestrator.status}")

    # Initialize agent manager (scoped to this orchestrator)
    logger.info("Initializing agent manager...")
    agent_manager = AgentManager(
        orchestrator_agent_id=orchestrator.id,
        ws_manager=ws_manager,
        logger=logger,
        working_dir=config.get_working_dir()
    )
    logger.success(f"Agent manager initialized for orchestrator {orchestrator.id}")

    # Initialize orchestrator service with agent manager
    logger.info("Initializing orchestrator service...")
    orchestrator_service = OrchestratorService(
        ws_manager=ws_manager,
        logger=logger,
        agent_manager=agent_manager,
        session_id=CLI_SESSION_ID or orchestrator.session_id,
        working_dir=config.get_working_dir(),
    )

    # Store in app state for access in endpoints
    app.state.orchestrator_service = orchestrator_service
    app.state.orchestrator = orchestrator

    # Initialize autocomplete service
    logger.info("Initializing autocomplete service...")
    autocomplete_service = AutocompleteService(
        orchestrator_agent_id=orchestrator.id,
        logger=logger,
        working_dir=config.get_working_dir(),
        ws_manager=ws_manager
    )
    app.state.autocomplete_service = autocomplete_service
    logger.success("Autocomplete service initialized")

    logger.success("Backend initialization complete")

    yield  # Server runs

    # Shutdown
    logger.info("Closing database connection pool...")
    await database.close_pool()
    logger.shutdown()


# Create FastAPI app with lifespan
app = FastAPI(title="Orchestrator 3 Stream API", version="1.0.0", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,  # From .env configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════


class LoadChatRequest(BaseModel):
    """Request model for loading chat history"""

    orchestrator_agent_id: str
    limit: Optional[int] = 50


class SendChatRequest(BaseModel):
    """Request model for sending chat message"""

    message: str
    orchestrator_agent_id: str


# ═══════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.http_request("GET", "/health", 200)
    return {
        "status": "healthy",
        "service": "orchestrator-3-stream",
        "websocket_connections": ws_manager.get_connection_count(),
    }


@app.get("/get_orchestrator")
async def get_orchestrator_info():
    """
    Get orchestrator agent information including system metadata.

    Fetches fresh data from database to ensure session_id is always current.
    Returns orchestrator ID, session, costs, metadata, slash commands, and templates.
    """
    try:
        logger.http_request("GET", "/get_orchestrator")

        # Refresh orchestrator from database to get current session_id
        orchestrator_id = app.state.orchestrator.id
        orchestrator_data = await database.get_orchestrator_by_id(orchestrator_id)

        if not orchestrator_data:
            logger.error(f"Orchestrator not found in database: {orchestrator_id}")
            raise HTTPException(status_code=404, detail="Orchestrator not found")

        # Update app.state with fresh data (keeps in-memory cache synchronized)
        orchestrator = OrchestratorAgent(**orchestrator_data)
        app.state.orchestrator = orchestrator

        # Discover slash commands
        slash_commands = discover_slash_commands(config.get_working_dir())

        # Get agent templates from SubagentRegistry
        from modules.subagent_loader import SubagentRegistry
        registry = SubagentRegistry(config.get_working_dir(), logger)
        templates = registry.list_templates()

        # Get orchestrator tools
        orchestrator_tools = get_orchestrator_tools()

        # Get available ADW workflow types
        adw_workflows = discover_adw_workflows(config.get_working_dir())

        # Prepare metadata with fallback for system_message_info
        metadata = orchestrator.metadata or {}

        # If system_message_info doesn't exist, create fallback from current state
        if not metadata.get("system_message_info"):
            metadata["system_message_info"] = {
                "session_id": orchestrator.session_id,
                "cwd": orchestrator.working_dir or config.get_working_dir(),
                "captured_at": None,  # Indicates this is fallback data
                "subtype": "fallback"  # Indicates this wasn't from a SystemMessage
            }

        logger.http_request("GET", "/get_orchestrator", 200)
        return {
            "status": "success",
            "orchestrator": {
                "id": str(orchestrator.id),
                "session_id": orchestrator.session_id,
                "status": orchestrator.status,
                "working_dir": orchestrator.working_dir,
                "input_tokens": orchestrator.input_tokens,
                "output_tokens": orchestrator.output_tokens,
                "total_cost": float(orchestrator.total_cost),
                "metadata": metadata,  # Include metadata with fallback
            },
            "slash_commands": slash_commands,  # List of available commands
            "agent_templates": templates,      # List of available templates
            "orchestrator_tools": orchestrator_tools,  # List of management tools
            "adw_workflows": adw_workflows,    # List of available ADW workflow types
        }
    except Exception as e:
        logger.error(f"Failed to get orchestrator info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_headers")
async def get_headers():
    """
    Get header information for the frontend.

    Returns:
        - cwd: Current working directory for orchestrator and agents
    """
    try:
        logger.http_request("GET", "/get_headers")

        cwd = config.get_working_dir()

        logger.http_request("GET", "/get_headers", 200)
        return {"status": "success", "cwd": cwd}
    except Exception as e:
        logger.error(f"Failed to get headers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# SLASH COMMAND DISCOVERY
# ═══════════════════════════════════════════════════════════

# Import slash command discovery from parser module
from modules.slash_command_parser import discover_slash_commands

# ═══════════════════════════════════════════════════════════
# ADW WORKFLOW DISCOVERY
# ═══════════════════════════════════════════════════════════

def discover_adw_workflows(working_dir: str) -> List[dict]:
    """
    Discover available ADW workflow types from adws/adw_workflows/*.py files.

    Args:
        working_dir: Working directory (project root)

    Returns:
        List of dicts with workflow type name and description
    """
    workflow_dir = Path(working_dir) / "adws" / "adw_workflows"
    if not workflow_dir.exists():
        return []

    workflows = []
    for file in workflow_dir.glob("adw_*.py"):
        # Extract type from filename: adw_plan_build.py -> plan_build
        name = file.stem  # adw_plan_build
        if name.startswith("adw_"):
            workflow_type = name[4:]  # Remove "adw_" prefix

            # Try to extract description from docstring
            description = f"ADW workflow: {workflow_type.replace('_', ' ')}"
            try:
                content = file.read_text(encoding='utf-8')
                # Look for module docstring
                if '"""' in content:
                    start = content.index('"""') + 3
                    end = content.index('"""', start)
                    doc = content[start:end].strip()
                    # Get first line of docstring
                    first_line = doc.split('\n')[0].strip()
                    if first_line and len(first_line) < 200:
                        description = first_line
            except Exception:
                pass

            workflows.append({
                "type": workflow_type,
                "display_name": workflow_type.replace("_", "-"),
                "description": description,
            })

    return sorted(workflows, key=lambda x: x["type"])


class OpenFileRequest(BaseModel):
    """Request model for opening a file in IDE"""
    file_path: str


@app.post("/api/open-file")
async def open_file_in_ide(request: OpenFileRequest):
    """
    Open a file in the configured IDE (Cursor or VS Code).

    Opens the file using the IDE command specified in config.IDE_COMMAND.
    """
    try:
        import subprocess

        logger.http_request("POST", "/api/open-file")

        if not config.IDE_ENABLED:
            logger.http_request("POST", "/api/open-file", 403)
            return {
                "status": "error",
                "message": "IDE integration is disabled in configuration"
            }

        file_path = request.file_path

        # Validate file exists
        if not os.path.exists(file_path):
            logger.http_request("POST", "/api/open-file", 404)
            return {"status": "error", "message": f"File not found: {file_path}"}

        # Build IDE command
        ide_cmd = config.IDE_COMMAND
        full_command = [ide_cmd, file_path]

        logger.info(f"Opening file in {ide_cmd}: {file_path}")

        # Execute IDE command
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            logger.http_request("POST", "/api/open-file", 200)
            return {
                "status": "success",
                "message": f"Opened {file_path} in {ide_cmd}",
                "file_path": file_path
            }
        else:
            logger.error(f"Failed to open file in IDE: {result.stderr}")
            logger.http_request("POST", "/api/open-file", 500)
            return {
                "status": "error",
                "message": f"Failed to open file in IDE: {result.stderr}"
            }

    except subprocess.TimeoutExpired:
        logger.error("IDE command timed out")
        logger.http_request("POST", "/api/open-file", 500)
        return {"status": "error", "message": "IDE command timed out"}
    except FileNotFoundError:
        logger.error(f"IDE command not found: {config.IDE_COMMAND}")
        logger.http_request("POST", "/api/open-file", 500)
        return {
            "status": "error",
            "message": f"IDE command not found: {config.IDE_COMMAND}. Please ensure it's installed and in PATH."
        }
    except Exception as e:
        logger.error(f"Failed to open file in IDE: {e}")
        logger.http_request("POST", "/api/open-file", 500)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_chat")
async def load_chat(request: LoadChatRequest):
    """
    Load chat history for orchestrator agent.

    Returns:
        - messages: List of chat messages
        - turn_count: Total number of messages
    """
    try:
        logger.http_request("POST", "/load_chat")

        service: OrchestratorService = app.state.orchestrator_service
        result = await service.load_chat_history(
            orchestrator_agent_id=request.orchestrator_agent_id, limit=request.limit
        )

        logger.http_request("POST", "/load_chat", 200)
        return {
            "status": "success",
            "messages": result["messages"],
            "turn_count": result["turn_count"],
        }

    except Exception as e:
        logger.error(f"Failed to load chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_chat")
async def send_chat(request: SendChatRequest):
    """
    Send message to orchestrator agent.

    Message is processed with streaming via WebSocket.
    This endpoint returns immediately after starting execution.

    Returns:
        - status: success/error
        - message: Confirmation message
    """
    try:
        logger.http_request("POST", "/send_chat")

        service: OrchestratorService = app.state.orchestrator_service

        # Process message asynchronously (streaming via WebSocket)
        asyncio.create_task(
            service.process_user_message(
                user_message=request.message,
                orchestrator_agent_id=request.orchestrator_agent_id,
            )
        )

        logger.http_request("POST", "/send_chat", 200)
        return {
            "status": "success",
            "message": "Message received, processing with streaming",
        }

    except Exception as e:
        logger.error(f"Failed to send chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_events")
async def get_events_endpoint(
    agent_id: Optional[str] = None,
    task_slug: Optional[str] = None,
    event_types: str = "all",
    limit: int = 50,
    offset: int = 0,
):
    """
    Get events from all sources for EventStream component.

    Query params:
        - agent_id: Optional filter by agent UUID
        - task_slug: Optional filter by task
        - event_types: Comma-separated list or "all" (default: "all")
        - limit: Max events to return (default 50)
        - offset: Pagination offset (default 0)

    Returns:
        - status: success/error
        - events: List of unified events with sourceType field
        - count: Total event count
    """
    try:
        logger.http_request("GET", "/get_events")

        # Parse event types (default: agent_logs and orchestrator_chat only, no system_logs)
        requested_types = (
            event_types.split(",")
            if event_types != "all"
            else ["agent_logs", "orchestrator_chat"]
        )

        all_events = []

        # Fetch agent logs
        if "agent_logs" in requested_types:
            agent_uuid = uuid.UUID(agent_id) if agent_id else None
            if agent_uuid:
                agent_logs = await database.get_agent_logs(
                    agent_id=agent_uuid, task_slug=task_slug, limit=limit, offset=offset
                )
            else:
                agent_logs = await database.list_agent_logs(
                    orchestrator_agent_id=app.state.orchestrator.id,
                    limit=limit,
                    offset=offset
                )

            # Add sourceType field
            for log in agent_logs:
                log["sourceType"] = "agent_log"
                all_events.append(log)

        # Fetch system logs
        if "system_logs" in requested_types:
            system_logs = await database.list_system_logs(limit=limit, offset=offset)
            for log in system_logs:
                log["sourceType"] = "system_log"
                all_events.append(log)

        # Fetch orchestrator chat (filtered by current orchestrator)
        if "orchestrator_chat" in requested_types:
            chat_logs = await database.list_orchestrator_chat(
                orchestrator_agent_id=app.state.orchestrator.id,
                limit=limit,
                offset=offset
            )
            for log in chat_logs:
                log["sourceType"] = "orchestrator_chat"
                all_events.append(log)

        # Sort by timestamp (newest first for limiting)
        all_events.sort(
            key=lambda x: x.get("timestamp") or x.get("created_at"), reverse=True
        )

        # Apply limit to get most recent events
        all_events = all_events[:limit]

        # Reverse to show oldest at top, newest at bottom
        all_events.reverse()

        # Convert UUIDs and datetimes to strings for JSON
        for event in all_events:
            for key, value in list(event.items()):
                if isinstance(value, uuid.UUID):
                    event[key] = str(value)
                elif hasattr(value, "isoformat"):
                    event[key] = value.isoformat()

        logger.http_request("GET", "/get_events", 200)
        return {"status": "success", "events": all_events, "count": len(all_events)}

    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list_agents")
async def list_agents_endpoint():
    """
    List all active agents for sidebar display.

    Returns:
        - status: success/error
        - agents: List of agent objects enriched with log_count from agent_logs table
    """
    try:
        logger.http_request("GET", "/list_agents")

        agents = await database.list_agents(
            orchestrator_agent_id=app.state.orchestrator.id,
            archived=False
        )

        # Serialize Pydantic models to dicts
        agents_data = [agent.model_dump() for agent in agents]

        # Enrich each agent with log count from agent_logs table
        async with database.get_connection() as conn:
            for agent_data in agents_data:
                agent_id = agent_data["id"]

                # Count logs for this agent from agent_logs table
                log_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM agent_logs WHERE agent_id = $1", agent_id
                )
                agent_data["log_count"] = log_count or 0

        logger.http_request("GET", "/list_agents", 200)
        return {"status": "success", "agents": agents_data}

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/autocomplete-generate")
async def autocomplete_generate(request: AutocompleteGenerateRequest) -> AutocompleteResponse:
    """
    Generate autocomplete suggestions for user input.

    Args:
        request: AutocompleteGenerateRequest with user_input and orchestrator_agent_id

    Returns:
        AutocompleteResponse with list of autocomplete suggestions
    """
    try:
        logger.http_request("POST", "/autocomplete-generate")
        service: AutocompleteService = app.state.autocomplete_service
        response = await service.generate_autocomplete(
            user_input=request.user_input,
            orchestrator_agent_id=request.orchestrator_agent_id
        )
        logger.http_request("POST", "/autocomplete-generate", 200)
        return response
    except Exception as e:
        logger.error(f"Autocomplete generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/autocomplete-update")
async def autocomplete_update(request: AutocompleteUpdateRequest):
    """
    Update autocomplete completion history.

    Tracks whether user accepted an autocomplete suggestion or typed manually.
    This data is used to improve future autocomplete suggestions.

    Args:
        request: AutocompleteUpdateRequest with completion_type and related fields

    Returns:
        Success status
    """
    try:
        logger.http_request("POST", "/autocomplete-update")
        service: AutocompleteService = app.state.autocomplete_service
        await service.update_completion_history(
            orchestrator_agent_id=request.orchestrator_agent_id,
            completion_type=request.completion_type,
            user_input_on_enter=request.user_input_on_enter,
            user_input_before_completion=request.user_input_before_completion,
            autocomplete_item=request.autocomplete_item,
            reasoning=request.reasoning
        )
        logger.http_request("POST", "/autocomplete-update", 200)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Autocomplete update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates and chat messages"""

    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()

            # Log received message
            if data:
                logger.debug(f"📥 Received WebSocket message: {data[:100]}")

                # Try to parse as JSON for structured messages
                try:
                    message = json.loads(data)

                    # Route message based on type
                    if isinstance(message, dict) and "type" in message:
                        msg_type = message.get("type")

                        # Handle ADW broadcast requests from workflow processes
                        if msg_type == "adw_broadcast":
                            broadcast_type = message.get("broadcast_type")
                            logger.debug(f"ADW broadcast request: {broadcast_type}")

                            if broadcast_type == "adw_created":
                                await ws_manager.broadcast_adw_created(
                                    message.get("adw", {})
                                )
                            elif broadcast_type == "adw_updated":
                                await ws_manager.broadcast_adw_updated(
                                    message.get("adw_id", ""),
                                    message.get("adw", {})
                                )
                            elif broadcast_type == "adw_event":
                                await ws_manager.broadcast_adw_event(
                                    message.get("adw_id", ""),
                                    message.get("event", {})
                                )
                            elif broadcast_type == "adw_step_change":
                                await ws_manager.broadcast_adw_step_change(
                                    message.get("adw_id", ""),
                                    message.get("step", ""),
                                    message.get("event_type", ""),
                                    message.get("payload")
                                )
                            elif broadcast_type == "adw_status":
                                # Broadcast status as an adw_updated event
                                await ws_manager.broadcast_adw_updated(
                                    message.get("adw_id", ""),
                                    {
                                        "status": message.get("status"),
                                        "current_step": message.get("current_step"),
                                        "completed_steps": message.get("completed_steps"),
                                        "error_message": message.get("error_message"),
                                    }
                                )
                            elif broadcast_type == "adw_event_summary_update":
                                # Broadcast summary update for an existing ADW event
                                await ws_manager.broadcast_adw_event_summary_update(
                                    message.get("adw_id", ""),
                                    message.get("event_id", ""),
                                    message.get("summary", "")
                                )
                            else:
                                logger.warning(f"Unknown ADW broadcast type: {broadcast_type}")

                        # Handle agent broadcast requests from ADW workflow processes
                        elif msg_type == "agent_broadcast":
                            broadcast_type = message.get("broadcast_type")
                            logger.debug(f"Agent broadcast request: {broadcast_type}")

                            if broadcast_type == "agent_created":
                                await ws_manager.broadcast_agent_created(
                                    message.get("agent", {})
                                )
                            elif broadcast_type == "agent_status_changed":
                                await ws_manager.broadcast_agent_status_change(
                                    message.get("agent_id", ""),
                                    message.get("old_status", ""),
                                    message.get("new_status", "")
                                )
                            elif broadcast_type == "agent_updated":
                                await ws_manager.broadcast_agent_updated(
                                    message.get("agent_id", ""),
                                    message.get("agent", {})
                                )
                            else:
                                logger.warning(f"Unknown agent broadcast type: {broadcast_type}")
                        else:
                            # Log unknown message types for future event handlers
                            logger.debug(f"Received WebSocket message type: {msg_type}")

                except json.JSONDecodeError:
                    # Not JSON, treat as plain text (keep alive ping)
                    pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ════════════════════════════════════════════════════════════════════════════════
# AI Developer Workflow (ADW) Endpoints
# ════════════════════════════════════════════════════════════════════════════════


class ListAdwsRequest(BaseModel):
    """Request model for listing ADWs"""
    orchestrator_agent_id: str
    status: Optional[str] = None
    limit: Optional[int] = 20


class GetAdwEventsRequest(BaseModel):
    """Request model for getting ADW events"""
    adw_id: str
    limit: Optional[int] = 2000
    event_type: Optional[str] = None
    include_payload: Optional[bool] = True


@app.post("/adws")
async def list_adws(request: ListAdwsRequest):
    """
    List AI Developer Workflows for an orchestrator.

    Returns ADWs sorted by creation date (newest first).
    Optionally filter by status (pending, in_progress, completed, failed, cancelled).
    """
    try:
        logger.http_request("POST", "/adws")

        orchestrator_id = uuid.UUID(request.orchestrator_agent_id)
        adws = await database.list_adws(
            orchestrator_agent_id=orchestrator_id,
            status=request.status,
            limit=request.limit,
        )

        # Serialize UUIDs and datetimes
        for adw in adws:
            for key, value in adw.items():
                if isinstance(value, uuid.UUID):
                    adw[key] = str(value)
                elif hasattr(value, 'isoformat'):
                    adw[key] = value.isoformat()

        logger.http_request("POST", "/adws", 200)
        return {"status": "success", "adws": adws, "count": len(adws)}

    except Exception as e:
        logger.error(f"Failed to list ADWs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/adws/{adw_id}")
async def get_adw(adw_id: str):
    """
    Get a single ADW by ID with full status details.

    Returns the complete ADW record including:
    - Status and progress (current_step, completed_steps, total_steps)
    - Timing (started_at, completed_at, duration_seconds)
    - Error info (error_message, error_step) if failed
    - Input/output data
    """
    try:
        logger.http_request("GET", f"/adws/{adw_id}")

        adw = await database.get_adw(uuid.UUID(adw_id))

        if not adw:
            raise HTTPException(status_code=404, detail=f"ADW not found: {adw_id}")

        # Serialize UUIDs and datetimes
        for key, value in adw.items():
            if isinstance(value, uuid.UUID):
                adw[key] = str(value)
            elif hasattr(value, 'isoformat'):
                adw[key] = value.isoformat()

        logger.http_request("GET", f"/adws/{adw_id}", 200)
        return {"status": "success", "adw": adw}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ADW {adw_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/adws/{adw_id}/events")
async def get_adw_events(adw_id: str, request: GetAdwEventsRequest):
    """
    Get events for an ADW (swimlane squares) from BOTH agent_logs AND system_logs.

    Returns events sorted by timestamp (oldest first) for swimlane rendering.
    Each event represents a square in the swimlane UI.

    Optionally filter by event_type:
    - StepStart, StepEnd: Step lifecycle markers
    - PostToolUse: Tool execution events
    - text, result: Response events
    - SystemInfo, SystemWarning, SystemError: System log events
    """
    try:
        logger.http_request("POST", f"/adws/{adw_id}/events")

        # Fetch from agent_logs
        agent_events = await database.get_adw_logs(
            adw_id=uuid.UUID(adw_id),
            limit=request.limit,
            event_type=request.event_type,
            include_payload=request.include_payload,
        )

        # Fetch from system_logs (no event_type filter - system logs have different types)
        system_events = await database.get_adw_system_logs(
            adw_id=uuid.UUID(adw_id),
            limit=request.limit,
            include_metadata=request.include_payload,
        )

        # Merge and sort by timestamp
        events = agent_events + system_events

        # Serialize UUIDs and datetimes
        for event in events:
            for key, value in event.items():
                if isinstance(value, uuid.UUID):
                    event[key] = str(value)
                elif hasattr(value, 'isoformat'):
                    event[key] = value.isoformat()

        # Sort by timestamp (oldest first)
        events.sort(key=lambda e: e.get("timestamp", ""))

        # Group events by adw_step for swimlane rendering
        steps: Dict[str, List[Dict]] = {}
        for event in events:
            step = event.get("adw_step") or "_workflow"
            if step not in steps:
                steps[step] = []
            steps[step].append(event)

        logger.http_request("POST", f"/adws/{adw_id}/events", 200)
        return {
            "status": "success",
            "adw_id": adw_id,
            "events": events,
            "events_by_step": steps,
            "count": len(events),
        }

    except Exception as e:
        logger.error(f"Failed to get ADW events for {adw_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/adws/{adw_id}/summary")
async def get_adw_summary(adw_id: str):
    """
    Get a summary of an ADW including status and step breakdown.

    Returns:
    - ADW basic info (name, type, status)
    - Step summary with event counts per step
    - Agent info for each step
    """
    try:
        logger.http_request("GET", f"/adws/{adw_id}/summary")

        # Get ADW record
        adw = await database.get_adw(uuid.UUID(adw_id))
        if not adw:
            raise HTTPException(status_code=404, detail=f"ADW not found: {adw_id}")

        # Get all events grouped by step
        events = await database.get_adw_logs(
            adw_id=uuid.UUID(adw_id),
            limit=500,
            include_payload=False,
        )

        # Build step summary
        step_summary: Dict[str, Dict] = {}
        for event in events:
            step = event.get("adw_step") or "_workflow"
            if step not in step_summary:
                step_summary[step] = {
                    "step": step,
                    "event_count": 0,
                    "event_types": {},
                    "agent_id": None,
                    "started_at": None,
                    "ended_at": None,
                }

            step_summary[step]["event_count"] += 1

            # Track event type counts
            event_type = event.get("event_type", "unknown")
            step_summary[step]["event_types"][event_type] = (
                step_summary[step]["event_types"].get(event_type, 0) + 1
            )

            # Track agent and timing
            if event.get("agent_id"):
                step_summary[step]["agent_id"] = str(event["agent_id"])
            if event_type == "StepStart":
                step_summary[step]["started_at"] = event.get("timestamp")
            if event_type == "StepEnd":
                step_summary[step]["ended_at"] = event.get("timestamp")

        # Serialize ADW
        for key, value in adw.items():
            if isinstance(value, uuid.UUID):
                adw[key] = str(value)
            elif hasattr(value, 'isoformat'):
                adw[key] = value.isoformat()

        logger.http_request("GET", f"/adws/{adw_id}/summary", 200)
        return {
            "status": "success",
            "adw": adw,
            "steps": list(step_summary.values()),
            "total_events": len(events),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ADW summary for {adw_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Display startup banner
    table = Table(
        title="Orchestrator 3 Stream Configuration",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Backend URL", config.BACKEND_URL)
    table.add_row("WebSocket URL", config.WEBSOCKET_URL)
    table.add_row("Database", "PostgreSQL (NeonDB)")

    console.print(table)

    # Run the server with config ports
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)
