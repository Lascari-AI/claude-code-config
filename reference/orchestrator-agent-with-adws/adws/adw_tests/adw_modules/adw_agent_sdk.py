# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pydantic>=2.0",
#   "claude-agent-sdk>=0.1.18",
#   "rich>=13.0",
# ]
# ///
"""
ADW Agent SDK - Test Runner

Tests for the adw_agent_sdk module. Run with:

    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py <test-type>

Available test types:
    types-only        Validate Pydantic types without SDK calls
    just-prompt       Simple prompt -> completion (2+2=4)
    slash-command     Test built-in /help slash command
    hooks             Test PreToolUse and PostToolUse hooks
    tools             Test with specific tools (Glob, Read)
    model-select      Test different models (Haiku, Sonnet)
    session           Test session capture and timestamps
    cwd-slash-command Test cwd option with project /ping command
    messages-detail   Test all message types and block capture
    quick-prompt      Test quick_prompt() for one-off adhoc queries

Examples:
    # Run types-only test (default, no SDK calls)
    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py types-only

    # Test basic prompt/completion
    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py just-prompt

    # Test hooks (PreToolUse, PostToolUse)
    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py hooks

    # Test quick_prompt for simple one-off queries
    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py quick-prompt

    # List all available tests
    uv run adws/adw_tests/adw_modules/adw_agent_sdk.py --list
"""

from __future__ import annotations

import asyncio
import sys
from enum import Enum
from pathlib import Path

# Add parent directories to path for imports
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

# Import from main SDK module
from adws.adw_modules.adw_agent_sdk import (
    # Adhoc prompts
    AdhocPrompt,
    AssistantMessage,
    CompactBoundaryMessage,
    HookContext,
    # Hooks
    HookEventName,
    HookInput,
    HookResponse,
    ModelName,
    PostToolUseInput,
    PreToolUseInput,
    # Core types
    QueryInput,
    QueryOptions,
    ResultMessage,
    SettingSource,
    # Messages
    SystemInitMessage,
    SystemPromptConfig,
    SystemPromptMode,
    # Token tracking
    TokenUsage,
    UsageAccumulator,
    UserMessage,
    query_to_completion,
    quick_prompt,
)

# =============================================================================
# TEST TYPES
# =============================================================================


class TestType(str, Enum):
    """Available test types for the SDK."""

    TYPES_ONLY = "types-only"  # Just validate types, no SDK calls
    JUST_PROMPT = "just-prompt"  # Simple prompt → completion
    SLASH_COMMAND = "slash-command"  # Test slash command (e.g., /help)
    HOOKS = "hooks"  # Test hooks (PreToolUse, PostToolUse)
    TOOLS = "tools"  # Test with specific tools (Read, Glob)
    MODEL_SELECT = "model-select"  # Test different models (Haiku for speed)
    SESSION = "session"  # Test session capture
    CWD_SLASH_COMMAND = "cwd-slash-command"  # Test cwd + project slash command (/ping)
    MESSAGES_DETAIL = "messages-detail"  # Test all message types and blocks
    QUICK_PROMPT = "quick-prompt"  # Test quick_prompt() for adhoc queries
    QUICK_PROMPT_CWD_REUSABLE = "quick-prompt-cwd-reusable"  # Test quick_prompt with cwd + /ping
    QUICK_PROMPT_SYSTEM_MODES = "quick-prompt-system-modes"  # Test all 3 system prompt modes


# =============================================================================
# TEST IMPLEMENTATIONS
# =============================================================================


