"""
Chat Router - Endpoints for interactive chat with Claude Agent SDK.

Provides the send-message endpoint for spec/plan interview conversations.
Messages are routed through SpecAgentService which handles SDK interaction
and persistence to the interactive_messages table.

CP1 (tracer bullet): Single endpoint, new service per request.
CP2 will add: GET /chat/history, service instance caching, SDK session resume.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.spec_agent_service import SpecAgentService
from database.connection import get_async_session
from database.crud import get_session_by_slug

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class ChatSendRequest(BaseModel):
    """Request body for sending a chat message."""

    session_slug: str
    message: str


class ChatSendResponse(BaseModel):
    """Response body with agent response blocks."""

    blocks: list[dict]
    turn_index: int


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest) -> ChatSendResponse:
    """
    Send a message to the spec interview agent.

    Creates a new SpecAgentService per request (CP1 tracer bullet).
    Persists user message and agent response blocks to interactive_messages.

    Args:
        request: Session slug and user message text

    Returns:
        Agent response blocks and turn index

    Raises:
        HTTPException 404: Session not found
        HTTPException 500: Agent SDK error
    """
    # Look up session by slug
    async with get_async_session() as db:
        session = await get_session_by_slug(db, request.session_slug)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_slug}",
        )

    # Create service, send message, disconnect (CP1: fresh per request)
    service = SpecAgentService(
        session_slug=request.session_slug,
        working_dir=session.working_dir,
    )

    try:
        await service.connect(session.id)
        blocks = await service.send_message(request.message, turn_index=0)
        await service.disconnect()
    except Exception as e:
        logger.exception("Chat send failed: session=%s", request.session_slug)
        # Ensure cleanup on error
        try:
            await service.disconnect()
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        ) from e

    return ChatSendResponse(blocks=blocks, turn_index=0)
