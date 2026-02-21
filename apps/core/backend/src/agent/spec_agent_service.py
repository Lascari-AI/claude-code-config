"""
SpecAgentService - Service class for spec interview chat via Claude Agent SDK.

Wraps the Claude Agent SDK ClaudeSDKClient for spec phase conversations. Handles:
- Configuring the agent with session MCP tools and skill loading
- Sending user messages and collecting response blocks
- Persisting both user and agent messages to interactive_messages table
- Managing the Agent DB record lifecycle
- Client registry for multi-turn conversation support

Uses ClaudeSDKClient for multi-turn conversation continuity with hook support.
The SDK session ID is captured from ResultMessage after the first query and
stored for resume across server restarts.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, TypedDict
from uuid import UUID

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    ResultMessage,
)

from database.connection import get_async_session
from database.crud import (
    create_agent,
    create_agent_log,
    create_interactive_message,
    list_agents_for_session,
    update_agent,
)
from database.models import AgentCreate, AgentLogCreate, AgentUpdate, InteractiveMessageCreate
from mcp_tools import get_session_mcp_server
from mcp_tools.server import SERVER_NAME

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class PendingQuestion(TypedDict):
    """Structured question data from an AskUserQuestion tool call."""

    tool_use_id: str
    questions: list[dict]  # [{question, header, options: [{label, description}], multiSelect}]


class SendMessageResult(TypedDict):
    """Return type for send_message and send_tool_result."""

    blocks: list[dict]
    pending_question: PendingQuestion | None


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

    On first call after server restart, checks DB for an existing spec
    agent with sdk_session_id and resumes the SDK session if found.

    Args:
        session_slug: Session slug (registry key)
        working_dir: Working directory for the agent
        session_id: Parent session UUID for FK relationships
    """
    if session_slug in _active_services:
        service = _active_services[session_slug]
        if service._client is not None:  # Still connected
            return service

    # Check DB for existing spec agent that can be resumed
    resume_session_id: str | None = None
    existing_agent_id: UUID | None = None

    async with get_async_session() as db:
        agents = await list_agents_for_session(
            db, session_id, agent_type="spec", status="executing"
        )
        if not agents:
            # Also check 'waiting' status (paused on AskUserQuestion)
            agents = await list_agents_for_session(
                db, session_id, agent_type="spec", status="waiting"
            )

        if agents:
            existing_agent = agents[-1]  # Most recent
            if existing_agent.sdk_session_id:
                resume_session_id = existing_agent.sdk_session_id
                existing_agent_id = existing_agent.id
                logger.info(
                    "Found existing spec agent for resume: agent=%s sdk_session=%s",
                    existing_agent_id,
                    resume_session_id,
                )

    service = SpecAgentService(session_slug, working_dir)
    await service.connect(
        session_id,
        resume_session_id=resume_session_id,
        existing_agent_id=existing_agent_id,
    )
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

    Uses ClaudeSDKClient for multi-turn conversation with hook support.

    Lifecycle (multi-turn via registry):
        service = await get_or_create_service(slug, working_dir, session_id)
        blocks = await service.send_message(prompt, turn_index=0)
        # ... subsequent calls reuse the same client instance
        blocks = await service.send_message(prompt, turn_index=1)
        await remove_service(slug)  # When phase complete
    """

    def __init__(self, session_slug: str, working_dir: str) -> None:
        self.session_slug = session_slug
        self.working_dir = working_dir
        self._agent_id: Optional[UUID] = None
        self._session_id: Optional[UUID] = None
        self._sdk_session_id: Optional[str] = None
        self._client: Optional[ClaudeSDKClient] = None

    async def connect(
        self,
        session_id: UUID,
        resume_session_id: str | None = None,
        existing_agent_id: UUID | None = None,
    ) -> None:
        """
        Prepare the agent: create or reuse DB record, configure SDK client.

        When resume_session_id is provided, reuses the existing Agent record
        and configures the SDK client to resume the prior conversation.

        Args:
            session_id: Parent session UUID for FK relationships
            resume_session_id: SDK session ID to resume (from prior agent)
            existing_agent_id: Existing Agent UUID to reuse instead of creating new
        """
        self._session_id = session_id

        if existing_agent_id and resume_session_id:
            # Resume: reuse existing Agent record
            self._agent_id = existing_agent_id
            self._sdk_session_id = resume_session_id

            async with get_async_session() as db:
                await update_agent(db, existing_agent_id, AgentUpdate(status="executing"))

            logger.info(
                "Resuming existing agent: agent=%s sdk_session=%s",
                existing_agent_id,
                resume_session_id,
            )
        else:
            # Fresh start: create new Agent DB record
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
                await update_agent(db, agent.id, AgentUpdate(status="executing"))

        # Configure SDK options with Claude Code preset + spec interview instructions
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": (
                    "\n\n# Spec Interview Mode\n\n"
                    "You are conducting a spec interview for a development session. "
                    "Your role is to help the user define WHAT they want to build before planning HOW.\n\n"
                    "Principles:\n"
                    "- Ask ONE focused question at a time\n"
                    "- Be in-depth — ask about technical details, UI/UX, concerns, tradeoffs, edge cases\n"
                    "- Dig into non-obvious aspects and explain WHY you're asking\n"
                    "- Capture the user's mental model, reasoning, and preferences\n"
                    "- After each answer, update the spec.md document in the session directory\n"
                    "- Continue until the spec is comprehensive"
                ),
            },
            setting_sources=["project"],
            cwd=self.working_dir,
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
            permission_mode="acceptEdits",
            hooks={
                "PreToolUse": [HookMatcher(hooks=[self._pre_tool_hook])],
                "PostToolUse": [HookMatcher(hooks=[self._post_tool_hook])],
            },
            # Resume prior SDK session if available (e.g. after server restart)
            resume=resume_session_id,
        )

        # Create and connect the SDK client
        self._client = ClaudeSDKClient(options=options)
        await self._client.connect()

        logger.info(
            "SpecAgentService connected: session=%s agent=%s resume=%s",
            session_id,
            self._agent_id,
            bool(resume_session_id),
        )

    async def send_message(self, prompt: str, turn_index: int) -> SendMessageResult:
        """
        Send a user message and collect agent response blocks.

        Persists both the user message and agent response blocks to the
        interactive_messages table. On first call, captures sdk_session_id
        from ResultMessage and stores it in the Agent record for resume.
        The ClaudeSDKClient maintains conversation context across calls.

        If the agent calls AskUserQuestion, execution pauses and returns
        the pending question. Call send_tool_result() with the user's
        answer to continue the conversation.

        Args:
            prompt: User message text
            turn_index: Conversation turn number

        Returns:
            SendMessageResult with blocks and optional pending_question
        """
        if self._client is None or self._session_id is None:
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

        return await self._run_query(prompt, turn_index)

    async def start_interview(self, turn_index: int) -> SendMessageResult:
        """
        Kick off the spec interview — agent sends the opening message.

        Sends an init prompt to the agent without persisting a user message.
        Only the agent's response blocks are persisted via _run_query().
        This gives us the "agent speaks first" UX with no fake user bubble.

        Args:
            turn_index: Conversation turn number (typically 0)

        Returns:
            SendMessageResult with agent greeting blocks
        """
        if self._client is None or self._session_id is None:
            raise RuntimeError("SpecAgentService not connected. Call connect() first.")

        init_prompt = (
            "A new session has been created. Begin the spec interview by greeting "
            "the user warmly but briefly, and asking what they want to build. "
            "Be conversational and curious."
        )
        return await self._run_query(init_prompt, turn_index)

    async def send_tool_result(
        self, tool_use_id: str, result: dict, turn_index: int
    ) -> SendMessageResult:
        """
        Send user's answer to an AskUserQuestion tool call back to the SDK.

        Persists the user's answer as an interactive message, then sends
        a follow-up query to the client. The client maintains conversation
        context, so the answer is carried forward automatically.

        Args:
            tool_use_id: The tool_use_id from the pending question
            result: User's answers dict {question_text: selected_option}
            turn_index: Conversation turn number

        Returns:
            SendMessageResult with new response blocks and optional pending_question
        """
        if self._client is None or self._session_id is None:
            raise RuntimeError("SpecAgentService not connected. Call connect() first.")

        # Persist user's answer as interactive message
        answer_content = json.dumps({"tool_use_id": tool_use_id, "answers": result})
        async with get_async_session() as db:
            await create_interactive_message(
                db,
                InteractiveMessageCreate(
                    session_id=self._session_id,
                    agent_id=self._agent_id,
                    phase="spec",
                    role="user",
                    block_type="tool_result",
                    content=answer_content,
                    tool_name="AskUserQuestion",
                    turn_index=turn_index,
                    block_index=0,
                ),
            )

        answer_prompt = json.dumps({"answers": result})
        return await self._run_query(answer_prompt, turn_index)

    async def _run_query(self, prompt: str, turn_index: int) -> SendMessageResult:
        """
        Execute SDK query via ClaudeSDKClient and process response blocks.

        Sends the prompt via client.query(), then iterates client.receive_response()
        to collect AssistantMessage blocks and the final ResultMessage.
        Detects AskUserQuestion tool calls and returns them as pending questions.

        Args:
            prompt: Message to send to the agent
            turn_index: Conversation turn number

        Returns:
            SendMessageResult with blocks and optional pending_question
        """
        response_blocks: list[dict] = []
        pending_question: PendingQuestion | None = None
        block_index = 0

        # Send prompt to the client
        await self._client.query(prompt)

        # Collect response messages until ResultMessage
        async for message in self._client.receive_response():
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

                        # Detect AskUserQuestion — capture and pause execution
                        if block.name == "AskUserQuestion":
                            pending_question = PendingQuestion(
                                tool_use_id=block.id,
                                questions=block.input.get("questions", []),
                            )

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

                # If AskUserQuestion found, stop processing further messages
                if pending_question:
                    logger.info(
                        "AskUserQuestion detected: tool_use_id=%s agent=%s",
                        pending_question["tool_use_id"],
                        self._agent_id,
                    )
                    break

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

        return SendMessageResult(blocks=response_blocks, pending_question=pending_question)

    # ─── Observability Hooks ────────────────────────────────────────────────────

    async def _pre_tool_hook(self, input_data: dict, tool_use_id, context) -> dict:
        """
        PreToolUse hook — logs tool invocation to AgentLog before execution.

        Called by the SDK before each tool is executed. Creates an AgentLog
        entry for real-time execution timeline visibility.

        Follows SDK hook callback signature: (input_data, tool_use_id, context).
        """
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})
        try:
            async with get_async_session() as db:
                await create_agent_log(
                    db,
                    AgentLogCreate(
                        agent_id=self._agent_id,
                        session_id=self._session_id,
                        sdk_session_id=self._sdk_session_id,
                        event_category="hook",
                        event_type="PreToolUse",
                        tool_name=tool_name,
                        tool_input=tool_input,
                    ),
                )
        except Exception:
            # Hooks must not break the agent execution pipeline
            logger.exception("Failed to log PreToolUse for tool=%s", tool_name)
        return {}

    async def _post_tool_hook(self, input_data: dict, tool_use_id, context) -> dict:
        """
        PostToolUse hook — logs tool completion to AgentLog after execution.

        Called by the SDK after each tool completes. Records output and
        duration for cost tracking and debugging.

        Follows SDK hook callback signature: (input_data, tool_use_id, context).
        """
        tool_name = input_data.get("tool_name", "unknown")
        tool_output = str(input_data.get("tool_response", ""))
        try:
            async with get_async_session() as db:
                await create_agent_log(
                    db,
                    AgentLogCreate(
                        agent_id=self._agent_id,
                        session_id=self._session_id,
                        sdk_session_id=self._sdk_session_id,
                        event_category="hook",
                        event_type="PostToolUse",
                        tool_name=tool_name,
                        tool_output=tool_output,
                    ),
                )
        except Exception:
            # Hooks must not break the agent execution pipeline
            logger.exception("Failed to log PostToolUse for tool=%s", tool_name)
        return {}

    async def disconnect(self) -> None:
        """
        Clean up: disconnect SDK client and mark Agent DB record as complete.
        """
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                logger.exception("Error disconnecting SDK client: agent=%s", self._agent_id)
            self._client = None

        if self._agent_id:
            async with get_async_session() as db:
                await update_agent(
                    db,
                    self._agent_id,
                    AgentUpdate(status="complete"),
                )

            logger.info("SpecAgentService disconnected: agent=%s", self._agent_id)