async def test_types_only() -> None:
    """Validate types without making SDK calls.

    Tests: QueryOptions, QueryInput, TokenUsage, UsageAccumulator, HookResponse
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty

    console = Console(width=120)
    console.print(Panel("[bold cyan]ADW Agent SDK - Types Validation[/bold cyan]", width=console.width))

    # Query options
    options = QueryOptions(
        model=ModelName.OPUS,
        allowed_tools=["Read", "Write", "Bash", "Skill"],
        setting_sources=[SettingSource.USER, SettingSource.PROJECT],
        max_turns=10,
    )
    console.print(Panel(Pretty(options), title="QueryOptions", width=console.width))

    # Query input
    query = QueryInput(prompt="Analyze the codebase", options=options)
    console.print(Panel(Pretty(query), title="QueryInput", width=console.width))

    # Token usage
    usage = TokenUsage(input_tokens=5000, output_tokens=1500, cache_read_input_tokens=2000)
    console.print(Panel(
        f"{Pretty(usage)}\n\nEstimated Cost: ${usage.calculate_cost():.6f}",
        title="TokenUsage",
        width=console.width,
    ))

    # Usage accumulator deduplication
    acc = UsageAccumulator()
    acc.process("msg_001", usage)
    acc.process("msg_001", usage)  # Duplicate - ignored
    acc.process("msg_002", TokenUsage(input_tokens=1000, output_tokens=500))
    console.print(Panel(
        f"Processed IDs: {acc.processed_ids}\nTotal input: {acc.total_input_tokens}",
        title="UsageAccumulator (deduplicates)",
        width=console.width,
    ))

    # Hook response examples
    console.print(Panel(
        f"Allow: {HookResponse.allow()}\n\n"
        f"Deny: {HookResponse.deny('Cannot modify .env')}\n\n"
        f"Stop: {HookResponse.stop('User cancelled')}",
        title="HookResponse Factory Methods",
        width=console.width,
    ))

    console.print(Panel("[bold green]All types validated![/bold green]", width=console.width))


async def test_just_prompt() -> None:
    """Test simple prompt → completion.

    Tests: Basic SDK query flow, message parsing, result extraction
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: just-prompt[/bold cyan]", width=console.width))

    query_input = QueryInput(
        prompt="What is 2 + 2? Respond with just the number.",
        options=QueryOptions(
            model=ModelName.HAIKU,  # Fast model for testing
            max_turns=1,
        ),
    )

    console.print(Panel(Pretty(query_input), title="QueryInput", width=console.width))
    console.print("[yellow]Executing query...[/yellow]")

    result = await query_to_completion(query_input)

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Result:[/bold] {result.result}\n"
        f"[bold]Error:[/bold] {result.error}\n"
        f"[bold]Session ID:[/bold] {result.session_id}\n"
        f"[bold]Duration:[/bold] {result.duration_seconds:.2f}s\n"
        f"[bold]Messages:[/bold] {len(result.messages)}",
        title="QueryOutput",
        width=console.width,
    ))

    if result.usage:
        console.print(Panel(Pretty(result.usage), title="Final Usage", width=console.width))


async def test_slash_command() -> None:
    """Test slash command execution.

    Tests: SDK slash command handling, SystemInitMessage parsing
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: slash-command[/bold cyan]", width=console.width))

    # Use /help which is a built-in slash command
    query_input = QueryInput(
        prompt="/help",
        options=QueryOptions(
            model=ModelName.HAIKU,
            max_turns=1,
        ),
    )

    console.print(Panel(Pretty(query_input), title="QueryInput (/help)", width=console.width))
    console.print("[yellow]Executing slash command...[/yellow]")

    result = await query_to_completion(query_input)

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Result (first 500 chars):[/bold]\n{(result.result or '')[:500]}...",
        title="QueryOutput",
        width=console.width,
    ))

    # Show available slash commands from init message
    for msg in result.messages:
        if isinstance(msg, SystemInitMessage):
            console.print(Panel(
                f"[bold]Slash Commands:[/bold] {msg.slash_commands[:10]}...",
                title="System Init",
                width=console.width,
            ))
            break


async def test_hooks() -> None:
    """Test hooks (PreToolUse, PostToolUse).

    Tests: Hook registration with SDKHookMatcher, callback invocation, typed conversion
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: hooks[/bold cyan]", width=console.width))

    # Track hook invocations
    hook_log: list[str] = []

    async def pre_tool_hook(
        input_data: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookResponse:
        """Log PreToolUse events."""
        if isinstance(input_data, PreToolUseInput):
            hook_log.append(f"[PreToolUse] {input_data.tool_name}: {list(input_data.tool_input.keys())}")
            console.print(f"[magenta]HOOK: PreToolUse - {input_data.tool_name}[/magenta]")
        return HookResponse.allow()

    async def post_tool_hook(
        input_data: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookResponse:
        """Log PostToolUse events."""
        if isinstance(input_data, PostToolUseInput):
            hook_log.append(f"[PostToolUse] {input_data.tool_name}")
            console.print(f"[green]HOOK: PostToolUse - {input_data.tool_name}[/green]")
        return HookResponse.allow()

    query_input = QueryInput(
        prompt="List files in the current directory using the Glob tool with pattern '*'",
        options=QueryOptions(
            model=ModelName.HAIKU,
            allowed_tools=["Glob"],
            max_turns=3,
            hooks={
                HookEventName.PRE_TOOL_USE: [pre_tool_hook],
                HookEventName.POST_TOOL_USE: [post_tool_hook],
            },
        ),
    )

    console.print(Panel(Pretty(query_input.options.hooks), title="Hooks Config", width=console.width))
    console.print("[yellow]Executing with hooks...[/yellow]")

    result = await query_to_completion(query_input)

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Hook Invocations:[/bold] {len(hook_log)}\n"
        + "\n".join(hook_log),
        title="Hook Log",
        width=console.width,
    ))

    console.print(Panel(
        f"[bold]Result:[/bold] {(result.result or '')[:300]}...",
        title="QueryOutput",
        width=console.width,
    ))


