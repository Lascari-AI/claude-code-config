"""
Chat Router - Endpoints for interactive chat with Claude Agent SDK.

Provides the send-message endpoint for spec/plan interview conversations.
Messages are routed through SpecAgentService which handles SDK interaction
and persistence to the interactive_messages table.

Uses service registry for multi-turn: get_or_create_service() caches
active service instances per session. SDK session resume via query()+resume
maintains conversation context across requests.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agent.spec_agent_service import get_or_create_service, remove_service
from database.connection import get_async_session
from database.crud import (
    get_max_turn_index,
    get_session_by_slug,
    list_messages_for_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class ChatStartRequest(BaseModel):
    """Request body for starting the auto-interview (agent speaks first)."""

    session_slug: str


class ChatSendRequest(BaseModel):
    """Request body for sending a chat message."""

    session_slug: str
    message: str


class ChatSendResponse(BaseModel):
    """Response body with agent response blocks."""

    blocks: list[dict]
    turn_index: int
    pending_question: Optional[dict] = None  # {tool_use_id, questions[]}


class ChatAnswerRequest(BaseModel):
    """Request body for answering an AskUserQuestion."""

    session_slug: str
    tool_use_id: str
    answers: dict[str, str]  # {question_text: selected_option}


class ChatHistoryMessage(BaseModel):
    """Single message block in chat history."""

    role: str
    block_type: str
    content: Optional[str]
    tool_name: Optional[str]
    turn_index: int
    block_index: int
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Response body for chat history."""

    messages: list[ChatHistoryMessage]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/start", response_model=ChatSendResponse)
async def start_chat(request: ChatStartRequest) -> ChatSendResponse:
    """
    Start the spec interview — agent sends the opening message.

    Idempotent: if any messages already exist for this session,
    returns an empty response (prevents double-start on page refresh).

    Args:
        request: Session slug

    Returns:
        Agent greeting blocks and turn index

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

    # Idempotency check: if any messages exist, skip (already started)
    async with get_async_session() as db:
        existing = await list_messages_for_session(db, session.id, limit=1)
    if existing:
        logger.info("Chat already started, skipping: session=%s", request.session_slug)
        return ChatSendResponse(blocks=[], turn_index=0, pending_question=None)

    # Start the interview (agent speaks first, no user message persisted)
    try:
        service = await get_or_create_service(
            session_slug=request.session_slug,
            working_dir=session.working_dir,
            session_id=session.id,
        )
        result = await service.start_interview(turn_index=0)
    except Exception as e:
        logger.exception("Chat start failed: session=%s", request.session_slug)
        try:
            await remove_service(request.session_slug)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        ) from e

    return ChatSendResponse(
        blocks=result["blocks"],
        turn_index=0,
        pending_question=result["pending_question"],
    )


@router.post("/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest) -> ChatSendResponse:
    """
    Send a message to the spec interview agent.

    Uses get_or_create_service() for multi-turn support: first request
    creates the service and Agent DB record, subsequent requests reuse
    the cached instance with SDK session resume.

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

    # Determine turn_index from existing messages
    async with get_async_session() as db:
        max_turn = await get_max_turn_index(db, session.id)
    turn_index = max_turn + 1

    # Get or create service (cached for multi-turn)
    try:
        service = await get_or_create_service(
            session_slug=request.session_slug,
            working_dir=session.working_dir,
            session_id=session.id,
        )
        result = await service.send_message(request.message, turn_index=turn_index)
    except Exception as e:
        logger.exception("Chat send failed: session=%s", request.session_slug)
        # Clean up on error — remove from registry
        try:
            await remove_service(request.session_slug)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        ) from e

    return ChatSendResponse(
        blocks=result["blocks"],
        turn_index=turn_index,
        pending_question=result["pending_question"],
    )


@router.post("/answer", response_model=ChatSendResponse)
async def answer_question(request: ChatAnswerRequest) -> ChatSendResponse:
    """
    Submit user's answer to an AskUserQuestion tool call.

    Retrieves the cached service for the session, sends the tool result
    back to the SDK, and returns the agent's continued response.

    Args:
        request: Session slug, tool_use_id, and answer selections

    Returns:
        Agent response blocks (may contain another pending_question)

    Raises:
        HTTPException 404: Session not found
        HTTPException 500: Agent SDK error
    """
    async with get_async_session() as db:
        session = await get_session_by_slug(db, request.session_slug)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_slug}",
        )

    # Determine turn_index
    async with get_async_session() as db:
        max_turn = await get_max_turn_index(db, session.id)
    turn_index = max_turn + 1

    try:
        service = await get_or_create_service(
            session_slug=request.session_slug,
            working_dir=session.working_dir,
            session_id=session.id,
        )
        result = await service.send_tool_result(
            tool_use_id=request.tool_use_id,
            result=request.answers,
            turn_index=turn_index,
        )
    except Exception as e:
        logger.exception("Chat answer failed: session=%s", request.session_slug)
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        ) from e

    return ChatSendResponse(
        blocks=result["blocks"],
        turn_index=turn_index,
        pending_question=result["pending_question"],
    )


@router.get("/history/{session_slug}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_slug: str,
    phase: Optional[str] = Query(None, description="Filter by phase (spec, plan)"),
) -> ChatHistoryResponse:
    """
    Get chat history for a session.

    Returns all persisted interactive messages ordered by turn_index
    then block_index. Supports optional phase filtering.

    Args:
        session_slug: Session slug to fetch history for
        phase: Optional phase filter (spec, plan)

    Returns:
        List of message blocks and total count

    Raises:
        HTTPException 404: Session not found
    """
    async with get_async_session() as db:
        session = await get_session_by_slug(db, session_slug)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_slug}",
        )

    async with get_async_session() as db:
        messages = await list_messages_for_session(db, session.id, phase=phase)

    history = [
        ChatHistoryMessage(
            role=msg.role,
            block_type=msg.block_type,
            content=msg.content,
            tool_name=msg.tool_name,
            turn_index=msg.turn_index,
            block_index=msg.block_index,
            timestamp=msg.timestamp,
        )
        for msg in messages
    ]

    return ChatHistoryResponse(messages=history, total=len(history))
