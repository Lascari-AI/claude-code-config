"""
SpecAgentService - Service class for spec interview chat via Claude Agent SDK.

Wraps the Claude Agent SDK query() for spec phase conversations. Handles:
- Configuring the agent with session MCP tools and skill loading
- Sending user messages and collecting response blocks
- Persisting both user and agent messages to interactive_messages table
- Managing the Agent DB record lifecycle
- Client registry for multi-turn conversation support

Uses query() with ClaudeAgentOptions.resume for multi-turn conversation
continuity. The SDK session ID is captured from ResultMessage after the first
query and passed via resume on subsequent calls.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Optional
from uuid import UUID

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

from database.connection import get_async_session
from database.crud import create_agent, create_interactive_message, update_agent
from database.models import AgentCreate, AgentUpdate, InteractiveMessageCreate
from mcp_tools import get_session_mcp_server
from mcp_tools.server import SERVER_NAME

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

_active_services: dict[str, SpecAgentService] = {}


async def get_or_create_service(
    session_slug: str,
    working_dir: str,
    session_id: UUID,
) -> SpecAgentService:
    """
    Get an existing service or create and connect a new one.

    Caches services by session_slug for reuse across requests within
    the same phase. Enables multi-turn conversation without creating
    new Agent records or SDK sessions per message.

    Args:
        session_slug: Session slug (registry key)
        working_dir: Working directory for the agent
        session_id: Parent session UUID for FK relationships
    """
    if session_slug in _active_services:
        service = _active_services[session_slug]
        if service._options is not None:  # Still connected
            return service

    service = SpecAgentService(session_slug, working_dir)
    await service.connect(session_id)
    _active_services[session_slug] = service
    return service


async def remove_service(session_slug: str) -> None:
    """Remove and disconnect a service from the registry."""
    service = _active_services.pop(session_slug, None)
    if service:
        await service.disconnect()


class SpecAgentService:
    """
    Service for spec interview conversations via Claude Agent SDK.

    Lifecycle (multi-turn via registry):
        service = await get_or_create_service(slug, working_dir, session_id)
        blocks = await service.send_message(prompt, turn_index=0)
        # ... subsequent calls reuse the same service instance
        blocks = await service.send_message(prompt, turn_index=1)
        await remove_service(slug)  # When phase complete
    """

    def __init__(self, session_slug: str, working_dir: str) -> None:
        self.session_slug = session_slug
        self.working_dir = working_dir
        self._agent_id: Optional[UUID] = None
        self._session_id: Optional[UUID] = None
        self._sdk_session_id: Optional[str] = None
        self._options: Optional[ClaudeAgentOptions] = None

    async def connect(self, session_id: UUID) -> None:
        """
        Prepare the agent: create DB record and configure SDK options.

        Args:
            session_id: Parent session UUID for FK relationships
        """
        self._session_id = session_id

        # Create Agent DB record
        async with get_async_session() as db:
            agent = await create_agent(
                db,
                AgentCreate(
                    session_id=session_id,
                    agent_type="spec",
                    model="claude-sonnet-4-5-20250929",
                    model_alias="sonnet",
                    working_dir=self.working_dir,
                ),
            )
            self._agent_id = agent.id

            # Mark agent as executing
            await update_agent(db, agent.id, AgentUpdate(status="executing"))

        # Configure SDK options
        self._options = ClaudeAgentOptions(
            mcp_servers={SERVER_NAME: get_session_mcp_server()},
            allowed_tools=[
                f"mcp__{SERVER_NAME}__*",  # Session state tools
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "Skill",
                "Bash",
            ],
            max_turns=10,
        )

        logger.info(
            "SpecAgentService connected: session=%s agent=%s",
            session_id,
            self._agent_id,
        )

    async def send_message(self, prompt: str, turn_index: int) -> list[dict]:
        """
        Send a user message and collect agent response blocks.

        Persists both the user message and agent response blocks to the
        interactive_messages table. On first call, captures sdk_session_id
        from ResultMessage and stores it in the Agent record for resume.
        Subsequent calls use resume to maintain conversation context.

        Args:
            prompt: User message text
            turn_index: Conversation turn number

        Returns:
            List of response block dicts: [{role, block_type, content, tool_name}]
        """
        if self._options is None or self._session_id is None:
            raise RuntimeError("SpecAgentService not connected. Call connect() first.")

        # Persist user message
        async with get_async_session() as db:
            await create_interactive_message(
                db,
                InteractiveMessageCreate(
                    session_id=self._session_id,
                    agent_id=self._agent_id,
                    phase="spec",
                    role="user",
                    block_type="text",
                    content=prompt,
                    turn_index=turn_index,
                    block_index=0,
                ),
            )

        # Build options with resume if we have a prior sdk_session_id
        opts = self._options
        if self._sdk_session_id:
            opts = replace(self._options, resume=self._sdk_session_id)

        # Query the agent
        response_blocks: list[dict] = []
        block_index = 0

        async for message in query(prompt=prompt, options=opts):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    block_dict: dict = {}

                    if hasattr(block, "text"):
                        # TextBlock
                        block_dict = {
                            "role": "assistant",
                            "block_type": "text",
                            "content": block.text,
                            "tool_name": None,
                        }
                    elif hasattr(block, "name") and hasattr(block, "input"):
                        # ToolUseBlock
                        block_dict = {
                            "role": "tool_use",
                            "block_type": "tool_use",
                            "content": str(block.input),
                            "tool_name": block.name,
                        }

                    if block_dict:
                        response_blocks.append(block_dict)

                        # Persist to DB
                        async with get_async_session() as db:
                            await create_interactive_message(
                                db,
                                InteractiveMessageCreate(
                                    session_id=self._session_id,
                                    agent_id=self._agent_id,
                                    phase="spec",
                                    role=block_dict["role"],
                                    block_type=block_dict["block_type"],
                                    content=block_dict["content"],
                                    tool_name=block_dict["tool_name"],
                                    turn_index=turn_index,
                                    block_index=block_index + 1,  # +1 since user msg is 0
                                ),
                            )
                            block_index += 1

            elif isinstance(message, ResultMessage):
                # Capture SDK session ID for resume on subsequent calls
                if message.session_id and not self._sdk_session_id:
                    self._sdk_session_id = message.session_id
                    async with get_async_session() as db:
                        await update_agent(
                            db,
                            self._agent_id,
                            AgentUpdate(sdk_session_id=self._sdk_session_id),
                        )
                    logger.info(
                        "Captured SDK session ID: %s for agent=%s",
                        self._sdk_session_id,
                        self._agent_id,
                    )

                logger.info(
                    "Agent result: subtype=%s agent=%s",
                    message.subtype,
                    self._agent_id,
                )

        return response_blocks

    async def disconnect(self) -> None:
        """
        Clean up: mark Agent DB record as complete.
        """
        if self._agent_id:
            async with get_async_session() as db:
                await update_agent(
                    db,
                    self._agent_id,
                    AgentUpdate(status="complete"),
                )

            logger.info("SpecAgentService disconnected: agent=%s", self._agent_id)

        self._options = None