async def test_tools() -> None:
    """Test with specific tools (Read, Glob, Grep).

    Tests: allowed_tools option, tool use detection in AssistantMessage
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: tools[/bold cyan]", width=console.width))

    query_input = QueryInput(
        prompt="Use Glob to find *.py files in the current directory, then tell me how many you found.",
        options=QueryOptions(
            model=ModelName.HAIKU,
            allowed_tools=["Glob", "Read"],
            max_turns=5,
        ),
    )

    console.print(Panel(
        f"[bold]Allowed Tools:[/bold] {query_input.options.allowed_tools}",
        title="QueryInput",
        width=console.width,
    ))
    console.print("[yellow]Executing with tools...[/yellow]")

    result = await query_to_completion(query_input)

    # Count tool uses
    tool_uses = [
        msg for msg in result.messages
        if isinstance(msg, AssistantMessage) and msg.tool_use
    ]

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Tool Uses:[/bold] {len(tool_uses)}\n"
        f"[bold]Result:[/bold] {(result.result or '')[:500]}",
        title="QueryOutput",
        width=console.width,
    ))

    if result.usage_accumulator:
        console.print(Panel(
            f"[bold]Unique Messages:[/bold] {len(result.usage_accumulator.processed_ids)}\n"
            f"[bold]Total Input Tokens:[/bold] {result.usage_accumulator.total_input_tokens}\n"
            f"[bold]Total Output Tokens:[/bold] {result.usage_accumulator.total_output_tokens}",
            title="Usage Accumulator",
            width=console.width,
        ))


async def test_model_select() -> None:
    """Test different models.

    Tests: model option with ModelName enum (Haiku vs Sonnet)
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: model-select[/bold cyan]", width=console.width))

    prompt = "What is the capital of France? Answer in one word."

    for model in [ModelName.HAIKU, ModelName.SONNET]:
        console.print(f"\n[yellow]Testing model: {model.value}[/yellow]")

        query_input = QueryInput(
            prompt=prompt,
            options=QueryOptions(
                model=model,
                max_turns=1,
            ),
        )

        result = await query_to_completion(query_input)

        console.print(Panel(
            f"[bold]Model:[/bold] {model.value}\n"
            f"[bold]Success:[/bold] {result.success}\n"
            f"[bold]Result:[/bold] {result.result}\n"
            f"[bold]Duration:[/bold] {result.duration_seconds:.2f}s",
            title=f"Model: {model.name}",
            width=console.width,
        ))


