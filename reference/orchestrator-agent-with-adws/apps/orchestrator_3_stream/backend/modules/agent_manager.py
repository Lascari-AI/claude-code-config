"""
Agent Manager Module

Centralize agent lifecycle management, tool registration, and background execution.
Implements 8 management tools for the orchestrator agent.
"""

import asyncio
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    tool,
)

from . import config
from .command_agent_hooks import (
    create_post_tool_file_tracking_hook,
    create_post_tool_hook,
    create_pre_compact_hook,
    create_pre_tool_hook,
    create_stop_hook,
    create_subagent_stop_hook,
    create_user_prompt_hook,
)
from .database import (
    # ADW operations
    create_adw,
    create_agent,
    delete_agent,
    get_adw,
    get_adw_logs,
    get_agent,
    get_agent_by_name,
    get_latest_task_slug,
    get_tail_raw,
    get_tail_summaries,
    insert_message_block,
    insert_prompt,
    list_agents,
    update_agent_costs,
    update_agent_session,
    update_agent_status,
    update_log_summary,
    update_prompt_summary,
)
from .file_tracker import FileTracker
from .logger import OrchestratorLogger
from .single_agent_prompt import summarize_event
from .subagent_loader import SubagentRegistry
from .websocket_manager import WebSocketManager


# ADW runner - import at runtime to avoid circular imports
def _get_adw_runner():
    """Lazy import of ADW runner to avoid import issues at module load."""
    import sys
    from pathlib import Path
    # Add adws directory to path if not already there
    adws_path = Path(__file__).parent.parent.parent.parent.parent / "adws"
    if str(adws_path) not in sys.path:
        sys.path.insert(0, str(adws_path))
    from adw_triggers.adw_scripts import run_adw_workflow_async
    return run_adw_workflow_async


