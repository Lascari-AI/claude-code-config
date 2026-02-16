# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg>=0.29.0",
#   "python-dotenv>=1.0.0",
#   "pydantic>=2.0",
#   "claude-agent-sdk>=0.1.18",
#   "rich>=13.0",
#   "websockets>=12.0",
# ]
# ///
"""
ADW Plan-Build Workflow - Two-step workflow: plan then build.

This workflow:
1. Receives --adw-id as CLI arg
2. Fetches prompt and working_dir from DB
3. Runs /plan <prompt> agent
4. Extracts plan file path via quick_prompt
5. Runs /build <path> agent
6. Logs all events to agent_logs for swimlane visualization

Usage:
    uv run adws/adw_workflows/adw_plan_build.py --adw-id <uuid>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.adw_agent_sdk import (
    AdhocPrompt,
    HookContext,
    HookInput,
    HookMatcher,
    HookResponse,
    HooksConfig,
    MessageHandlers,
    ModelName,
    PostToolUseInput,
    PreToolUseInput,
    QueryInput,
    QueryOptions,
    ResultMessage,
    StopInput,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    query_to_completion,
    quick_prompt,
)
from adw_modules.adw_database import (
    create_agent,
    get_adw,
    update_agent,
    update_log_summary,
)
from adw_modules.adw_logging import (
    close_logging,
    init_logging,
    log_adw_event,
    log_step_end,
    log_step_start,
    log_system_event,
    update_adw_status,
)
from adw_modules.adw_summarizer import summarize_event
from adw_modules.adw_websockets import broadcast_adw_event_summary_update

load_dotenv()

console = Console()

# =============================================================================
# CONSTANTS
# =============================================================================

STEP_PLAN = "plan"
STEP_BUILD = "build"
TOTAL_STEPS = 2


# =============================================================================
# HOOK FACTORY - Creates hooks that log to DB
# =============================================================================


def create_logging_hooks(adw_id: str, adw_step: str, agent_id: str) -> HooksConfig:
    """Create hooks that log tool and lifecycle events to agent_logs.

    Captures:
    - PreToolUse: Before each tool execution
    - PostToolUse: After each tool execution (with results)
    - Stop: When the agent stops

    Args:
        adw_id: The ADW ID for logging
        adw_step: Current step slug (e.g., "plan", "build")
        agent_id: The agent ID for logging

    Returns:
        HooksConfig with all logging hooks
    """

    def _get_tool_summary(tool_name: str, tool_input: dict) -> str:
        """Build a human-readable summary for a tool call."""
        if tool_name == "Read" and "file_path" in tool_input:
            file_name = Path(tool_input["file_path"]).name
            return f"Read: {file_name}"
        elif tool_name == "Write" and "file_path" in tool_input:
            file_name = Path(tool_input["file_path"]).name
            return f"Write: {file_name}"
        elif tool_name == "Edit" and "file_path" in tool_input:
            file_name = Path(tool_input["file_path"]).name
            return f"Edit: {file_name}"
        elif tool_name == "Bash" and "command" in tool_input:
            cmd = tool_input["command"][:40]
            return f"Bash: {cmd}..."
        elif tool_name == "Glob" and "pattern" in tool_input:
            return f"Glob: {tool_input['pattern']}"
        elif tool_name == "Grep" and "pattern" in tool_input:
            return f"Grep: {tool_input['pattern']}"
        elif tool_name == "Skill" and "skill" in tool_input:
            return f"Skill: /{tool_input['skill']}"
        elif tool_name == "Task":
            desc = tool_input.get("description", "")[:30]
            return f"Task: {desc}..."
        return f"Tool: {tool_name}"

    async def pre_tool_use_hook(
        hook_input: HookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> HookResponse:
        """Log tool call BEFORE execution."""
        if not isinstance(hook_input, PreToolUseInput):
            return HookResponse.allow()

        tool_name = hook_input.tool_name
        tool_input = hook_input.tool_input
        summary = _get_tool_summary(tool_name, tool_input)

        await log_adw_event(
            adw_id=adw_id,
            adw_step=adw_step,
            event_category="hook",
            event_type="PreToolUse",
            content=f"Using tool: {tool_name}",
            agent_id=agent_id,
            payload={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_use_id": tool_use_id,
            },
            summary=summary,
        )

        return HookResponse.allow()

    async def post_tool_use_hook(
        hook_input: HookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> HookResponse:
        """Log tool usage AFTER execution with results."""
        if not isinstance(hook_input, PostToolUseInput):
            return HookResponse.allow()

        tool_name = hook_input.tool_name
        tool_input = hook_input.tool_input
        summary = _get_tool_summary(tool_name, tool_input) + " ✓"

        await log_adw_event(
            adw_id=adw_id,
            adw_step=adw_step,
            event_category="hook",
            event_type="PostToolUse",
            content=f"PostToolUse: {tool_name}",
            agent_id=agent_id,
            payload={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_use_id": tool_use_id,
                "tool_response": str(hook_input.tool_response)
                if hook_input.tool_response
                else None,
            },
            summary=summary,
        )

        return HookResponse.allow()

    async def stop_hook(
        hook_input: HookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> HookResponse:
        """Log when agent stops."""
        if not isinstance(hook_input, StopInput):
            return HookResponse.allow()

        reason = getattr(hook_input, "reason", "unknown")
        await log_adw_event(
            adw_id=adw_id,
            adw_step=adw_step,
            event_category="hook",
            event_type="Stop",
            content=f"Agent stopped: {reason}",
            agent_id=agent_id,
            payload={"reason": reason},
            summary=f"Stop: {reason}",
        )

        return HookResponse.allow()

    return HooksConfig(
        pre_tool_use=[
            HookMatcher(
                matcher=None,
                hooks=[pre_tool_use_hook],
                timeout=30,
            )
        ],
        post_tool_use=[
            HookMatcher(
                matcher=None,
                hooks=[post_tool_use_hook],
                timeout=30,
            )
        ],
        stop=[
            HookMatcher(
                matcher=None,
                hooks=[stop_hook],
                timeout=30,
            )
        ],
    )


# =============================================================================
# MESSAGE HANDLERS - Log agent response blocks
# =============================================================================


async def _summarize_and_update(log_id: str, adw_id: str, event_data: dict, event_type: str) -> None:
    """Background task to generate AI summary, update DB, and broadcast to frontend.

    Args:
        log_id: The log entry ID to update
        adw_id: The ADW ID for WebSocket broadcast
        event_data: Event data for summarization
        event_type: Type of event (TextBlock, ThinkingBlock, ToolUseBlock, etc.)
    """
    try:
        summary = await summarize_event(event_data, event_type)
        if summary and summary.strip():
            # Update database
            await update_log_summary(log_id, summary)
            # Broadcast to frontend so UI updates in real-time
            await broadcast_adw_event_summary_update(adw_id, log_id, summary)
    except Exception as e:
        # Log but don't fail - summary is non-critical
        console.print(f"[dim red]Summary generation failed: {e}[/dim red]")


def create_message_handlers(adw_id: str, adw_step: str, agent_id: str) -> MessageHandlers:
    """Create handlers that log agent message blocks to agent_logs.

    Captures individual blocks for granular visualization:
    - TextBlock: Agent text responses
    - ThinkingBlock: Agent thinking/reasoning
    - ToolUseBlock: Tool call declarations (before execution)

    Each block is logged with a static fallback summary, then an async task
    is spawned to generate an AI-powered summary using Claude Haiku.

    Args:
        adw_id: The ADW ID for logging
        adw_step: Current step slug
        agent_id: The agent ID for logging

    Returns:
        MessageHandlers for response logging
    """

    async def on_assistant_block(block: TextBlock | ThinkingBlock | ToolUseBlock) -> None:
        """Log individual assistant message blocks with async AI summarization."""
        if isinstance(block, TextBlock):
            # Text response from agent - keep full content
            text = block.text
            preview = text[:150] + "..." if len(text) > 150 else text
            log_id = await log_adw_event(
                adw_id=adw_id,
                adw_step=adw_step,
                event_category="response",
                event_type="TextBlock",
                content=text,
                agent_id=agent_id,
                payload={"text": text},
                summary=f"Response: {preview}",  # Fallback summary
            )
            # Spawn async AI summarization
            asyncio.create_task(_summarize_and_update(
                log_id, adw_id, {"content": text}, "TextBlock"
            ))

        elif isinstance(block, ThinkingBlock):
            # Agent thinking/reasoning - keep full content
            thinking = block.thinking
            preview = thinking[:100] + "..." if len(thinking) > 100 else thinking
            log_id = await log_adw_event(
                adw_id=adw_id,
                adw_step=adw_step,
                event_category="response",
                event_type="ThinkingBlock",
                content=thinking,
                agent_id=agent_id,
                payload={"thinking": thinking},
                summary=f"Thinking: {preview}",  # Fallback summary
            )
            # Spawn async AI summarization
            asyncio.create_task(_summarize_and_update(
                log_id, adw_id, {"thinking": thinking}, "ThinkingBlock"
            ))

        elif isinstance(block, ToolUseBlock):
            # Tool call declaration (the agent declaring it wants to use a tool)
            tool_name = block.name
            tool_input = block.input
            log_id = await log_adw_event(
                adw_id=adw_id,
                adw_step=adw_step,
                event_category="response",
                event_type="ToolUseBlock",
                content=f"[Tool] {tool_name}",
                agent_id=agent_id,
                payload={
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_use_id": block.id,
                },
                summary=f"Using tool: {tool_name}",  # Fallback summary
            )
            # Spawn async AI summarization
            asyncio.create_task(_summarize_and_update(
                log_id, adw_id, {"tool_name": tool_name, "tool_input": tool_input}, "ToolUseBlock"
            ))

    async def on_result(msg: ResultMessage) -> None:
        """Log final result with usage stats."""
        await log_adw_event(
            adw_id=adw_id,
            adw_step=adw_step,
            event_category="response",
            event_type="result",
            content=msg.result if msg.result else "",  # Full content
            agent_id=agent_id,
            payload={
                "subtype": msg.subtype.value if msg.subtype else None,
                "usage": msg.usage.model_dump() if msg.usage else None,
                "session_id": msg.session_id,
            },
            summary=f"Step completed: {msg.subtype.value if msg.subtype else 'unknown'}",
        )

    return MessageHandlers(
        on_assistant_block=on_assistant_block,
        on_result=on_result,
    )


# =============================================================================
# WORKFLOW STEPS
# =============================================================================


async def run_plan_step(
    adw_id: str,
    orchestrator_agent_id: str,
    prompt: str,
    working_dir: str,
    model: str = ModelName.OPUS.value,
) -> tuple[bool, str | None, str | None]:
    """Run the /plan step.

    Args:
        adw_id: ADW ID for logging
        orchestrator_agent_id: Parent orchestrator agent ID
        prompt: The task prompt to plan
        working_dir: Working directory for the agent
        model: Model to use

    Returns:
        Tuple of (success, session_id, agent_id)
    """
    step_start_time = time.time()

    # Create agent record upfront (name includes ADW ID for uniqueness)
    agent_id = await create_agent(
        orchestrator_agent_id=orchestrator_agent_id,
        name=f"plan-{adw_id[:8]}",
        model=model,
        working_dir=working_dir,
        adw_id=adw_id,
        adw_step=STEP_PLAN,
    )
    console.print(f"[dim]Created plan agent: {agent_id}[/dim]")

    # System log: Agent created
    await log_system_event(
        adw_id=adw_id,
        adw_step=STEP_PLAN,
        level="INFO",
        message=f"Created plan agent: {agent_id[:8]}",
        metadata={"agent_id": agent_id, "model": model},
    )

    # Update agent status to executing (broadcast status change)
    await update_agent(agent_id=agent_id, status="executing", old_status="idle")

    # Log step start
    await log_step_start(
        adw_id=adw_id,
        adw_step=STEP_PLAN,
        agent_id=agent_id,
        payload={"prompt": prompt, "model": model},
        summary=f"Starting plan step for: {prompt[:100]}...",
    )

    # Update ADW status
    await update_adw_status(
        adw_id=adw_id,
        status="in_progress",
        current_step=STEP_PLAN,
    )

    console.print(Panel(
        f"[bold cyan]Step 1: Plan[/bold cyan]\n\nPrompt: {prompt[:200]}...",
        title="ADW Plan-Build Workflow",
        width=console.width,
    ))

    try:
        # System log: Starting agent execution
        await log_system_event(
            adw_id=adw_id,
            adw_step=STEP_PLAN,
            level="INFO",
            message=f"Executing /plan command with model {model}",
            metadata={"prompt_preview": prompt[:100], "working_dir": working_dir},
        )

        # Build the agent query
        # Use Skill tool to invoke /plan
        query_input = QueryInput(
            prompt=f"/plan {prompt}",
            options=QueryOptions(
                model=model,
                cwd=working_dir,
                allowed_tools=[
                    "Read", "Glob", "Grep", "Bash", "Write", "Edit",
                    "Task", "TodoWrite", "WebFetch", "WebSearch", "Skill",
                ],
                hooks=create_logging_hooks(adw_id, STEP_PLAN, agent_id),
                bypass_permissions=True,
            ),
            handlers=create_message_handlers(adw_id, STEP_PLAN, agent_id),
        )

        # Execute the agent
        result = await query_to_completion(query_input)

        duration_ms = int((time.time() - step_start_time) * 1000)

        # Update agent with session_id and usage
        await update_agent(
            agent_id=agent_id,
            session_id=result.session_id,
            status="complete" if result.success else "blocked",
            input_tokens=result.usage.input_tokens if result.usage else None,
            output_tokens=result.usage.output_tokens if result.usage else None,
            total_cost=result.usage.total_cost_usd if result.usage else None,
        )

        if result.success:
            console.print(f"[green]Plan step completed successfully[/green]")
            await log_step_end(
                adw_id=adw_id,
                adw_step=STEP_PLAN,
                agent_id=agent_id,
                status="success",
                duration_ms=duration_ms,
                payload={"session_id": result.session_id},
                summary="Plan step completed successfully",
            )
            return True, result.session_id, agent_id
        else:
            console.print(f"[red]Plan step failed: {result.error}[/red]")
            await log_step_end(
                adw_id=adw_id,
                adw_step=STEP_PLAN,
                agent_id=agent_id,
                status="failed",
                duration_ms=duration_ms,
                payload={"error": result.error},
                summary=f"Plan step failed: {result.error}",
            )
            return False, None, agent_id

    except Exception as e:
        duration_ms = int((time.time() - step_start_time) * 1000)
        console.print(f"[red]Plan step exception: {e}[/red]")
        await update_agent(agent_id=agent_id, status="blocked", old_status="executing")
        await log_step_end(
            adw_id=adw_id,
            adw_step=STEP_PLAN,
            agent_id=agent_id,
            status="failed",
            duration_ms=duration_ms,
            payload={"exception": str(e)},
            summary=f"Plan step exception: {e}",
        )
        return False, None, agent_id


async def extract_plan_path(
    working_dir: str,
    session_id: str | None,
    model: str = ModelName.OPUS.value,
) -> str | None:
    """Use quick_prompt to extract the plan file path.

    Args:
        working_dir: Working directory
        session_id: Session ID from plan step (for context)
        model: Model to use

    Returns:
        Path to the plan file, or None if not found
    """
    console.print("[cyan]Extracting plan file path...[/cyan]")

    # Very explicit prompt to get ONLY the file path
    extraction_prompt = """You just ran /plan and created a plan file.