async def test_session() -> None:
    """Test session capture and display.

    Tests: Session ID extraction from SystemInitMessage and ResultMessage, timestamps
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.pretty import Pretty

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: session[/bold cyan]", width=console.width))

    query_input = QueryInput(
        prompt="Say 'Hello, session test!' and nothing else.",
        options=QueryOptions(
            model=ModelName.HAIKU,
            max_turns=1,
        ),
    )

    console.print("[yellow]Executing to capture session...[/yellow]")

    result = await query_to_completion(query_input)

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Session ID:[/bold] {result.session_id}\n"
        f"[bold]Result:[/bold] {result.result}\n"
        f"[bold]Duration:[/bold] {result.duration_seconds:.2f}s\n"
        f"[bold]Started:[/bold] {result.started_at}\n"
        f"[bold]Completed:[/bold] {result.completed_at}",
        title="Session Info",
        width=console.width,
    ))

    # Show all message types received
    msg_types = [type(msg).__name__ for msg in result.messages]
    console.print(Panel(
        f"[bold]Message Types:[/bold] {msg_types}",
        title="Messages Received",
        width=console.width,
    ))

    # Show init message details
    for msg in result.messages:
        if isinstance(msg, SystemInitMessage):
            console.print(Panel(
                Pretty(msg),
                title="SystemInitMessage",
                width=console.width,
            ))
            break


async def test_cwd_slash_command() -> None:
    """Test cwd option with project slash command (/ping).

    Tests: cwd option, project-specific slash commands from .claude/commands/

    This test:
    1. Sets cwd to the project root (parent.parent.parent.parent of this script)
    2. Runs the /ping slash command from .claude/commands/ping.md
    3. Expects "pong" in the response
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: cwd-slash-command[/bold cyan]", width=console.width))

    # Get project root: adws/adw_tests/adw_modules/adw_agent_sdk.py -> parent.parent.parent.parent
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent
    console.print(f"[dim]Script path: {script_path}[/dim]")
    console.print(f"[dim]Project root (cwd): {project_root}[/dim]")

    # Verify ping.md exists
    ping_path = project_root / ".claude" / "commands" / "ping.md"
    if not ping_path.exists():
        console.print(f"[red]Error: {ping_path} does not exist![/red]")
        return

    console.print(f"[green]✓ Found: {ping_path}[/green]")

    query_input = QueryInput(
        prompt="/ping",
        options=QueryOptions(
            model=ModelName.HAIKU,
            cwd=str(project_root),  # Set working directory to project root
            max_turns=1,
        ),
    )

    console.print(Panel(
        f"[bold]Prompt:[/bold] {query_input.prompt}\n"
        f"[bold]CWD:[/bold] {query_input.options.cwd}\n"
        f"[bold]Model:[/bold] {query_input.options.model}",
        title="QueryInput",
        width=console.width,
    ))
    console.print("[yellow]Executing /ping...[/yellow]")

    result = await query_to_completion(query_input)

    # Check for "pong" in result
    has_pong = "pong" in (result.result or "").lower()

    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Result:[/bold] {result.result}\n"
        f"[bold]Contains 'pong':[/bold] {'✓ YES' if has_pong else '✗ NO'}\n"
        f"[bold]Duration:[/bold] {result.duration_seconds:.2f}s\n"
        f"[bold]Session ID:[/bold] {result.session_id}",
        title="QueryOutput",
        width=console.width,
    ))

    if not has_pong:
        console.print("[red]Warning: Expected 'pong' in response![/red]")