class AgentManager:
    """
    Manages agent lifecycle, tool registration, and background execution.
    """

    def __init__(
        self,
        orchestrator_agent_id: uuid.UUID,
        ws_manager: WebSocketManager,
        logger: OrchestratorLogger,
        working_dir: Optional[str] = None,
    ):
        """
        Initialize Agent Manager.

        Args:
            orchestrator_agent_id: UUID of the orchestrator agent (for scoping agents)
            ws_manager: WebSocket manager for broadcasting
            logger: Logger instance
            working_dir: Optional working directory override
        """
        self.orchestrator_agent_id = orchestrator_agent_id
        self.ws_manager = ws_manager
        self.logger = logger
        self.working_dir = working_dir or config.get_working_dir()
        self.active_clients: Dict[str, ClaudeSDKClient] = {}
        self.active_clients_lock = threading.Lock()

        # File tracking registry (keyed by agent_id)
        self.file_trackers: Dict[str, FileTracker] = {}

        # Subagent template registry
        self.subagent_registry = SubagentRegistry(self.working_dir, self.logger)
        template_count = len(self.subagent_registry._templates)
        if template_count > 0:
            self.logger.info(f"Subagent registry initialized with {template_count} template(s)")
        else:
            self.logger.warning("⚠️  No subagent templates available. Agents must be created manually.")

        self.logger.info(
            f"AgentManager initialized for orchestrator {orchestrator_agent_id}"
        )

    def _get_available_workflow_types(self) -> List[str]:
        """
        Discover available ADW workflow types from adws/adw_workflows/*.py files.

        Returns:
            List of workflow type names (e.g., ['feature-development', 'bug-fix'])
        """
        workflow_dir = Path(self.working_dir) / "adws" / "adw_workflows"
        if not workflow_dir.exists():
            return []

        types = []
        for file in workflow_dir.glob("adw_*.py"):
            # Extract type from filename: adw_feature-development.py -> feature-development
            name = file.stem  # adw_feature-development
            if name.startswith("adw_"):
                workflow_type = name[4:]  # Remove "adw_" prefix
                types.append(workflow_type)

        return sorted(types)

    def create_management_tools(self) -> List:
        """
        Create 10 management tools for orchestrator.

        Agent Management Tools (8):
            - create_agent, list_agents, command_agent, check_agent_status
            - delete_agent, interrupt_agent, read_system_logs, report_cost

        ADW Tools (2):
            - start_adw: Start an AI Developer Workflow
            - check_adw: Check ADW status and recent activity

        Returns:
            List of tool callables decorated with @tool
        """

        @tool(
            "create_agent",
            "Create a new agent. REQUIRED: name. OPTIONAL: system_prompt (can be empty if using template), model, subagent_template. Use 'fast' for haiku model. If subagent_template is provided, the template's system prompt, tools, and model will be applied automatically.",
            {"name": str, "system_prompt": str, "model": str, "subagent_template": str},
        )
        async def create_agent_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for creating new agents"""
            try:
                name = args.get("name")
                system_prompt = args.get("system_prompt", "")
                model_input = args.get("model", config.DEFAULT_AGENT_MODEL)
                subagent_template = args.get("subagent_template")

                # Model alias mapping
                model_aliases = {
                    "opus": "claude-opus-4-5-20251101",
                    "sonnet": "claude-sonnet-4-5-20250929",
                    "haiku": "claude-haiku-4-5-20251001",
                    "fast": "claude-haiku-4-5-20251001",  # Alias for haiku
                }

                # Resolve model alias or use as-is
                model = (
                    model_aliases.get(model_input.lower(), model_input)
                    if isinstance(model_input, str)
                    else model_input
                )

                # Validate required fields
                if not name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: 'name' is required",
                            }
                        ],
                        "is_error": True,
                    }

                # system_prompt is only required if no template is provided
                if not system_prompt and not subagent_template:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: Either 'system_prompt' or 'subagent_template' must be provided",
                            }
                        ],
                        "is_error": True,
                    }

                result = await self.create_agent(name, system_prompt, model, subagent_template)

                if result["ok"]:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ Created agent '{name}'\n"
                                f"ID: {result['agent_id']}\n"
                                f"Session: {result['session_id']}\n"
                                f"Model: {model}",
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Failed: {result.get('error', 'Unknown error')}",
                            }
                        ],
                        "is_error": True,
                    }

            except Exception as e:
                self.logger.error(f"create_agent tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "list_agents",
            "List all active agents",
            {},
        )
        async def list_agents_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for listing agents"""
            try:
                agents = await list_agents(self.orchestrator_agent_id, archived=False)

                if not agents:
                    return {"content": [{"type": "text", "text": "No agents found"}]}

                lines = ["📋 Active Agents:\n"]
                for agent in agents:
                    lines.append(
                        f"• {agent.name} (ID: {agent.id})\n"
                        f"  Status: {agent.status}\n"
                        f"  Model: {agent.model}\n"
                        f"  Tokens: {agent.input_tokens + agent.output_tokens}\n"
                        f"  Cost: ${agent.total_cost:.4f}\n"
                    )

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"list_agents tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "command_agent",
            "Send a command to an agent. REQUIRED: agent_name, command.",
            {"agent_name": str, "command": str},
        )
        async def command_agent_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for commanding agents"""
            try:
                agent_name = args.get("agent_name")
                command = args.get("command")

                if not agent_name or not command:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: 'agent_name' and 'command' are required",
                            }
                        ],
                        "is_error": True,
                    }

                # Get agent by name (scoped to this orchestrator)
                agent = await get_agent_by_name(self.orchestrator_agent_id, agent_name)
                if not agent:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Agent '{agent_name}' not found",
                            }
                        ],
                        "is_error": True,
                    }

                # Command agent in background (agent.id is already UUID from Pydantic model)
                asyncio.create_task(self.command_agent(agent.id, command))

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ Command dispatched to '{agent_name}'\n"
                            f"Command: {command[:100]}{'...' if len(command) > 100 else ''}\n"
                            f"Agent will execute in background.",
                        }
                    ]
                }

            except Exception as e:
                self.logger.error(f"command_agent tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "check_agent_status",
            "Check agent status and recent activity. REQUIRED: agent_name.",
            {"agent_name": str, "tail_count": int, "offset": int, "verbose_logs": bool},
        )
        async def check_agent_status_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for checking agent status"""
            try:
                agent_name = args.get("agent_name")
                tail_count = args.get("tail_count", 10)
                offset = args.get("offset", 0)
                verbose_logs = args.get("verbose_logs", False)

                if not agent_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: 'agent_name' is required",
                            }
                        ],
                        "is_error": True,
                    }

                agent = await get_agent_by_name(self.orchestrator_agent_id, agent_name)
                if not agent:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Agent '{agent_name}' not found",
                            }
                        ],
                        "is_error": True,
                    }

                # Use Pydantic model properties
                task_slug = await get_latest_task_slug(agent.id)

                lines = [
                    f"📊 Agent Status: {agent.name}\n",
                    f"Status: {agent.status}\n",
                    f"Model: {agent.model}\n",
                    f"Tokens: {agent.input_tokens + agent.output_tokens}\n",
                    f"Cost: ${agent.total_cost:.4f}\n",
                ]

                if task_slug:
                    lines.append(f"\n🔍 Recent Activity (Task: {task_slug}):\n")

                    # Use verbose or summary mode
                    if verbose_logs:
                        logs = await get_tail_raw(
                            agent.id, task_slug, count=tail_count, offset=offset
                        )
                        for log in logs:
                            lines.append(
                                f"• [{log['event_type']}] {log.get('content', 'No content')}\n"
                                f"  Payload: {log.get('payload', {})}\n"
                            )
                    else:
                        logs = await get_tail_summaries(
                            agent.id, task_slug, count=tail_count, offset=offset
                        )
                        for log in logs:
                            lines.append(
                                f"• [{log['event_type']}] {log.get('summary', 'No summary')}\n"
                            )
                else:
                    lines.append("\nNo recent activity\n")

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"check_agent_status tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "delete_agent",
            "Delete an agent. REQUIRED: agent_name.",
            {"agent_name": str},
        )
        async def delete_agent_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for deleting agents"""
            try:
                agent_name = args.get("agent_name")

                if not agent_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: 'agent_name' is required",
                            }
                        ],
                        "is_error": True,
                    }

                agent = await get_agent_by_name(self.orchestrator_agent_id, agent_name)
                if not agent:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Agent '{agent_name}' not found",
                            }
                        ],
                        "is_error": True,
                    }

                # Use Pydantic model properties
                await delete_agent(agent.id)

                # Clean up file tracker
                if str(agent.id) in self.file_trackers:
                    del self.file_trackers[str(agent.id)]

                # Broadcast deletion (convert UUID to string for JSON)
                await self.ws_manager.broadcast_agent_deleted(str(agent.id))

                return {
                    "content": [
                        {"type": "text", "text": f"✅ Deleted agent '{agent_name}'"}
                    ]
                }

            except Exception as e:
                self.logger.error(f"delete_agent tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "interrupt_agent",
            "Interrupt a running agent. REQUIRED: agent_name.",
            {"agent_name": str},
        )
        async def interrupt_agent_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for interrupting agents"""
            try:
                agent_name = args.get("agent_name")

                if not agent_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "❌ Error: 'agent_name' is required",
                            }
                        ],
                        "is_error": True,
                    }

                with self.active_clients_lock:
                    client = self.active_clients.get(agent_name)

                if client:
                    await client.interrupt()
                    with self.active_clients_lock:
                        del self.active_clients[agent_name]

                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ Interrupted agent '{agent_name}'",
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"⚠️ Agent '{agent_name}' is not currently running",
                            }
                        ]
                    }

            except Exception as e:
                self.logger.error(f"interrupt_agent tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "read_system_logs",
            "Read recent system logs with filtering",
            {"offset": int, "limit": int, "message_contains": str, "level": str},
        )
        async def read_system_logs_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for reading system logs"""
            try:
                from .database import list_system_logs

                offset = args.get("offset", 0)
                limit = args.get("limit", 50)
                message_contains = args.get("message_contains")
                level = args.get("level")

                # Fetch system logs
                logs = await list_system_logs(
                    limit=limit,
                    offset=offset,
                    message_contains=message_contains,
                    level=level,
                )

                if not logs:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "📋 No system logs found matching the criteria",
                            }
                        ]
                    }

                lines = [f"📋 System Logs (showing {len(logs)} of max {limit}):\n\n"]

                for log in logs:
                    timestamp = log.get("timestamp", "N/A")
                    if hasattr(timestamp, "isoformat"):
                        timestamp = timestamp.isoformat()

                    level_str = log.get("level", "INFO")
                    message = log.get("message", "")
                    summary = log.get("summary", "")

                    # Show summary if available, otherwise message
                    display_text = summary if summary else message

                    lines.append(f"[{timestamp}] {level_str}: {display_text}\n")

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"read_system_logs tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "report_cost",
            "Report orchestrator's costs, tokens, and session ID",
            {},
        )
        async def report_cost_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for cost reporting"""
            try:
                from .database import get_orchestrator

                # Get orchestrator agent info
                orch_data = await get_orchestrator()

                if not orch_data:
                    return {
                        "content": [
                            {"type": "text", "text": "❌ Error: Orchestrator not found"}
                        ],
                        "is_error": True,
                    }

                total_tokens = orch_data["input_tokens"] + orch_data["output_tokens"]
                context_percentage = (
                    total_tokens / 200000
                ) * 100  # 200k context window

                lines = [
                    "💰 Orchestrator Cost Report:\n\n",
                    f"Session ID: {orch_data['session_id'] or 'Not set yet'}\n",
                    f"Status: {orch_data['status']}\n\n",
                    f"Total Cost: ${orch_data['total_cost']:.4f}\n",
                    f"Input Tokens: {orch_data['input_tokens']:,}\n",
                    f"Output Tokens: {orch_data['output_tokens']:,}\n",
                    f"Total Tokens: {total_tokens:,}\n",
                    f"Context Usage: {context_percentage:.1f}%\n",
                ]

                # Add warning if approaching context limit
                if context_percentage >= 80:
                    lines.append(
                        f"\n⚠️  Warning: Context usage at {context_percentage:.1f}% - consider compacting soon\n"
                    )

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"report_cost tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        # ═══════════════════════════════════════════════════════════
        # AI DEVELOPER WORKFLOW TOOLS
        # ═══════════════════════════════════════════════════════════

        @tool(
            "start_adw",
            "Start an AI Developer Workflow. REQUIRED: name_of_adw, workflow_type, prompt. OPTIONAL: description. The workflow runs asynchronously - use check_adw to monitor progress. Returns adw_id for tracking.",
            {"name_of_adw": str, "workflow_type": str, "prompt": str, "description": str},
        )
        async def start_adw_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for starting AI Developer Workflows"""
            try:
                name_of_adw = args.get("name_of_adw")
                workflow_type = args.get("workflow_type")
                prompt = args.get("prompt")
                description = args.get("description")

                # Validate required fields
                if not name_of_adw:
                    return {
                        "content": [{"type": "text", "text": "❌ Error: 'name_of_adw' is required"}],
                        "is_error": True,
                    }
                if not workflow_type:
                    return {
                        "content": [{"type": "text", "text": "❌ Error: 'workflow_type' is required"}],
                        "is_error": True,
                    }
                if not prompt:
                    return {
                        "content": [{"type": "text", "text": "❌ Error: 'prompt' is required"}],
                        "is_error": True,
                    }

                # Validate workflow_type exists
                workflow_file = Path(self.working_dir) / "adws" / "adw_workflows" / f"adw_{workflow_type}.py"
                if not workflow_file.exists():
                    available = self._get_available_workflow_types()
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Error: Workflow type '{workflow_type}' not found.\n"
                                        f"Available types: {', '.join(available) if available else 'None'}\n"
                                        f"Expected file: adws/adw_workflows/adw_{workflow_type}.py",
                            }
                        ],
                        "is_error": True,
                    }

                # Create ADW record in database (stores prompt + working_dir in input_data)
                adw_record = await create_adw(
                    orchestrator_agent_id=self.orchestrator_agent_id,
                    adw_name=name_of_adw,
                    workflow_type=workflow_type,
                    prompt=prompt,
                    working_dir=self.working_dir,
                    description=description,
                )

                adw_id = str(adw_record["id"])

                # Log and broadcast
                self.logger.info(f"🚀 Started ADW '{name_of_adw}' (type: {workflow_type}) with ID: {adw_id}")
                await self.ws_manager.broadcast({
                    "type": "adw_started",
                    "data": {
                        "adw_id": adw_id,
                        "adw_name": name_of_adw,
                        "workflow_type": workflow_type,
                        "status": "pending",
                    }
                })

                # Trigger the workflow execution in background
                # Note: working_dir is already stored in DB via create_adw above
                run_adw = _get_adw_runner()
                runner_result = await run_adw(
                    adw_id=adw_id,
                    workflow_type=workflow_type,
                )

                if runner_result.get("status") == "error":
                    self.logger.error(f"ADW runner error: {runner_result.get('error')}")
                    return {
                        "content": [{"type": "text", "text": f"❌ Failed to start workflow: {runner_result.get('error')}"}],
                        "is_error": True,
                    }

                pid = runner_result.get("pid", "unknown")
                self.logger.info(f"ADW workflow started with PID: {pid}")

                lines = [
                    f"✅ Started AI Developer Workflow\n\n",
                    f"ADW ID: {adw_id}\n",
                    f"Name: {name_of_adw}\n",
                    f"Type: {workflow_type}\n",
                    f"Status: running (PID: {pid})\n\n",
                    f"Use check_adw(adw_id=\"{adw_id}\") to monitor progress.\n",
                    f"⚠️  Note: Do NOT interfere with the ADW unless explicitly asked.",
                ]

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"start_adw tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        @tool(
            "check_adw",
            "Check ADW status and recent activity. REQUIRED: adw_id. OPTIONAL: tail_count (default 10), event_type (filter by StepStart/StepEnd/etc), include_step_details (default false).",
            {"adw_id": str, "tail_count": int, "event_type": str, "include_step_details": bool},
        )
        async def check_adw_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """Tool for checking AI Developer Workflow status"""
            try:
                adw_id_str = args.get("adw_id")
                tail_count = args.get("tail_count", 10)
                event_type = args.get("event_type")
                include_step_details = args.get("include_step_details", False)

                if not adw_id_str:
                    return {
                        "content": [{"type": "text", "text": "❌ Error: 'adw_id' is required"}],
                        "is_error": True,
                    }

                # Parse UUID
                try:
                    adw_id = uuid.UUID(adw_id_str)
                except ValueError:
                    return {
                        "content": [{"type": "text", "text": f"❌ Error: Invalid adw_id format: {adw_id_str}"}],
                        "is_error": True,
                    }

                # Get ADW record
                adw = await get_adw(adw_id)
                if not adw:
                    return {
                        "content": [{"type": "text", "text": f"❌ ADW '{adw_id_str}' not found"}],
                        "is_error": True,
                    }

                # Get recent logs
                logs = await get_adw_logs(
                    adw_id=adw_id,
                    limit=tail_count,
                    event_type=event_type,
                    include_payload=include_step_details,
                )

                # Build status display
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(adw["status"], "❓")

                lines = [
                    f"📊 ADW Status: {adw['adw_name']}\n\n",
                    f"Status: {status_icon} {adw['status']}\n",
                    f"Type: {adw['workflow_type']}\n",
                    f"Progress: {adw['completed_steps']}/{adw['total_steps']} steps\n",
                ]

                if adw["current_step"]:
                    lines.append(f"Current Step: {adw['current_step']}\n")

                if adw["started_at"]:
                    lines.append(f"Started: {adw['started_at']}\n")

                if adw["duration_seconds"]:
                    lines.append(f"Duration: {adw['duration_seconds']}s\n")

                if adw["error_message"]:
                    lines.append(f"\n⚠️  Error: {adw['error_message']}\n")
                    if adw["error_step"]:
                        lines.append(f"Error Step: {adw['error_step']}\n")

                # Add recent events
                if logs:
                    filter_note = f" (filtered by: {event_type})" if event_type else ""
                    lines.append(f"\n🔍 Recent Activity{filter_note}:\n")
                    for log in logs:
                        step_info = f"[{log['adw_step']}] " if log.get("adw_step") else ""
                        summary = log.get("summary") or log.get("event_type", "No summary")
                        lines.append(f"• {step_info}{log['event_type']}: {summary}\n")
                        if include_step_details and log.get("payload"):
                            lines.append(f"  Payload: {log['payload']}\n")
                else:
                    lines.append("\nNo recent activity\n")

                return {"content": [{"type": "text", "text": "".join(lines)}]}

            except Exception as e:
                self.logger.error(f"check_adw tool error: {e}", exc_info=True)
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return [
            create_agent_tool,
            list_agents_tool,
            command_agent_tool,
            check_agent_status_tool,
            delete_agent_tool,
            interrupt_agent_tool,
            read_system_logs_tool,
            report_cost_tool,
            start_adw_tool,
            check_adw_tool,
        ]

    async def create_agent(
        self, name: str, system_prompt: str, model: Optional[str] = None, subagent_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent.

        Args:
            name: Unique agent name
            system_prompt: Agent's system prompt (can be empty if using template)
            model: Optional model override
            subagent_template: Optional template name to use

        Returns:
            Dict with ok, agent_id, session_id, or error
        """
        try:
            # Handle template-based creation
            metadata = {}
            allowed_tools = None  # Will use defaults if not specified

            if subagent_template:
                self.logger.info(f"Creating agent '{name}' using template '{subagent_template}'")

                # Fetch template
                template = self.subagent_registry.get_template(subagent_template)

                if not template:
                    # Template not found - provide helpful error
                    available = self.subagent_registry.get_available_names()
                    available_str = ', '.join(available) if available else 'None - create templates in .claude/agents/'
                    self.logger.error(f"❌ Template '{subagent_template}' not found")
                    self.logger.info(f"Available templates: {available_str}")
                    return {
                        "ok": False,
                        "error": f"Template '{subagent_template}' not found. Available: {available_str}",
                        "suggestion": "Create templates in .claude/agents/ directory or use manual agent creation"
                    }

                # Apply template configuration
                system_prompt = template.prompt_body
                if template.frontmatter.model:
                    model = template.frontmatter.model
                allowed_tools = template.frontmatter.tools

                # Add template metadata
                metadata = {
                    "template_name": template.frontmatter.name,
                    "template_color": template.frontmatter.color,
                }

                # Log template application
                if template.frontmatter.tools:
                    tool_count = len(template.frontmatter.tools)
                    self.logger.info(f"Applying template '{template.frontmatter.name}': {tool_count} tools, model={model or 'default'}")
                else:
                    self.logger.info(f"Applying template '{template.frontmatter.name}': all default tools, model={model or 'default'}")

            # Check if agent name already exists (scoped to this orchestrator)
            existing = await get_agent_by_name(self.orchestrator_agent_id, name)
            if existing:
                self.logger.warning(f"Attempted to create agent with duplicate name: {name}")
                return {
                    "ok": False,
                    "error": f"❌ Agent name '{name}' is already in use. Please choose a different name."
                }

            # Create agent in database (scoped to this orchestrator)
            agent_id = await create_agent(
                orchestrator_agent_id=self.orchestrator_agent_id,
                name=name,
                model=model or config.DEFAULT_AGENT_MODEL,
                system_prompt=system_prompt,
                working_dir=self.working_dir,
                metadata=metadata,
            )

            # Initialize file tracker for this agent
            self.file_trackers[str(agent_id)] = FileTracker(
                agent_id, name, self.working_dir
            )

            # Initialize agent with greeting
            task_slug = f"{name}-greeting"
            entry_counter = {"count": 0}

            hooks_dict = self._build_hooks_for_agent(
                agent_id, name, task_slug, entry_counter
            )

            # For agent creation, disallow all tools - agent only needs to acknowledge initialization
            # Tools will be enabled later during command_agent calls when actual work is performed
            tools_to_use = []  # No tools during initialization

            # Pass ANTHROPIC_API_KEY explicitly to ensure subprocess has access
            env_vars = {}
            if "ANTHROPIC_API_KEY" in os.environ:
                env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

            options = ClaudeAgentOptions(
                system_prompt=system_prompt,
                model=model or config.DEFAULT_AGENT_MODEL,
                cwd=self.working_dir,
                hooks=hooks_dict,
                allowed_tools=tools_to_use,  # Empty list = no tools during init
                permission_mode="acceptEdits",
                env=env_vars,  # Ensure API key is available to subprocess
                setting_sources=["project"],  # Load CLAUDE.md and slash commands
            )

            async with ClaudeSDKClient(options=options) as client:
                # Load initialization prompt from file
                init_prompt_path = Path(config.BACKEND_DIR) / "prompts" / "command_level_agent_init_user_prompt.md"
                init_prompt = init_prompt_path.read_text().strip()

                await client.query(init_prompt)

                session_id = await self._process_agent_messages(
                    client, agent_id, name, task_slug, entry_counter
                )

            # Update session in database
            await update_agent_session(agent_id, session_id)

            # Broadcast creation
            await self.ws_manager.broadcast_agent_created(
                {
                    "id": str(agent_id),
                    "name": name,
                    "model": model or config.DEFAULT_AGENT_MODEL,
                    "status": "idle",
                }
            )

            self.logger.info(f"Created agent '{name}' with ID {agent_id}")

            return {"ok": True, "agent_id": str(agent_id), "session_id": session_id}

        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}

    async def command_agent(
        self, agent_id: uuid.UUID, command: str, task_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send command to agent.

        Args:
            agent_id: UUID of agent
            command: Command text
            task_slug: Optional task identifier

        Returns:
            Dict with ok, task_slug, or error
        """
        try:
            agent = await get_agent(agent_id)
            if not agent:
                return {"ok": False, "error": "Agent not found"}

            # Ensure file tracker exists for this agent
            if str(agent_id) not in self.file_trackers:
                self.file_trackers[str(agent_id)] = FileTracker(
                    agent_id, agent.name, agent.working_dir or self.working_dir
                )

            # Generate task slug if not provided
            if not task_slug:
                # Create slug from command (first 50 chars, kebab-case)
                slug_base = re.sub(r"[^a-z0-9]+", "-", command[:50].lower()).strip("-")
                task_slug = f"{slug_base}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            entry_counter = {"count": 0}

            # Insert prompt to database
            prompt_id = await insert_prompt(
                agent_id=agent_id,
                task_slug=task_slug,
                author="orchestrator_agent",
                prompt_text=command,
                session_id=agent.session_id,
            )

            # Generate AI summary in background
            asyncio.create_task(self._summarize_and_update_prompt(prompt_id, command))

            # Build hooks
            hooks_dict = self._build_hooks_for_agent(
                agent_id, agent.name, task_slug, entry_counter
            )

            # Default allowed tools - comprehensive set for general work
            default_allowed = [
                "Read",
                "Write",
                "Edit",
                "Bash",
                "Glob",
                "Grep",
                "Task",
                "WebFetch",
                "WebSearch",
                "BashOutput",
                "SlashCommand",
                "TodoWrite",
                "KillShell",
                "AskUserQuestion",
                "Skill",
            ]

            default_disallowed = ["NotebookEdit", "ExitPlanMode"]

            # Pass ANTHROPIC_API_KEY explicitly to ensure subprocess has access
            env_vars = {}
            if "ANTHROPIC_API_KEY" in os.environ:
                env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

            # Build options with session resume (use Pydantic model properties)
            options = ClaudeAgentOptions(
                system_prompt=agent.system_prompt,
                model=agent.model,
                cwd=agent.working_dir,
                resume=agent.session_id,
                hooks=hooks_dict,
                max_turns=config.MAX_AGENT_TURNS,
                allowed_tools=default_allowed,
                disallowed_tools=default_disallowed,
                permission_mode="acceptEdits",
                env=env_vars,  # Ensure API key is available to subprocess
                setting_sources=["project"],  # Load CLAUDE.md and slash commands
            )

            # Update status to executing
            await update_agent_status(agent_id, "executing")
            await self.ws_manager.broadcast_agent_status_change(
                str(agent_id), "idle", "executing"
            )

            # Execute agent
            async with ClaudeSDKClient(options=options) as client:
                # Track in active clients for interrupt
                with self.active_clients_lock:
                    self.active_clients[agent.name] = client

                await client.query(command)

                session_id = await self._process_agent_messages(
                    client, agent_id, agent.name, task_slug, entry_counter
                )

                # Remove from active clients
                with self.active_clients_lock:
                    self.active_clients.pop(agent.name, None)

            # Update session and status
            await update_agent_session(agent_id, session_id)
            await update_agent_status(agent_id, "idle")
            await self.ws_manager.broadcast_agent_status_change(
                str(agent_id), "executing", "idle"
            )

            self.logger.info(f"Agent '{agent.name}' completed task: {task_slug}")

            return {"ok": True, "task_slug": task_slug}

        except Exception as e:
            self.logger.error(f"Failed to command agent: {e}", exc_info=True)
            await update_agent_status(agent_id, "blocked")
            return {"ok": False, "error": str(e)}

    def _build_hooks_for_agent(
        self,
        agent_id: uuid.UUID,
        agent_name: str,
        task_slug: str,
        entry_counter: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Build hooks dictionary for agent.

        Args:
            agent_id: UUID of agent
            agent_name: Name of the agent
            task_slug: Task identifier
            entry_counter: Mutable counter dict

        Returns:
            Hooks dict for ClaudeAgentOptions
        """
        # Get file tracker for this agent
        file_tracker = self.file_trackers.get(str(agent_id))

        # Build PostToolUse hooks list
        post_tool_hooks = [
            create_post_tool_hook(
                agent_id,
                agent_name,
                task_slug,
                entry_counter,
                self.logger,
                self.ws_manager,
            )
        ]

        # Add file tracking hook if file_tracker exists
        if file_tracker:
            post_tool_hooks.append(
                create_post_tool_file_tracking_hook(
                    file_tracker,
                    agent_id,
                    agent_name,
                    self.logger,
                )
            )

        return {
            "PreToolUse": [
                HookMatcher(
                    hooks=[
                        create_pre_tool_hook(
                            agent_id,
                            agent_name,
                            task_slug,
                            entry_counter,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                )
            ],
            "PostToolUse": [HookMatcher(hooks=post_tool_hooks)],
            "UserPromptSubmit": [
                HookMatcher(
                    hooks=[
                        create_user_prompt_hook(
                            agent_id,
                            agent_name,
                            task_slug,
                            entry_counter,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                )
            ],
            "Stop": [
                HookMatcher(
                    hooks=[
                        create_stop_hook(
                            agent_id,
                            agent_name,
                            task_slug,
                            entry_counter,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                )
            ],
            "SubagentStop": [
                HookMatcher(
                    hooks=[
                        create_subagent_stop_hook(
                            agent_id,
                            agent_name,
                            task_slug,
                            entry_counter,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                )
            ],
            "PreCompact": [
                HookMatcher(
                    hooks=[
                        create_pre_compact_hook(
                            agent_id,
                            agent_name,
                            task_slug,
                            entry_counter,
                            self.logger,
                            self.ws_manager,
                        )
                    ]
                )
            ],
        }

    async def _process_agent_messages(
        self,
        client: ClaudeSDKClient,
        agent_id: uuid.UUID,
        agent_name: str,
        task_slug: str,
        entry_counter: Dict[str, int],
    ) -> Optional[str]:
        """
        Process agent messages and log to database.

        Args:
            client: Claude SDK client
            agent_id: UUID of agent
            agent_name: Name of agent
            task_slug: Task identifier
            entry_counter: Mutable counter

        Returns:
            Final session_id
        """
        session_id = None
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        last_text_block_id = None  # Track last TextBlock for file tracking attachment
        text_block_count = 0
        thinking_block_count = 0
        tool_use_block_count = 0

        try:
            self.logger.debug(f"[AgentManager] Starting message processing for agent={agent_name} task={task_slug}")
            async for message in client.receive_response():
                self.logger.debug(f"[AgentManager] Received message type: {type(message).__name__}")

                if isinstance(message, SystemMessage):
                    # SystemMessage has subtype and data fields (not content)
                    # Log it with full details to understand what's happening
                    subtype = getattr(message, 'subtype', 'unknown')
                    data = getattr(message, 'data', {})

                    self.logger.warning(
                        f"[AgentManager] SystemMessage received for agent={agent_name} task={task_slug}:\n"
                        f"  Subtype: {subtype}\n"
                        f"  Data: {data}\n"
                    )

                    # SystemMessages are informational - log but don't process as agent output
                    continue

                if isinstance(message, AssistantMessage):
                    self.logger.debug(f"[AgentManager] AssistantMessage has {len(message.content)} blocks")
                    for block in message.content:
                        entry_index = entry_counter["count"]
                        entry_counter["count"] += 1
                        self.logger.debug(f"[AgentManager] Processing block type: {type(block).__name__}")

                        if isinstance(block, TextBlock):
                            text_block_count += 1
                            block_id = await insert_message_block(
                                agent_id=agent_id,
                                task_slug=task_slug,
                                entry_index=entry_index,
                                block_type="text",
                                content=block.text,
                                payload={"text": block.text},
                            )

                            # Track this as the last TextBlock for file tracking attachment
                            last_text_block_id = block_id

                            # Spawn async summarization
                            asyncio.create_task(
                                self._summarize_and_update_block(
                                    block_id, agent_id, "text", {"content": block.text}
                                )
                            )

                            # Broadcast agent text response via WebSocket
                            await self.ws_manager.broadcast_agent_log(
                                {
                                    "id": str(block_id),
                                    "agent_id": str(agent_id),
                                    "agent_name": agent_name,
                                    "task_slug": task_slug,
                                    "entry_index": entry_index,
                                    "event_category": "response",
                                    "event_type": "TextBlock",
                                    "content": block.text,
                                    "summary": block.text,
                                    "payload": {"text": block.text},
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                            self.logger.debug(
                                f"Broadcast TextBlock for agent {agent_name}"
                            )

                        elif isinstance(block, ThinkingBlock):
                            thinking_block_count += 1
                            block_id = await insert_message_block(
                                agent_id=agent_id,
                                task_slug=task_slug,
                                entry_index=entry_index,
                                block_type="thinking",
                                content=block.thinking,
                                payload={"thinking": block.thinking},
                            )

                            # Spawn async summarization
                            asyncio.create_task(
                                self._summarize_and_update_block(
                                    block_id,
                                    agent_id,
                                    "thinking",
                                    {"content": block.thinking},
                                )
                            )

                            # Broadcast agent thinking via WebSocket
                            await self.ws_manager.broadcast_agent_log(
                                {
                                    "id": str(block_id),
                                    "agent_id": str(agent_id),
                                    "agent_name": agent_name,
                                    "task_slug": task_slug,
                                    "entry_index": entry_index,
                                    "event_category": "response",
                                    "event_type": "ThinkingBlock",
                                    "content": block.thinking,
                                    "summary": "[Agent is thinking]",
                                    "payload": {"thinking": block.thinking},
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                            self.logger.debug(
                                f"Broadcast ThinkingBlock for agent {agent_name}"
                            )

                        elif isinstance(block, ToolUseBlock):
                            tool_use_block_count += 1
                            block_id = await insert_message_block(
                                agent_id=agent_id,
                                task_slug=task_slug,
                                entry_index=entry_index,
                                block_type="tool_use",
                                content=None,
                                payload={
                                    "tool_name": block.name,
                                    "tool_input": block.input,
                                    "tool_use_id": block.id,
                                },
                            )

                            # Spawn async summarization
                            asyncio.create_task(
                                self._summarize_and_update_block(
                                    block_id,
                                    agent_id,
                                    "tool_use",
                                    {
                                        "tool_name": block.name,
                                        "tool_input": block.input,
                                    },
                                )
                            )

                            # Broadcast agent tool use via WebSocket
                            await self.ws_manager.broadcast_agent_log(
                                {
                                    "id": str(block_id),
                                    "agent_id": str(agent_id),
                                    "agent_name": agent_name,
                                    "task_slug": task_slug,
                                    "entry_index": entry_index,
                                    "event_category": "response",
                                    "event_type": "ToolUseBlock",
                                    "content": f"[Tool] {block.name}",
                                    "summary": f"Using tool: {block.name}",
                                    "payload": {
                                        "tool_name": block.name,
                                        "tool_input": block.input,
                                        "tool_use_id": block.id,
                                    },
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                            self.logger.debug(
                                f"Broadcast ToolUseBlock for agent {agent_name}"
                            )

                elif isinstance(message, ResultMessage):
                    session_id = message.session_id

                    # Capture file changes for this agent and broadcast as separate event
                    file_tracker = self.file_trackers.get(str(agent_id))
                    if file_tracker and last_text_block_id:
                        try:
                            # Generate summaries (async)
                            modified_files_summary = (
                                await file_tracker.generate_file_changes_summary()
                            )
                            read_files_summary = (
                                file_tracker.generate_read_files_summary()
                            )

                            # Only broadcast if there are file operations
                            if modified_files_summary or read_files_summary:
                                # Import Pydantic model for type safety
                                import uuid

                                from .file_tracker import AgentLogMetadata

                                # Build metadata using Pydantic model
                                file_metadata = AgentLogMetadata(
                                    file_changes=modified_files_summary,
                                    read_files=read_files_summary,
                                    total_files_modified=len(modified_files_summary),
                                    total_files_read=len(read_files_summary),
                                    generated_at=datetime.now(timezone.utc).isoformat(),
                                )

                                # IMPORTANT: Update the TextBlock in database with file tracking data
                                # This ensures file changes persist and show up on page refresh
                                from .database import update_log_payload
                                await update_log_payload(
                                    last_text_block_id,
                                    file_metadata.model_dump()
                                )

                                # Broadcast as separate FileTrackingBlock event for real-time WebSocket updates
                                await self.ws_manager.broadcast_agent_log(
                                    {
                                        "id": str(uuid.uuid4()),  # New unique ID for this event
                                        "parent_log_id": str(last_text_block_id),  # Link to parent TextBlock
                                        "agent_id": str(agent_id),
                                        "agent_name": agent_name,
                                        "task_slug": task_slug,
                                        "event_category": "file_tracking",
                                        "event_type": "FileTrackingBlock",
                                        "content": f"📂 {len(modified_files_summary)} modified, {len(read_files_summary)} read",
                                        "summary": f"File tracking: {len(modified_files_summary)} modified, {len(read_files_summary)} read",
                                        "payload": file_metadata.model_dump(),
                                        "timestamp": datetime.now(
                                            timezone.utc
                                        ).isoformat(),
                                    }
                                )

                                self.logger.info(
                                    f"[FileTracker] Agent={agent_name} Modified={len(modified_files_summary)} Read={len(read_files_summary)} | Stored in DB"
                                )
                        except Exception as e:
                            self.logger.error(
                                f"Error capturing file changes: {e}", exc_info=True
                            )

                    # Extract cost from top-level field first (preferred)
                    total_cost = getattr(message, "total_cost_usd", None) or 0.0

                    # Extract token counts from usage dict/object
                    if message.usage:
                        usage = message.usage
                        if isinstance(usage, dict):
                            total_input_tokens = usage.get("input_tokens", 0)
                            total_output_tokens = usage.get("output_tokens", 0)
                            # Fall back to usage cost if top-level is None/0.0
                            if total_cost == 0.0:
                                total_cost = usage.get("total_cost_usd", 0.0)
                        else:
                            total_input_tokens = getattr(usage, "input_tokens", 0)
                            total_output_tokens = getattr(usage, "output_tokens", 0)
                            # Fall back to usage cost if top-level is None/0.0
                            if total_cost == 0.0:
                                total_cost = getattr(usage, "total_cost_usd", 0.0)

            # Update costs in database
            if total_input_tokens or total_output_tokens:
                await update_agent_costs(
                    agent_id, total_input_tokens, total_output_tokens, total_cost
                )

                # Fetch updated agent to get cumulative totals
                updated_agent = await get_agent(agent_id)

                if updated_agent:
                    # Broadcast updated token/cost data to frontend
                    await self.ws_manager.broadcast_agent_updated(
                        agent_id=str(agent_id),
                        agent_data={
                            "input_tokens": updated_agent.input_tokens,
                            "output_tokens": updated_agent.output_tokens,
                            "total_cost": float(updated_agent.total_cost)
                        }
                    )

                    self.logger.debug(
                        f"Broadcast token update for agent {updated_agent.name} ({agent_id}): "
                        f"in={updated_agent.input_tokens}, out={updated_agent.output_tokens}, "
                        f"cost=${float(updated_agent.total_cost):.4f}"
                    )

        except Exception as e:
            self.logger.error(f"Error processing agent messages: {e}", exc_info=True)
            raise  # Re-raise to let command_agent handle the error properly

        finally:
            # Log summary of what we processed
            self.logger.info(
                f"[AgentManager] Processed agent={agent_name} task={task_slug}: "
                f"TextBlocks={text_block_count}, ThinkingBlocks={thinking_block_count}, "
                f"ToolUseBlocks={tool_use_block_count}"
            )

        return session_id

    # ═══════════════════════════════════════════════════════════
    # HELPER METHODS - AI Summarization
    # ═══════════════════════════════════════════════════════════

    async def _summarize_and_update_prompt(
        self, prompt_id: uuid.UUID, prompt_text: str
    ) -> None:
        """
        Generate AI summary for prompt and update database (background task).

        Args:
            prompt_id: UUID of the prompt to update
            prompt_text: The prompt text content
        """
        try:
            # Build event data for summarization
            event_data = {"prompt": prompt_text}

            # Generate AI summary (uses Claude Haiku for speed/cost)
            summary = await summarize_event(event_data, "UserPromptSubmit")

            # Update database with summary (only if non-empty)
            if summary and summary.strip():
                await update_prompt_summary(prompt_id, summary)
                self.logger.debug(
                    f"[AgentManager:Summary] Generated summary for prompt_id={prompt_id}: {summary}"
                )
            else:
                self.logger.warning(
                    f"[AgentManager:Summary] Empty summary for prompt_id={prompt_id}"
                )

        except Exception as e:
            self.logger.error(
                f"[AgentManager:Summary] Failed for prompt_id={prompt_id}: {e}"
            )

    async def _summarize_and_update_block(
        self,
        block_id: uuid.UUID,
        agent_id: uuid.UUID,
        block_type: str,
        event_data: Dict[str, Any],
    ) -> None:
        """
        Generate AI summary for message block and update database (background task).

        Args:
            block_id: UUID of the block to update
            agent_id: UUID of the agent this block belongs to
            block_type: Type of block (text, thinking, tool_use)
            event_data: Event data for summarization
        """
        try:
            # Generate AI summary (uses Claude Haiku for speed/cost)
            summary = await summarize_event(event_data, block_type)

            # Update database with summary (only if non-empty)
            if summary and summary.strip():
                await update_log_summary(block_id, summary)
                self.logger.debug(
                    f"[AgentManager:Summary] Generated summary for block_id={block_id}: {summary}"
                )

                # Broadcast the latest summary for this agent to frontend
                await self.ws_manager.broadcast_agent_summary_update(
                    agent_id=str(agent_id), summary=summary
                )
            else:
                self.logger.warning(
                    f"[AgentManager:Summary] Empty summary for block_id={block_id}"
                )

        except Exception as e:
            self.logger.error(
                f"[AgentManager:Summary] Failed for block_id={block_id}: {e}"
            )