IMPORTANT: Respond with ONLY the absolute file path to the plan file you created.
- No explanation
- No markdown
- No quotes
- Just the raw file path on a single line

Example correct response:
/Users/user/project/specs/feature-plan.md

What is the absolute path to the plan file you created?"""

    try:
        result = await quick_prompt(AdhocPrompt(
            prompt=extraction_prompt,
            model=model,
            cwd=working_dir,
        ))

        if result:
            # Clean up the result - remove any whitespace, quotes, backticks
            path = result.strip().strip("`").strip('"').strip("'").strip()
            # Take only the first line in case there's extra text
            path = path.split("\n")[0].strip()

            # Validate it looks like a path
            if path.startswith("/") or path.startswith("./"):
                console.print(f"[green]Found plan file: {path}[/green]")
                return path
            else:
                console.print(f"[yellow]Unexpected path format: {path}[/yellow]")
                # Try to extract a path from the response
                import re
                match = re.search(r'(/[^\s]+\.md)', result)
                if match:
                    path = match.group(1)
                    console.print(f"[green]Extracted path: {path}[/green]")
                    return path

        console.print("[yellow]Could not extract plan file path[/yellow]")
        return None

    except Exception as e:
        console.print(f"[red]Error extracting plan path: {e}[/red]")
        return None


async def run_build_step(
    adw_id: str,
    orchestrator_agent_id: str,
    plan_path: str,
    working_dir: str,
    model: str = ModelName.OPUS.value,
) -> tuple[bool, str | None, str | None]:
    """Run the /build step.

    Args:
        adw_id: ADW ID for logging
        orchestrator_agent_id: Parent orchestrator agent ID
        plan_path: Path to the plan file
        working_dir: Working directory for the agent
        model: Model to use

    Returns:
        Tuple of (success, session_id, agent_id)
    """
    step_start_time = time.time()

    # Create agent record upfront (name includes ADW ID for uniqueness)
    agent_id = await create_agent(
        orchestrator_agent_id=orchestrator_agent_id,
        name=f"build-{adw_id[:8]}",
        model=model,
        working_dir=working_dir,
        adw_id=adw_id,
        adw_step=STEP_BUILD,
    )
    console.print(f"[dim]Created build agent: {agent_id}[/dim]")

    # System log: Agent created
    await log_system_event(
        adw_id=adw_id,
        adw_step=STEP_BUILD,
        level="INFO",
        message=f"Created build agent: {agent_id[:8]}",
        metadata={"agent_id": agent_id, "model": model},
    )

    # Update agent status to executing (broadcast status change)
    await update_agent(agent_id=agent_id, status="executing", old_status="idle")

    # Log step start
    await log_step_start(
        adw_id=adw_id,
        adw_step=STEP_BUILD,
        agent_id=agent_id,
        payload={"plan_path": plan_path, "model": model},
        summary=f"Starting build step with plan: {plan_path}",
    )

    # Update ADW status
    await update_adw_status(
        adw_id=adw_id,
        status="in_progress",
        current_step=STEP_BUILD,
        completed_steps=1,
    )

    console.print(Panel(
        f"[bold cyan]Step 2: Build[/bold cyan]\n\nPlan: {plan_path}",
        title="ADW Plan-Build Workflow",
        width=console.width,
    ))

    try:
        # System log: Starting agent execution
        await log_system_event(
            adw_id=adw_id,
            adw_step=STEP_BUILD,
            level="INFO",
            message=f"Executing /build command with plan: {plan_path}",
            metadata={"plan_path": plan_path, "working_dir": working_dir},
        )

        # Build the agent query
        query_input = QueryInput(
            prompt=f"/build {plan_path}",
            options=QueryOptions(
                model=model,
                cwd=working_dir,
                allowed_tools=[
                    "Read", "Glob", "Grep", "Bash", "Write", "Edit",
                    "Task", "TodoWrite", "WebFetch", "WebSearch", "Skill",
                ],
                hooks=create_logging_hooks(adw_id, STEP_BUILD, agent_id),
                bypass_permissions=True,
            ),
            handlers=create_message_handlers(adw_id, STEP_BUILD, agent_id),
        )

        # Execute the agent
        result = await query_to_completion(query_input)

        duration_ms = int((time.time() - step_start_time) * 1000)

        # Update agent with session_id and usage
        await update_agent(
            agent_id=agent_id,
            session_id=result.session_id,
            status="complete" if result.success else "blocked",
            input_tokens=result.usage.input_tokens if result.usage else None,
            output_tokens=result.usage.output_tokens if result.usage else None,
            total_cost=result.usage.total_cost_usd if result.usage else None,
        )

        if result.success:
            console.print(f"[green]Build step completed successfully[/green]")
            await log_step_end(
                adw_id=adw_id,
                adw_step=STEP_BUILD,
                agent_id=agent_id,
                status="success",
                duration_ms=duration_ms,
                payload={"session_id": result.session_id},
                summary="Build step completed successfully",
            )
            return True, result.session_id, agent_id
        else:
            console.print(f"[red]Build step failed: {result.error}[/red]")
            await log_step_end(
                adw_id=adw_id,
                adw_step=STEP_BUILD,
                agent_id=agent_id,
                status="failed",
                duration_ms=duration_ms,
                payload={"error": result.error},
                summary=f"Build step failed: {result.error}",
            )
            return False, None, agent_id

    except Exception as e:
        duration_ms = int((time.time() - step_start_time) * 1000)
        console.print(f"[red]Build step exception: {e}[/red]")
        await update_agent(agent_id=agent_id, status="blocked", old_status="executing")
        await log_step_end(
            adw_id=adw_id,
            adw_step=STEP_BUILD,
            agent_id=agent_id,
            status="failed",
            duration_ms=duration_ms,
            payload={"exception": str(e)},
            summary=f"Build step exception: {e}",
        )
        return False, None, agent_id


# =============================================================================
# MAIN WORKFLOW
# =============================================================================


async def run_workflow(adw_id: str) -> bool:
    """Run the complete plan-build workflow.

    Args:
        adw_id: The ADW ID to execute

    Returns:
        True if successful, False otherwise
    """
    workflow_start_time = time.time()

    # Initialize logging with WebSocket connection for real-time updates
    # This is resilient - workflow continues even if WS server is unavailable
    await init_logging(verbose=False)

    console.print(Panel(
        f"[bold]Starting ADW Plan-Build Workflow[/bold]\n\nADW ID: {adw_id}",
        title="ADW Workflow",
        width=console.width,
    ))

    # Fetch ADW record from database
    adw = await get_adw(adw_id)
    if not adw:
        console.print(f"[red]ADW not found: {adw_id}[/red]")
        return False

    # Extract orchestrator_agent_id (required for creating child agents)
    orchestrator_agent_id = adw.get("orchestrator_agent_id")
    if not orchestrator_agent_id:
        console.print("[red]No orchestrator_agent_id found in ADW record[/red]")
        await update_adw_status(
            adw_id=adw_id,
            status="failed",
            error_message="No orchestrator_agent_id found",
        )
        return False
    orchestrator_agent_id = str(orchestrator_agent_id)

    # Extract input data
    input_data = adw.get("input_data", {})
    prompt = input_data.get("prompt")
    working_dir = input_data.get("working_dir")
    model = input_data.get("model", ModelName.OPUS.value)

    if not prompt:
        console.print("[red]No prompt found in ADW input_data[/red]")
        await update_adw_status(
            adw_id=adw_id,
            status="failed",
            error_message="No prompt found in input_data",
        )
        return False

    if not working_dir:
        console.print("[red]No working_dir found in ADW input_data[/red]")
        await update_adw_status(
            adw_id=adw_id,
            status="failed",
            error_message="No working_dir found in input_data",
        )
        return False

    console.print(f"[cyan]Prompt:[/cyan] {prompt[:200]}...")
    console.print(f"[cyan]Working Dir:[/cyan] {working_dir}")
    console.print(f"[cyan]Model:[/cyan] {model}")

    # Log workflow start
    await log_system_event(
        adw_id=adw_id,
        adw_step=None,
        level="INFO",
        message=f"Workflow started: {adw.get('adw_name', 'unknown')}",
        metadata={"prompt": prompt, "working_dir": working_dir, "model": model},
    )

    try:
        # Step 1: Plan
        plan_success, plan_session_id, plan_agent_id = await run_plan_step(
            adw_id=adw_id,
            orchestrator_agent_id=orchestrator_agent_id,
            prompt=prompt,
            working_dir=working_dir,
            model=model,
        )

        if not plan_success:
            await update_adw_status(
                adw_id=adw_id,
                status="failed",
                error_message="Plan step failed",
                error_step=STEP_PLAN,
            )
            return False

        # Extract plan file path
        plan_path = await extract_plan_path(
            working_dir=working_dir,
            session_id=plan_session_id,
            model=model,
        )

        if not plan_path:
            # Try a fallback - look for recently created .md files in specs/
            console.print("[yellow]Attempting fallback plan path detection...[/yellow]")
            specs_dir = Path(working_dir) / "specs"
            if specs_dir.exists():
                md_files = sorted(specs_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
                if md_files:
                    plan_path = str(md_files[0])
                    console.print(f"[green]Found recent plan file: {plan_path}[/green]")

        if not plan_path:
            await update_adw_status(
                adw_id=adw_id,
                status="failed",
                error_message="Could not extract plan file path",
                error_step=STEP_PLAN,
            )
            return False

        # Step 2: Build
        build_success, build_session_id, build_agent_id = await run_build_step(
            adw_id=adw_id,
            orchestrator_agent_id=orchestrator_agent_id,
            plan_path=plan_path,
            working_dir=working_dir,
            model=model,
        )

        if not build_success:
            await update_adw_status(
                adw_id=adw_id,
                status="failed",
                error_message="Build step failed",
                error_step=STEP_BUILD,
                completed_steps=1,
            )
            return False

        # Workflow completed successfully
        duration_seconds = int(time.time() - workflow_start_time)
        await update_adw_status(
            adw_id=adw_id,
            status="completed",
            completed_steps=TOTAL_STEPS,
        )

        await log_system_event(
            adw_id=adw_id,
            adw_step=None,
            level="INFO",
            message=f"Workflow completed successfully in {duration_seconds}s",
            metadata={
                "plan_path": plan_path,
                "plan_session_id": plan_session_id,
                "plan_agent_id": plan_agent_id,
                "build_session_id": build_session_id,
                "build_agent_id": build_agent_id,
                "duration_seconds": duration_seconds,
            },
        )

        console.print(Panel(
            f"[bold green]Workflow Completed Successfully![/bold green]\n\n"
            f"Duration: {duration_seconds}s\n"
            f"Plan file: {plan_path}",
            title="ADW Complete",
            width=console.width,
        ))

        return True

    except Exception as e:
        console.print(f"[red]Workflow exception: {e}[/red]")
        await update_adw_status(
            adw_id=adw_id,
            status="failed",
            error_message=str(e),
        )
        await log_system_event(
            adw_id=adw_id,
            adw_step=None,
            level="ERROR",
            message=f"Workflow exception: {e}",
        )
        return False

    finally:
        # Always close logging (database pool + WebSocket connection)
        await close_logging()


# =============================================================================
# CLI ENTRYPOINT
# =============================================================================


def main():
    """CLI entrypoint for the plan-build workflow."""
    parser = argparse.ArgumentParser(
        description="ADW Plan-Build Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--adw-id",
        required=True,
        help="ADW ID (UUID) to execute",
    )

    args = parser.parse_args()

    # Run the workflow
    success = asyncio.run(run_workflow(args.adw_id))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