async def test_messages_detail() -> None:
    """Test all message types and block-level detail.

    Tests: Message type capture, block parsing (TextBlock, ToolUseBlock, ThinkingBlock)

    This test runs a query that uses tools to trigger multiple message types:
    - SystemInitMessage (session init)
    - AssistantMessage (with text and tool_use blocks)
    - UserMessage (with tool_result)
    - ResultMessage (final result with usage)
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: messages-detail[/bold cyan]", width=console.width))

    query_input = QueryInput(
        prompt="Use Glob to find *.md files in the current directory. List up to 3 files.",
        options=QueryOptions(
            model=ModelName.HAIKU,
            allowed_tools=["Glob"],
            max_turns=3,
        ),
    )

    console.print(Panel(
        f"[bold]Prompt:[/bold] {query_input.prompt}\n"
        f"[bold]Tools:[/bold] {query_input.options.allowed_tools}",
        title="QueryInput",
        width=console.width,
    ))
    console.print("[yellow]Executing to capture all message types...[/yellow]")

    result = await query_to_completion(query_input)

    # Summary
    console.print(Panel(
        f"[bold]Success:[/bold] {result.success}\n"
        f"[bold]Total Messages:[/bold] {len(result.messages)}\n"
        f"[bold]Duration:[/bold] {result.duration_seconds:.2f}s",
        title="Query Result",
        width=console.width,
    ))

    # Create table of all messages
    table = Table(title="Messages Captured", width=console.width)
    table.add_column("#", style="dim", width=3)
    table.add_column("Type", style="cyan", width=20)
    table.add_column("Subtype/ID", style="green", width=25)
    table.add_column("Content Preview", style="white", width=60)

    for i, msg in enumerate(result.messages):
        msg_type = type(msg).__name__
        subtype_or_id = ""
        content_preview = ""

        if isinstance(msg, SystemInitMessage):
            subtype_or_id = f"session: {msg.session_id[:8]}..."
            content_preview = f"tools: {len(msg.tools)}, commands: {len(msg.slash_commands)}"

        elif isinstance(msg, CompactBoundaryMessage):
            subtype_or_id = "compact"
            content_preview = str(msg.compact_metadata)[:50]

        elif isinstance(msg, AssistantMessage):
            subtype_or_id = f"id: {msg.id[:12]}..."
            parts = []
            if msg.message:
                parts.append(f"text: {len(msg.message)} chars")
            if msg.tool_use:
                parts.append(f"tool: {msg.tool_use.get('name', '?')}")
            content_preview = ", ".join(parts) if parts else "(empty)"

        elif isinstance(msg, UserMessage):
            subtype_or_id = "user"
            if msg.tool_result:
                tool_id = msg.tool_result.get("tool_use_id", "?")
                is_err = msg.tool_result.get("is_error", False)
                content_preview = f"tool_result: {tool_id[:12]}... {'(error)' if is_err else '(ok)'}"
            elif msg.message:
                content_preview = f"message: {msg.message[:40]}..."
            else:
                content_preview = "(empty)"

        elif isinstance(msg, ResultMessage):
            subtype_or_id = f"subtype: {msg.subtype.value}"
            if msg.result:
                content_preview = f"result: {msg.result[:40]}..."
            elif msg.error:
                content_preview = f"error: {msg.error[:40]}..."
            else:
                content_preview = "(empty)"

        table.add_row(str(i), msg_type, subtype_or_id, content_preview)

    console.print(table)

    # Count by type
    type_counts: dict[str, int] = {}
    for msg in result.messages:
        name = type(msg).__name__
        type_counts[name] = type_counts.get(name, 0) + 1

    console.print(Panel(
        "\n".join([f"[bold]{k}:[/bold] {v}" for k, v in type_counts.items()]),
        title="Message Type Counts",
        width=console.width,
    ))

    # Show AssistantMessage details (blocks) - using new content_blocks field
    assistant_msgs = [m for m in result.messages if isinstance(m, AssistantMessage)]
    if assistant_msgs:
        console.print(Panel("[bold]AssistantMessage Block Details (via content_blocks)[/bold]", width=console.width))
        for i, am in enumerate(assistant_msgs):
            block_info = []
            block_info.append(f"[bold]content_blocks count:[/bold] {len(am.content_blocks)}")

            for j, block in enumerate(am.content_blocks):
                block_type = type(block).__name__
                if block_type == "TextBlock":
                    text = getattr(block, "text", "")
                    block_info.append(f"  [{j}] [cyan]TextBlock:[/cyan] {len(text)} chars")
                    block_info.append(f"      Preview: {text[:60]}...")
                elif block_type == "ThinkingBlock":
                    thinking = getattr(block, "thinking", "")
                    block_info.append(f"  [{j}] [magenta]ThinkingBlock:[/magenta] {len(thinking)} chars")
                elif block_type == "ToolUseBlock":
                    name = getattr(block, "name", "?")
                    block_id = getattr(block, "id", "?")
                    block_info.append(f"  [{j}] [yellow]ToolUseBlock:[/yellow] {name}")
                    block_info.append(f"      ID: {block_id}")
                else:
                    block_info.append(f"  [{j}] [dim]{block_type}[/dim]")

            # Also show convenience fields
            if am.message:
                block_info.append(f"[dim]Convenience: message = {len(am.message)} chars[/dim]")
            if am.tool_use:
                block_info.append(f"[dim]Convenience: tool_use = {am.tool_use.get('name', '?')}[/dim]")

            console.print(Panel(
                "\n".join(block_info) if block_info else "(no blocks)",
                title=f"AssistantMessage #{i} (id: {am.id[:12]}...)",
                width=console.width,
            ))

    # Show UserMessage details (blocks)
    user_msgs = [m for m in result.messages if isinstance(m, UserMessage)]
    if user_msgs:
        console.print(Panel("[bold]UserMessage Block Details (via content_blocks)[/bold]", width=console.width))
        for i, um in enumerate(user_msgs):
            block_info = []
            block_info.append(f"[bold]content_blocks count:[/bold] {len(um.content_blocks)}")

            for j, block in enumerate(um.content_blocks):
                block_type = type(block).__name__
                if block_type == "TextBlock":
                    text = getattr(block, "text", "")
                    block_info.append(f"  [{j}] [cyan]TextBlock:[/cyan] {len(text)} chars")
                elif block_type == "ToolResultBlock":
                    tool_use_id = getattr(block, "tool_use_id", "?")
                    is_error = getattr(block, "is_error", False)
                    block_info.append(f"  [{j}] [green]ToolResultBlock:[/green] {tool_use_id[:16]}...")
                    block_info.append(f"      is_error: {is_error}")
                else:
                    block_info.append(f"  [{j}] [dim]{block_type}[/dim]")

            console.print(Panel(
                "\n".join(block_info) if block_info else "(no blocks)",
                title=f"UserMessage #{i}",
                width=console.width,
            ))

    # Notes about content_blocks feature
    console.print(Panel(
        "[green]✓ SDK Types Now Used:[/green]\n"
        "• content_blocks contains actual SDK dataclass instances (TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock)\n"
        "• Use get_sdk_types() to get type classes for isinstance checks\n"
        "• Convenience fields (message, tool_use) still populated for backward compatibility\n"
        "• All block types captured: TextBlock, ThinkingBlock, ToolUseBlock (in AssistantMessage)\n"
        "• ToolResultBlock captured in UserMessage.content_blocks",
        title="Notes",
        width=console.width,
    ))


async def test_quick_prompt() -> None:
    """Test quick_prompt() for simple one-off queries.

    Tests: AdhocPrompt, quick_prompt(), SDK query() function, Claude Code system prompt

    This test uses quick_prompt() which:
    - Uses the SDK's query() function (new session each time)
    - Uses project scope (loads CLAUDE.md)
    - Uses Claude Code's default system prompt
    - Returns just the result string
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: quick-prompt[/bold cyan]", width=console.width))

    # Get project root for cwd
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent
    console.print(f"[dim]Project root (cwd): {project_root}[/dim]")

    # Test 1: Simple math query (no cwd)
    console.print("\n[yellow]Test 1: Simple math query[/yellow]")
    prompt1 = AdhocPrompt(
        prompt="What is 7 * 8? Respond with just the number, nothing else.",
        model=ModelName.HAIKU,
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt1.prompt}\n"
        f"[bold]Model:[/bold] {prompt1.model}\n"
        f"[bold]CWD:[/bold] {prompt1.cwd or '(none)'}",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result1 = await quick_prompt(prompt1)

    has_56 = "56" in result1
    console.print(Panel(
        f"[bold]Result:[/bold] {result1}\n"
        f"[bold]Contains '56':[/bold] {'✓ YES' if has_56 else '✗ NO'}",
        title="Result 1",
        width=console.width,
    ))

    # Test 2: Query with cwd and project context
    console.print("\n[yellow]Test 2: Query with cwd (project context)[/yellow]")
    prompt2 = AdhocPrompt(
        prompt="What is the name of this project based on the directory structure? Just say the folder name.",
        model=ModelName.HAIKU,
        cwd=str(project_root),
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt2.prompt}\n"
        f"[bold]Model:[/bold] {prompt2.model}\n"
        f"[bold]CWD:[/bold] {prompt2.cwd}",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result2 = await quick_prompt(prompt2)

    console.print(Panel(
        f"[bold]Result:[/bold] {result2}",
        title="Result 2",
        width=console.width,
    ))

    # Test 3: Custom system prompt
    console.print("\n[yellow]Test 3: Custom system prompt[/yellow]")
    prompt3 = AdhocPrompt(
        prompt="Say hello",
        model=ModelName.HAIKU,
        system_prompt="You are a pirate. Always respond in pirate speak with 'Arrr!'",
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt3.prompt}\n"
        f"[bold]Model:[/bold] {prompt3.model}\n"
        f"[bold]System Prompt:[/bold] {prompt3.system_prompt}",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result3 = await quick_prompt(prompt3)

    has_pirate = "arrr" in result3.lower() or "ahoy" in result3.lower() or "matey" in result3.lower()
    console.print(Panel(
        f"[bold]Result:[/bold] {result3}\n"
        f"[bold]Contains pirate speak:[/bold] {'✓ YES' if has_pirate else '✗ Maybe'}",
        title="Result 3",
        width=console.width,
    ))

    # Summary
    console.print(Panel(
        "[green]✓ quick_prompt() Features:[/green]\n"
        "• Uses SDK query() - new session each time (no persistence)\n"
        "• Uses project scope (setting_sources=['project'])\n"
        "• Uses Claude Code default system prompt when None\n"
        "• Supports custom system_prompt override\n"
        "• Returns just the result string (simple API)",
        title="Summary",
        width=console.width,
    ))


