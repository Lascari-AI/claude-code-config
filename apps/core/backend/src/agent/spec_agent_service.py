"""
SpecAgentService - Service class for spec interview chat via Claude Agent SDK.

Wraps the Claude Agent SDK query() for spec phase conversations. Handles:
- Configuring the agent with session MCP tools and skill loading
- Sending user messages and collecting response blocks
- Persisting both user and agent messages to interactive_messages table
- Managing the Agent DB record lifecycle

CP1 (tracer bullet): Uses query() for single request-response cycles.
CP2 will upgrade to ClaudeSDKClient for multi-turn with SDK session resume.
"""

from __future__ import annotations

import logging
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


class SpecAgentService:
    """
    Service for spec interview conversations via Claude Agent SDK.

    Lifecycle per request (CP1):
        service = SpecAgentService(session_slug, working_dir)
        await service.connect(session_id)
        blocks = await service.send_message(prompt, turn_index=0)
        await service.disconnect()

    CP2 will add instance caching and SDK session resume for multi-turn.
    """

    def __init__(self, session_slug: str, working_dir: str) -> None:
        self.session_slug = session_slug
        self.working_dir = working_dir
        self._agent_id: Optional[UUID] = None
        self._session_id: Optional[UUID] = None
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
        interactive_messages table.

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

        # Query the agent
        response_blocks: list[dict] = []
        block_index = 0

        async for message in query(prompt=prompt, options=self._options):
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
