"""
Orchestrator Service Module

Business logic for executing orchestrator agent with WebSocket streaming.

Implements three-phase logging pattern:
1. Pre-execution: Log user message to database
2. Execution: Execute agent, stream response via WebSocket
3. Post-execution: Log orchestrator response, update costs

Reference: apps/orchestrator_1_term/modules/orchestrator_agent.py
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Claude SDK imports
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from . import config

# Configuration
from .config import DEFAULT_CHAT_HISTORY_LIMIT

# Database operations
from .database import (
    get_chat_history,
    get_orchestrator_action_blocks,
    get_turn_count,
    insert_chat_message,
    insert_system_log,
    update_chat_summary,
    update_orchestrator_costs,
    update_orchestrator_session,
    update_system_log_summary,
)
from .logger import OrchestratorLogger

# Hook imports for orchestrator agent event tracking
from .orchestrator_hooks import (
    create_orchestrator_post_tool_hook,
    create_orchestrator_pre_tool_hook,
    create_orchestrator_stop_hook,
)

# AI summarization
from .single_agent_prompt import summarize_event
from .subagent_loader import SubagentRegistry

# WebSocket and logging
from .websocket_manager import WebSocketManager


def get_orchestrator_tools() -> List[str]:
    """
    Get orchestrator management tool signatures in TypeScript format.

    Shows required vs optional parameters with proper TypeScript syntax:
    - Required parameters: `name: string`
    - Optional parameters: `param?: type`
    - Default values: `param = value`

    Returns:
        List of tool signatures in TypeScript function format
    """
    return [
        # Agent Management Tools
        "create_agent(name: string, system_prompt?: string, model?: string, subagent_template?: string)",
        "list_agents()",
        "command_agent(agent_name: string, command: string)",
        "check_agent_status(agent_name: string, tail_count = 10, offset = 0, verbose_logs = false)",
        "delete_agent(agent_name: string)",
        "interrupt_agent(agent_name: string)",
        "read_system_logs(offset = 0, limit = 50, message_contains?: string, level?: string)",
        "report_cost()",
        # AI Developer Workflow Tools
        "start_adw(name_of_adw: string, workflow_type: string, prompt: string, description?: string)",
        "check_adw(adw_id: string, tail_count = 10, event_type?: string, include_step_details = false)",
    ]


class OrchestratorService:
    """
    Service layer for orchestrator agent operations.

    Handles chat message processing, agent execution, and WebSocket streaming.
    """

    def __init__(
        self,
        ws_manager: WebSocketManager,
        logger: OrchestratorLogger,
        agent_manager: Optional["AgentManager"] = None,
        session_id: Optional[str] = None,
        working_dir: Optional[str] = None,
    ):
        """
        Initialize orchestrator service.

        Args:
            ws_manager: WebSocket manager for streaming
            logger: Logger instance
            agent_manager: Optional AgentManager for management tools
            session_id: Optional session ID for resumption
            working_dir: Optional working directory override
        """
        self.ws_manager = ws_manager
        self.logger = logger
        self.agent_manager = agent_manager
        self.session_id = session_id
        self.working_dir = working_dir or config.get_working_dir()

        # Track if we started with a session_id (for resume vs new orchestrator)
        # If True, we're resuming an existing session and should NOT update session_id
        # If False, this is a new orchestrator and we SHOULD update session_id after first prompt
        self.started_with_session = session_id is not None

        # Track if we've captured SystemMessage metadata (only capture once per boot)
        self._system_message_captured = False

        # Interrupt support: Track active client and execution state
        self.active_client: Optional[ClaudeSDKClient] = None
        self.is_executing = False
        self._execution_lock = asyncio.Lock()

        # Get management tools from agent_manager if provided
        self.management_tools = []
        if self.agent_manager:
            self.management_tools = self.agent_manager.create_management_tools()
            self.logger.info(
                f"Registered {len(self.management_tools)} management tools"
            )

        self.logger.info(f"OrchestratorService initialized")
        if session_id:
            self.logger.info(f"Resuming session: {session_id}")
        self.logger.info(f"Working directory: {self.working_dir}")

    def _load_system_prompt(self) -> str:
        """
        Load orchestrator system prompt from file and inject dynamic placeholders.

        Placeholders:
            - {{SUBAGENT_MAP}}: Available subagent templates from .claude/agents/
            - {{AVAILABLE_ADW_TYPES}}: Available ADW workflow types from adws/adw_workflows/

        Returns:
            System prompt text with placeholders replaced

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = Path(config.ORCHESTRATOR_SYSTEM_PROMPT_PATH)

        # Make path absolute if it's relative
        if not prompt_path.is_absolute():
            prompt_path = Path(config.BACKEND_DIR) / prompt_path

        if not prompt_path.exists():
            self.logger.warning(
                f"System prompt not found at {prompt_path}, using default"
            )
            return "You are a helpful orchestrator agent that manages other Claude Code agents."

        with open(prompt_path, "r") as f:
            prompt_text = f.read()

        # Check for SUBAGENT_MAP placeholder
        if "{{SUBAGENT_MAP}}" in prompt_text:
            self.logger.debug("Found {{SUBAGENT_MAP}} placeholder in system prompt")

            # Initialize SubagentRegistry to discover templates
            registry = SubagentRegistry(self.working_dir, self.logger)
            self.logger.info("SubagentRegistry initialized for prompt injection")

            # Generate template list
            templates = registry.list_templates()

            if templates:
                # Format as markdown list
                template_lines = []
                for t in templates:
                    template_lines.append(f"- **{t['name']}**: {t['description']}")
                template_map = "\n".join(template_lines)
                self.logger.info(
                    f"✅ Injecting {len(templates)} subagent template(s) into orchestrator prompt"
                )
            else:
                # No templates available - provide helpful message
                template_map = "No subagent templates available. Create templates in `.claude/agents/` directory to enable specialized agents."
                self.logger.warning(
                    "⚠️  No templates available for SUBAGENT_MAP - using fallback message"
                )

            # Replace placeholder
            prompt_text = prompt_text.replace("{{SUBAGENT_MAP}}", template_map)

        # Check for AVAILABLE_ADW_TYPES placeholder
        if "{{AVAILABLE_ADW_TYPES}}" in prompt_text:
            self.logger.debug("Found {{AVAILABLE_ADW_TYPES}} placeholder in system prompt")

            # Discover available workflow types from adws/adw_workflows/adw_*.py
            workflow_dir = Path(self.working_dir) / "adws" / "adw_workflows"
            workflow_types = []

            if workflow_dir.exists():
                for file in workflow_dir.glob("adw_*.py"):
                    name = file.stem  # adw_feature-development
                    if name.startswith("adw_"):
                        workflow_type = name[4:]  # Remove "adw_" prefix
                        workflow_types.append(workflow_type)
                workflow_types.sort()

            if workflow_types:
                # Format as bullet list
                adw_type_list = "\n".join([f"- `{wt}` → `adws/adw_workflows/adw_{wt}.py`" for wt in workflow_types])
                self.logger.info(f"Discovered {len(workflow_types)} ADW workflow type(s)")
            else:
                adw_type_list = "No workflow types available. Create workflow files in `adws/adw_workflows/adw_*.py` to enable ADWs."
                self.logger.warning("⚠️  No ADW workflow types found")

            prompt_text = prompt_text.replace("{{AVAILABLE_ADW_TYPES}}", adw_type_list)

        return prompt_text

    def _create_claude_agent_options(
        self, orchestrator_agent_id: Optional[str] = None
    ) -> "ClaudeAgentOptions":
        """
        Create Claude Agent SDK options for orchestrator.

        Args:
            orchestrator_agent_id: Optional orchestrator UUID for hook tracking

        Returns:
            ClaudeAgentOptions configured for orchestrator

        Note:
            - Resumes session if self.session_id is valid Claude SDK format
            - Uses configured working directory
            - Registers management tools via MCP server if agent_manager provided
            - Includes hooks for event tracking
        """
        # Use resume if session_id exists
        resume_session = None
        if self.session_id and isinstance(self.session_id, str):
            resume_session = self.session_id
            self.logger.info(f"Resuming Claude SDK session: {resume_session[:20]}...")
        else:
            self.logger.info(
                "Starting fresh Claude SDK session (no valid session to resume)"
            )

        # Build options with management tools if available
        # Pass ANTHROPIC_API_KEY explicitly to ensure subprocess has access
        env_vars = {}
        if "ANTHROPIC_API_KEY" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

        options_dict = {
            "system_prompt": self._load_system_prompt(),
            "model": config.ORCHESTRATOR_MODEL,
            "cwd": self.working_dir,
            "resume": resume_session,
            "env": env_vars,  # Ensure API key is available to subprocess
        }

        # Add hooks for event tracking if orchestrator_agent_id provided
        if orchestrator_agent_id:
            task_slug = f"orchestrator-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            entry_counter = {"count": 0}
            options_dict["hooks"] = self._build_hooks_for_orchestrator(
                uuid.UUID(orchestrator_agent_id), task_slug, entry_counter
            )

        # Register management tools via MCP server
        if self.management_tools:
            from claude_agent_sdk import create_sdk_mcp_server

            mcp_server = create_sdk_mcp_server(
                name="mgmt", version="1.0.0", tools=self.management_tools
            )

            options_dict["mcp_servers"] = {"mgmt": mcp_server}

            # Define allowed tools
            options_dict["allowed_tools"] = [
                # Agent management tools
                "mcp__mgmt__create_agent",
                "mcp__mgmt__list_agents",
                "mcp__mgmt__command_agent",
                "mcp__mgmt__check_agent_status",
                "mcp__mgmt__delete_agent",
                "mcp__mgmt__interrupt_agent",
                "mcp__mgmt__read_system_logs",
                "mcp__mgmt__report_cost",
                # ADW tools
                "mcp__mgmt__start_adw",
                "mcp__mgmt__check_adw",
                # Standard tools
                "Bash",
                "Read",
                "SlashCommand",
                "Skill",
            ]

            self.logger.info("MCP management tools registered for orchestrator")

        # Add setting_sources to load project settings (CLAUDE.md, slash commands, etc.)
        options_dict["setting_sources"] = ["project"]

        options = ClaudeAgentOptions(**options_dict)

        return options

    def _build_hooks_for_orchestrator(
        self,
        orchestrator_agent_id: uuid.UUID,
        task_slug: str,
        entry_counter: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Build hooks dictionary for orchestrator agent.

        Args:
            orchestrator_agent_id: UUID of orchestrator
            task_slug: Task identifier
            entry_counter: Mutable counter dict

        Returns:
            Hooks dict for ClaudeAgentOptions
        """
        agent_name = "orchestrator"  # Orchestrator's name for logging

        return {
            "PreToolUse": [
                {
                    "hooks": [
                        create_orchestrator_pre_tool_hook(
                            orchestrator_agent_id,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "hooks": [
                        create_orchestrator_post_tool_hook(
                            orchestrator_agent_id,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        create_orchestrator_stop_hook(
                            orchestrator_agent_id,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                }
            ],
        }

    async def load_chat_history(
        self, orchestrator_agent_id: str, limit: int = DEFAULT_CHAT_HISTORY_LIMIT
    ) -> Dict[str, Any]:
        """
        Load chat history for orchestrator agent, including action blocks.

        Fetches both chat messages (TextBlock chunks) and action blocks
        (ThinkingBlock, ToolUseBlock) from system_logs, merges them, and
        returns in chronological order.

        Args:
            orchestrator_agent_id: UUID of orchestrator agent
            limit: Maximum number of messages to return

        Returns:
            Dictionary with messages list (includes action blocks) and turn count
        """
        try:
            orch_uuid = uuid.UUID(orchestrator_agent_id)

            # Get chat history, action blocks, and turn count in parallel
            messages = await get_chat_history(orch_uuid, limit=limit)
            action_blocks = await get_orchestrator_action_blocks(orch_uuid, limit=limit)
            turn_count = await get_turn_count(orch_uuid)

            # Convert chat messages UUIDs to strings for JSON serialization
            for msg in messages:
                msg["id"] = str(msg["id"])
                msg["orchestrator_agent_id"] = str(msg["orchestrator_agent_id"])
                if msg.get("agent_id"):
                    msg["agent_id"] = str(msg["agent_id"])
                # Convert datetime objects to ISO strings
                msg["created_at"] = msg["created_at"].isoformat()
                msg["updated_at"] = msg["updated_at"].isoformat()

            # Transform action blocks into chat message format
            transformed_blocks = []
            for block in action_blocks:
                block_type = block.get("metadata", {}).get("type")

                if block_type == "thinking_block":
                    # Transform thinking block to frontend format
                    transformed_blocks.append(
                        {
                            "id": str(block["id"]),
                            "sender_type": "orchestrator",
                            "receiver_type": "user",
                            "message": "",  # Empty for thinking blocks
                            "metadata": {
                                "type": "thinking",
                                "thinking": block["metadata"].get("thinking", ""),
                            },
                            "created_at": block["timestamp"].isoformat(),
                            "updated_at": block["timestamp"].isoformat(),
                            "orchestrator_agent_id": orchestrator_agent_id,
                            "agent_id": None,
                        }
                    )

                elif block_type == "tool_use_block":
                    # Transform tool use block to frontend format
                    transformed_blocks.append(
                        {
                            "id": str(block["id"]),
                            "sender_type": "orchestrator",
                            "receiver_type": "user",
                            "message": "",  # Empty for tool use blocks
                            "metadata": {
                                "type": "tool_use",
                                "tool_name": block["metadata"].get("tool_name", ""),
                                "tool_input": block["metadata"].get("tool_input", {}),
                            },
                            "created_at": block["timestamp"].isoformat(),
                            "updated_at": block["timestamp"].isoformat(),
                            "orchestrator_agent_id": orchestrator_agent_id,
                            "agent_id": None,
                        }
                    )

            # Merge messages and action blocks, then sort by timestamp
            all_messages = messages + transformed_blocks
            all_messages.sort(key=lambda x: x["created_at"])

            return {"messages": all_messages, "turn_count": turn_count}

        except Exception as e:
            self.logger.error(f"Failed to load chat history: {e}")
            raise

    async def process_user_message(
        self, user_message: str, orchestrator_agent_id: str
    ) -> Dict[str, Any]:
        """
        Process user message with orchestrator agent.

        Implements three-phase logging:
        1. Pre-execution: Log user message
        2. Execution: Execute agent with streaming
        3. Post-execution: Log response, update costs

        Args:
            user_message: User's message text
            orchestrator_agent_id: UUID of orchestrator agent

        Returns:
            Dictionary with response, session_id, and execution status

        Raises:
            Exception: If execution fails
        """
        orch_uuid = uuid.UUID(orchestrator_agent_id)

        # ═══════════════════════════════════════════════════════════
        # PHASE 1: PRE-EXECUTION - Log user message
        # ═══════════════════════════════════════════════════════════

        try:
            # Insert message into database
            chat_id = await insert_chat_message(
                orchestrator_agent_id=orch_uuid,
                sender_type="user",
                receiver_type="orchestrator",
                message=user_message,
                agent_id=None,
                metadata={},
            )

            # Generate AI summary in background
            asyncio.create_task(self._summarize_and_update_chat(chat_id, user_message))

            self.logger.chat_event(orchestrator_agent_id, user_message, sender="user")

            # Broadcast user message to EventStream (include database ID)
            await self.ws_manager.broadcast(
                {
                    "type": "orchestrator_chat",
                    "message": {
                        "id": str(chat_id),
                        "orchestrator_agent_id": str(orch_uuid),
                        "sender_type": "user",
                        "receiver_type": "orchestrator",
                        "message": user_message,
                        "agent_id": None,
                        "metadata": {},
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to log user message: {e}")
            raise

        # ═══════════════════════════════════════════════════════════
        # INTERRUPT CHECK - Stop current execution if busy
        # ═══════════════════════════════════════════════════════════

        async with self._execution_lock:
            if self.is_executing and self.active_client:
                self.logger.warning(
                    "⚠️  Orchestrator is busy with previous task - interrupting..."
                )
                try:
                    await self.active_client.interrupt()
                    self.logger.info("✅ Successfully interrupted previous task")

                    # Broadcast interruption notification
                    await self.ws_manager.broadcast(
                        {
                            "type": "system_log",
                            "data": {
                                "level": "WARNING",
                                "message": "Previous orchestrator task interrupted - refocusing on new message",
                                "timestamp": datetime.now().isoformat(),
                            },
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Failed to interrupt orchestrator: {e}")
                    # Continue anyway - the new message will be processed

        # ═══════════════════════════════════════════════════════════
        # PHASE 2: EXECUTION - Execute agent with streaming
        # ═══════════════════════════════════════════════════════════

        response_text = ""
        tools_used = []
        final_session_id = None
        usage_data = None
        result_message = None  # Track the ResultMessage for cost extraction

        try:
            # Set typing indicator
            await self.ws_manager.set_typing_indicator(orchestrator_agent_id, True)

            # Create Claude SDK client with hooks
            options = self._create_claude_agent_options(orchestrator_agent_id)

            async with ClaudeSDKClient(options=options) as client:
                # Track execution state for interrupt support
                async with self._execution_lock:
                    self.active_client = client
                    self.is_executing = True

                # Send user's prompt
                await client.query(user_message)

                # Iterate through ALL messages (THE CORE LOOP)
                async for message in client.receive_response():

                    # Handle SystemMessage (informational, not agent output)
                    if isinstance(message, SystemMessage):
                        subtype = getattr(message, "subtype", "unknown")
                        data = getattr(message, "data", {})
                        self.logger.warning(
                            f"[OrchestratorService] SystemMessage received:\n"
                            f"  Subtype: {subtype}\n"
                            f"  Data: {data}\n"
                        )

                        # NEW: Store SystemMessage data in orchestrator metadata (ONCE per boot)
                        if not self._system_message_captured:
                            try:
                                from .database import update_orchestrator_metadata
                                from .slash_command_parser import (
                                    discover_slash_commands,
                                )

                                # Discover slash commands from filesystem using custom parser
                                slash_commands = discover_slash_commands(self.working_dir)

                                # Extract relevant fields for display
                                system_message_info = {
                                    "session_id": data.get("session_id"),
                                    "cwd": data.get("cwd"),
                                    "tools": data.get("tools", []),
                                    "model": data.get("model"),
                                    "subtype": subtype,
                                    "captured_at": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                    "slash_commands": slash_commands,  # Store slash commands
                                }

                                # Store in metadata - IMPORTANT: Pass orchestrator_agent_id to update only THIS agent
                                await update_orchestrator_metadata(
                                    orchestrator_agent_id=orch_uuid,
                                    metadata_updates={"system_message_info": system_message_info}
                                )

                                # Mark as captured so we don't overwrite on subsequent messages
                                self._system_message_captured = True

                                self.logger.info(
                                    f"✅ Stored SystemMessage data in orchestrator metadata (including {len(slash_commands)} slash commands)"
                                )
                            except Exception as e:
                                raise e
                        else:
                            self.logger.debug(
                                "SystemMessage already captured, skipping metadata update"
                            )

                        # SystemMessages are informational - log but don't process as agent output
                        continue

                    # Process AssistantMessage blocks
                    if isinstance(message, AssistantMessage):
                        for block in message.content:

                            # Capture and stream text responses
                            if isinstance(block, TextBlock):
                                response_text += block.text

                                # Save this TextBlock chunk to database immediately
                                try:
                                    message_id = await insert_chat_message(
                                        orchestrator_agent_id=orch_uuid,
                                        sender_type="orchestrator",
                                        receiver_type="user",
                                        message=block.text,
                                        agent_id=None,
                                        metadata={"type": "text_chunk"},
                                    )

                                    # Generate AI summary in background
                                    asyncio.create_task(
                                        self._summarize_and_update_chat(
                                            message_id, block.text
                                        )
                                    )

                                    # Broadcast chunk to event stream with database ID
                                    await self.ws_manager.broadcast(
                                        {
                                            "type": "orchestrator_chat",
                                            "message": {
                                                "id": str(message_id),
                                                "orchestrator_agent_id": str(orch_uuid),
                                                "sender_type": "orchestrator",
                                                "receiver_type": "user",
                                                "message": block.text,
                                                "agent_id": None,
                                                "metadata": {"type": "text_chunk"},
                                                "timestamp": datetime.now().isoformat(),
                                            },
                                        }
                                    )
                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to save TextBlock chunk: {e}"
                                    )

                            # Capture thinking blocks
                            elif isinstance(block, ThinkingBlock):
                                self.logger.debug(
                                    f"Orchestrator thinking: {block.thinking[:100]}..."
                                )

                                # Save ThinkingBlock to system_logs
                                try:
                                    log_id = await insert_system_log(
                                        level="INFO",
                                        message=f"Orchestrator thinking: {block.thinking[:100]}...",
                                        metadata={
                                            "type": "thinking_block",
                                            "thinking": block.thinking,
                                            "orchestrator_agent_id": str(orch_uuid),
                                        },
                                    )

                                    # Generate AI summary in background
                                    asyncio.create_task(
                                        self._summarize_and_update_system_log(
                                            log_id, block.thinking, "thinking"
                                        )
                                    )

                                    # Broadcast thinking block to event stream
                                    await self.ws_manager.broadcast(
                                        {
                                            "type": "thinking_block",
                                            "data": {
                                                "id": str(log_id),
                                                "orchestrator_agent_id": str(orch_uuid),
                                                "thinking": block.thinking,
                                                "timestamp": datetime.now().isoformat(),
                                            },
                                        }
                                    )
                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to save ThinkingBlock: {e}"
                                    )

                            # Track tool usage
                            elif isinstance(block, ToolUseBlock):
                                tools_used.append(block.name)
                                self.logger.info(
                                    f"Orchestrator using tool: {block.name}"
                                )

                                # Save ToolUseBlock to system_logs
                                try:
                                    log_id = await insert_system_log(
                                        level="INFO",
                                        message=f"Orchestrator using tool: {block.name}",
                                        metadata={
                                            "type": "tool_use_block",
                                            "tool_name": block.name,
                                            "tool_input": block.input,
                                            "tool_use_id": block.id,
                                            "orchestrator_agent_id": str(orch_uuid),
                                        },
                                    )

                                    # Generate AI summary in background
                                    asyncio.create_task(
                                        self._summarize_and_update_system_log(
                                            log_id,
                                            f"Using tool: {block.name}",
                                            "tool_use",
                                            {
                                                "tool_name": block.name,
                                                "tool_input": block.input,
                                            },
                                        )
                                    )

                                    # Broadcast tool use block to event stream
                                    await self.ws_manager.broadcast(
                                        {
                                            "type": "tool_use_block",
                                            "data": {
                                                "id": str(log_id),
                                                "orchestrator_agent_id": str(orch_uuid),
                                                "tool_name": block.name,
                                                "tool_input": block.input,
                                                "tool_use_id": block.id,
                                                "timestamp": datetime.now().isoformat(),
                                            },
                                        }
                                    )
                                except Exception as e:
                                    self.logger.error(
                                        f"Failed to save ToolUseBlock: {e}"
                                    )

                    # Capture final session ID and usage
                    elif isinstance(message, ResultMessage):
                        result_message = (
                            message  # Store for cost extraction outside loop
                        )
                        final_session_id = message.session_id
                        usage_data = message.usage

                        # Extract cost from top-level field first (preferred)
                        cost = getattr(message, "total_cost_usd", None) or 0.0

                        # Log full ResultMessage details
                        self.logger.debug(
                            f"[OrchestratorService] ResultMessage received:\n"
                            f"  session_id: {message.session_id}\n"
                            f"  subtype: {getattr(message, 'subtype', 'N/A')}\n"
                            f"  duration_ms: {getattr(message, 'duration_ms', 'N/A')}\n"
                            f"  duration_api_ms: {getattr(message, 'duration_api_ms', 'N/A')}\n"
                            f"  is_error: {getattr(message, 'is_error', False)}\n"
                            f"  num_turns: {getattr(message, 'num_turns', 'N/A')}\n"
                            f"  result: {getattr(message, 'result', 'N/A')}\n"
                            f"  top_level_cost: {cost}\n"
                            f"  usage: {usage_data}\n"
                        )

                        # Fall back to usage cost if top-level is None/0.0
                        if cost == 0.0 and usage_data:
                            if isinstance(usage_data, dict):
                                cost = usage_data.get("total_cost_usd", 0.0)
                            else:
                                cost = getattr(usage_data, "total_cost_usd", 0.0)

                        self.logger.info(
                            f"Orchestrator session complete | "
                            f"turns: {message.num_turns} | "
                            f"cost: ${cost:.4f}"
                        )

            # Clear typing indicator (streaming is complete)
            await self.ws_manager.set_typing_indicator(orchestrator_agent_id, False)

            # Send completion signal to clear typing indicator in chat UI
            await self.ws_manager.broadcast(
                {
                    "type": "chat_stream",
                    "chunk": "",
                    "is_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Orchestrator execution failed: {e}")
            await self.ws_manager.set_typing_indicator(orchestrator_agent_id, False)
            await self.ws_manager.broadcast_error(
                error_message="Orchestrator execution failed", details={"error": str(e)}
            )
            raise

        finally:
            # Always reset execution state when done (success or failure)
            async with self._execution_lock:
                self.is_executing = False
                self.active_client = None
            self.logger.debug("Orchestrator execution state reset")

        # ═══════════════════════════════════════════════════════════
        # PHASE 3: POST-EXECUTION - Log response, update costs
        # ═══════════════════════════════════════════════════════════

        # Update orchestrator's session for next interaction
        if final_session_id:
            self.session_id = final_session_id

            # ONLY update database if this is a NEW orchestrator (didn't start with session_id)
            # For resumed orchestrators (started with --session), we skip database update
            if not self.started_with_session:
                try:
                    await update_orchestrator_session(orch_uuid, final_session_id)
                    self.logger.info(
                        f"Updated database with new session_id: {final_session_id[:20]}..."
                    )
                except Exception as e:
                    self.logger.error(f"Failed to update session: {e}")
            else:
                self.logger.debug(
                    f"Skipping session_id database update (resumed session)"
                )

        # Update costs in database
        # Extract cost from top-level field first (preferred) - using stored result_message
        cost_usd = 0.0
        input_tokens = 0
        output_tokens = 0

        if result_message:
            # Extract cost from top-level field first (preferred)
            cost_usd = getattr(result_message, "total_cost_usd", None) or 0.0

        # Extract token counts from usage dict/object
        if usage_data:
            # Handle both dict and object formats
            if isinstance(usage_data, dict):
                input_tokens = usage_data.get("input_tokens", 0)
                output_tokens = usage_data.get("output_tokens", 0)
                # Fall back to usage cost if top-level is None/0.0
                if cost_usd == 0.0:
                    cost_usd = usage_data.get("total_cost_usd", 0.0)
            else:
                input_tokens = getattr(usage_data, "input_tokens", 0)
                output_tokens = getattr(usage_data, "output_tokens", 0)
                # Fall back to usage cost if top-level is None/0.0
                if cost_usd == 0.0:
                    cost_usd = getattr(usage_data, "total_cost_usd", 0.0)

        # Log what we're about to update
        self.logger.debug(
            f"[OrchestratorService] Updating costs: "
            f"input_tokens={input_tokens}, output_tokens={output_tokens}, cost_usd=${cost_usd:.6f}"
        )

        try:
            # Call database update and get detailed response
            # IMPORTANT: Pass orchestrator_agent_id to ensure we only update THIS agent, not all agents
            update_result = await update_orchestrator_costs(
                orchestrator_agent_id=orch_uuid,
                input_tokens=input_tokens or 0,
                output_tokens=output_tokens or 0,
                cost_usd=cost_usd or 0.0,
            )

            # Log detailed results
            if update_result.get("success"):
                self.logger.info(
                    f"✅ Updated orchestrator costs successfully:\n"
                    f"  Rows Updated: {update_result.get('rows_updated', 0)}\n"
                    f"  Orchestrator ID: {update_result.get('id', 'N/A')}\n"
                    f"  New Total Tokens: {update_result.get('input_tokens', 0) + update_result.get('output_tokens', 0)}\n"
                    f"  New Total Cost: ${update_result.get('total_cost', 0.0):.6f}\n"
                    f"  Updated At: {update_result.get('updated_at', 'N/A')}"
                )

                # Broadcast orchestrator update via WebSocket for live frontend updates
                await self.ws_manager.broadcast_orchestrator_updated(
                    {
                        "id": update_result.get("id"),
                        "input_tokens": update_result.get("input_tokens", 0),
                        "output_tokens": update_result.get("output_tokens", 0),
                        "total_cost": update_result.get("total_cost", 0.0),
                        "updated_at": update_result.get("updated_at"),
                    }
                )
                self.logger.debug("📡 Broadcast orchestrator cost update via WebSocket")
            else:
                self.logger.error(
                    f"❌ Database update reported failure:\n"
                    f"  Error: {update_result.get('error', 'Unknown error')}\n"
                    f"  Rows Updated: {update_result.get('rows_updated', 0)}"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Failed to update costs (exception): {e}", exc_info=True
            )

        # Note: Each TextBlock chunk is saved individually as it streams in
        # This allows real-time display in chat UI
        self.logger.chat_event(
            orchestrator_agent_id, response_text, sender="orchestrator"
        )

        return {
            "ok": True,
            "response": response_text.strip(),
            "session_id": final_session_id or self.session_id,
            "tools_used": tools_used,
            "cost_usd": cost_usd,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    # ═══════════════════════════════════════════════════════════
    # HELPER METHODS - AI Summarization
    # ═══════════════════════════════════════════════════════════

    async def _summarize_and_update_chat(
        self, chat_id: uuid.UUID, message: str
    ) -> None:
        """
        Generate AI summary for chat message and update database (background task).

        Args:
            chat_id: UUID of the chat message to update
            message: The message text content
        """
        try:
            # Build event data for summarization
            event_data = {"content": message}

            # Generate AI summary (uses Claude Haiku for speed/cost)
            summary = await summarize_event(event_data, "text")

            # Update database with summary (only if non-empty)
            if summary and summary.strip():
                await update_chat_summary(chat_id, summary)
                self.logger.debug(
                    f"[OrchestratorService:Summary] Generated summary for chat_id={chat_id}: {summary}"
                )
            else:
                self.logger.warning(
                    f"[OrchestratorService:Summary] Empty summary for chat_id={chat_id}"
                )

        except Exception as e:
            self.logger.error(
                f"[OrchestratorService:Summary] Failed for chat_id={chat_id}: {e}"
            )

    async def _summarize_and_update_system_log(
        self,
        log_id: uuid.UUID,
        message: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Generate AI summary for system log and update database (background task).

        Args:
            log_id: UUID of the system log to update
            message: The log message content
            event_type: Type of event (thinking, tool_use, etc.)
            event_data: Optional additional event data for better summarization
        """
        try:
            # Build event data for summarization
            if event_data is None:
                event_data = {"content": message}
            else:
                # Merge message with event_data
                event_data["content"] = message

            # Generate AI summary (uses Claude Haiku for speed/cost)
            summary = await summarize_event(event_data, event_type)

            # Update database with summary (only if non-empty)
            if summary and summary.strip():
                await update_system_log_summary(log_id, summary)
                self.logger.debug(
                    f"[OrchestratorService:Summary] Generated summary for system_log_id={log_id}: {summary}"
                )
            else:
                self.logger.warning(
                    f"[OrchestratorService:Summary] Empty summary for system_log_id={log_id}"
                )

        except Exception as e:
            self.logger.error(
                f"[OrchestratorService:Summary] Failed for system_log_id={log_id}: {e}"
            )