async def test_quick_prompt_cwd_reusable() -> None:
    """Test quick_prompt() with cwd set to project root and /ping slash command.

    Tests: AdhocPrompt with cwd, quick_prompt(), reusable slash command

    This test:
    - Sets cwd to project root (parent.parent.parent.parent from this file)
    - Runs /ping which should respond with "Pong! 🏓"
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: quick-prompt-cwd-reusable[/bold cyan]", width=console.width))

    # Get project root (parent.parent.parent.parent from test file)
    # adws/adw_tests/adw_modules/adw_agent_sdk.py -> project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent
    console.print(f"[dim]Project root (cwd): {project_root}[/dim]")

    # Verify .claude/commands/ping.md exists
    ping_path = project_root / ".claude" / "commands" / "ping.md"
    console.print(f"[dim]Ping command path: {ping_path}[/dim]")
    console.print(f"[dim]Ping command exists: {ping_path.exists()}[/dim]")

    # Run /ping with cwd set to project root
    prompt = AdhocPrompt(
        prompt="/ping",
        model=ModelName.HAIKU,
        cwd=str(project_root),
    )

    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt.prompt}\n"
        f"[bold]Model:[/bold] {prompt.model}\n"
        f"[bold]CWD:[/bold] {prompt.cwd}",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[yellow]Executing quick_prompt()...[/yellow]")

    result = await quick_prompt(prompt)

    # Check for expected response
    has_pong = "pong" in result.lower()
    console.print(Panel(
        f"[bold]Result:[/bold] {result}\n"
        f"[bold]Contains 'pong':[/bold] {'✓ YES' if has_pong else '✗ NO'}",
        title="Result",
        width=console.width,
    ))

    if has_pong:
        console.print("[green]✓ /ping slash command worked with quick_prompt() + cwd![/green]")
    else:
        console.print("[yellow]⚠ Expected 'pong' in response[/yellow]")


async def test_quick_prompt_system_modes() -> None:
    """Test all three system prompt modes: DEFAULT, APPEND, OVERWRITE.

    Tests: SystemPromptMode, SystemPromptConfig, quick_prompt()

    This test verifies:
    1. DEFAULT - Uses Claude Code's default system prompt
    2. APPEND - Appends to Claude Code's default system prompt
    3. OVERWRITE - Completely replaces the system prompt
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)
    console.print(Panel("[bold cyan]Test: quick-prompt-system-modes[/bold cyan]", width=console.width))

    # Test 1: DEFAULT mode (None = use Claude Code's default)
    console.print("\n[yellow]Test 1: DEFAULT mode (None)[/yellow]")
    prompt1 = AdhocPrompt(
        prompt="What is 3 + 5? Just respond with the number.",
        model=ModelName.HAIKU,
        system_prompt=None,  # DEFAULT - uses Claude Code's system prompt
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt1.prompt}\n"
        f"[bold]System Prompt:[/bold] None (DEFAULT mode - Claude Code's system prompt)",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result1 = await quick_prompt(prompt1)
    has_8 = "8" in result1
    console.print(Panel(
        f"[bold]Result:[/bold] {result1}\n"
        f"[bold]Contains '8':[/bold] {'✓ YES' if has_8 else '✗ NO'}",
        title="Result 1 (DEFAULT)",
        width=console.width,
    ))

    # Test 2: APPEND mode (add to Claude Code's default)
    console.print("\n[yellow]Test 2: APPEND mode[/yellow]")
    prompt2 = AdhocPrompt(
        prompt="What is the capital of France?",
        model=ModelName.HAIKU,
        system_prompt=SystemPromptConfig(
            mode=SystemPromptMode.APPEND,
            system_prompt="Always end your response with '🎯 APPENDED!'",
        ),
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt2.prompt}\n"
        f"[bold]System Prompt Mode:[/bold] APPEND\n"
        f"[bold]Append Text:[/bold] Always end your response with '🎯 APPENDED!'",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result2 = await quick_prompt(prompt2)
    has_paris = "paris" in result2.lower()
    has_appended = "APPENDED" in result2 or "🎯" in result2
    console.print(Panel(
        f"[bold]Result:[/bold] {result2}\n"
        f"[bold]Contains 'Paris':[/bold] {'✓ YES' if has_paris else '✗ NO'}\n"
        f"[bold]Contains appended marker:[/bold] {'✓ YES' if has_appended else '✗ NO (may have ignored)'}",
        title="Result 2 (APPEND)",
        width=console.width,
    ))

    # Test 3: OVERWRITE mode (completely replace)
    console.print("\n[yellow]Test 3: OVERWRITE mode[/yellow]")
    prompt3 = AdhocPrompt(
        prompt="Say hello",
        model=ModelName.HAIKU,
        system_prompt=SystemPromptConfig(
            mode=SystemPromptMode.OVERWRITE,
            system_prompt="You are a robot. You must start every response with 'BEEP BOOP'.",
        ),
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt3.prompt}\n"
        f"[bold]System Prompt Mode:[/bold] OVERWRITE\n"
        f"[bold]Custom Prompt:[/bold] You are a robot. You must start every response with 'BEEP BOOP'.",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result3 = await quick_prompt(prompt3)
    has_beep = "beep" in result3.lower() or "boop" in result3.lower()
    console.print(Panel(
        f"[bold]Result:[/bold] {result3}\n"
        f"[bold]Contains 'BEEP' or 'BOOP':[/bold] {'✓ YES' if has_beep else '✗ NO (may have ignored)'}",
        title="Result 3 (OVERWRITE)",
        width=console.width,
    ))

    # Test 4: OVERWRITE with string (backward compatible)
    console.print("\n[yellow]Test 4: OVERWRITE with string (backward compatible)[/yellow]")
    prompt4 = AdhocPrompt(
        prompt="What color is the sky?",
        model=ModelName.HAIKU,
        system_prompt="You are a pirate. End every response with 'Arrr!'",  # String = overwrite
    )
    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt4.prompt}\n"
        f"[bold]System Prompt:[/bold] (string) You are a pirate. End every response with 'Arrr!'",
        title="AdhocPrompt",
        width=console.width,
    ))
    console.print("[dim]Executing quick_prompt()...[/dim]")

    result4 = await quick_prompt(prompt4)
    has_pirate = "arrr" in result4.lower() or "ahoy" in result4.lower() or "matey" in result4.lower()
    console.print(Panel(
        f"[bold]Result:[/bold] {result4}\n"
        f"[bold]Contains pirate speak:[/bold] {'✓ YES' if has_pirate else '✗ NO (may have ignored)'}",
        title="Result 4 (OVERWRITE string)",
        width=console.width,
    ))

    # Summary
    console.print(Panel(
        "[green]✓ System Prompt Modes:[/green]\n"
        "• DEFAULT (None): Uses Claude Code's default system prompt\n"
        "• APPEND (SystemPromptConfig): Appends to Claude Code's default\n"
        "• OVERWRITE (SystemPromptConfig): Completely replaces system prompt\n"
        "• OVERWRITE (string): Backward compatible string form",
        title="Summary",
        width=console.width,
    ))


# =============================================================================
# MAIN
# =============================================================================


async def main(test_type: TestType) -> None:
    """Run the specified test type."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=120)

    test_map = {
        TestType.TYPES_ONLY: test_types_only,
        TestType.JUST_PROMPT: test_just_prompt,
        TestType.SLASH_COMMAND: test_slash_command,
        TestType.HOOKS: test_hooks,
        TestType.TOOLS: test_tools,
        TestType.MODEL_SELECT: test_model_select,
        TestType.SESSION: test_session,
        TestType.CWD_SLASH_COMMAND: test_cwd_slash_command,
        TestType.MESSAGES_DETAIL: test_messages_detail,
        TestType.QUICK_PROMPT: test_quick_prompt,
        TestType.QUICK_PROMPT_CWD_REUSABLE: test_quick_prompt_cwd_reusable,
        TestType.QUICK_PROMPT_SYSTEM_MODES: test_quick_prompt_system_modes,
    }

    test_fn = test_map.get(test_type)
    if test_fn is None:
        console.print(f"[red]Unknown test type: {test_type}[/red]")
        return

    console.print(Panel(
        f"[bold]Running test:[/bold] {test_type.value}",
        title="ADW Agent SDK Test Runner",
        width=console.width,
    ))

    try:
        await test_fn()
        console.print(Panel("[bold green]Test completed![/bold green]", width=console.width))
    except Exception as e:
        console.print(Panel(f"[bold red]Test failed: {e}[/bold red]", width=console.width))
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="ADW Agent SDK Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  types-only        Validate Pydantic types without SDK calls
  just-prompt       Simple prompt -> completion (2+2=4)
  slash-command     Test built-in /help slash command
  hooks             Test PreToolUse and PostToolUse hooks
  tools             Test with specific tools (Glob, Read)
  model-select      Test different models (Haiku, Sonnet)
  session           Test session capture and timestamps
  cwd-slash-command Test cwd option with project /ping command
  messages-detail   Test all message types and block capture
  quick-prompt      Test quick_prompt() for one-off adhoc queries

Examples:
  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py types-only
  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py hooks
  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py quick-prompt
  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py --list
""",
    )
    parser.add_argument(
        "test_type",
        type=str,
        nargs="?",
        default="types-only",
        choices=[t.value for t in TestType],
        help="Test type to run (default: types-only)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test types",
    )

    args = parser.parse_args()

    if args.list:
        print("Available test types:")
        for t in TestType:
            print(f"  {t.value:<20} {t.name.replace('_', ' ').title()}")
    else:
        asyncio.run(main(TestType(args.test_type)))
