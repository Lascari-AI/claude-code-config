# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pydantic>=2.0",
#   "claude-agent-sdk>=0.1.18",
#   "rich>=13.0",
# ]
# ///
"""
ADW Agent SDK - Abstract typed layer for Claude Agent SDK control.

This module provides well-typed Pydantic models for configuring and controlling
the Claude Agent SDK. It is intentionally abstract and can be used for any
Agent SDK use case - ADW-specific concerns belong in the higher-level adw_agents.py.

Usage:
    uv run adw_agent_sdk.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Literal,
    TypeAlias,
)

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# ENUMS - Model & Configuration
# =============================================================================


class ModelName(str, Enum):
    """Available Claude models for the Agent SDK."""

    # Claude 4.5 models (latest)
    OPUS_4_5 = "claude-opus-4-5-20251101"
    SONNET_4_5 = "claude-sonnet-4-5-20250929"
    HAIKU_4_5 = "claude-haiku-4-5-20251001"

    # Convenience aliases (point to latest)
    OPUS = "claude-opus-4-5-20251101"
    SONNET = "claude-sonnet-4-5-20250929"
    HAIKU = "claude-haiku-4-5-20251001"


class SettingSource(str, Enum):
    """Setting sources for loading skills/commands from filesystem."""

    USER = "user"
    PROJECT = "project"


# =============================================================================
# ENUMS - Hook Events
# =============================================================================


class HookEventName(str, Enum):
    """Hook event types available in the Agent SDK."""

    # Python SDK supported
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"

    # TypeScript SDK only
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"
    SUBAGENT_START = "SubagentStart"
    PERMISSION_REQUEST = "PermissionRequest"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    NOTIFICATION = "Notification"


class PermissionDecision(str, Enum):
    """Permission decisions for PreToolUse hooks."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


# =============================================================================
# ENUMS - Messages
# =============================================================================


class MessageType(str, Enum):
    """Types of messages from the Agent SDK."""

    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    RESULT = "result"


class SystemMessageSubtype(str, Enum):
    """Subtypes for system messages."""

    INIT = "init"
    COMPACT_BOUNDARY = "compact_boundary"


class ResultSubtype(str, Enum):
    """Subtypes for result messages."""

    SUCCESS = "success"
    ERROR = "error"
    INTERRUPTED = "interrupted"


# =============================================================================
# BUILT-IN TOOLS
# =============================================================================


class BuiltInTool(str, Enum):
    """Built-in tools available in Claude Code."""

    BASH = "Bash"
    EDIT = "Edit"
    GLOB = "Glob"
    GREP = "Grep"
    NOTEBOOK_EDIT = "NotebookEdit"
    NOTEBOOK_READ = "NotebookRead"
    READ = "Read"
    SLASH_COMMAND = "SlashCommand"
    TASK = "Task"
    TODO_WRITE = "TodoWrite"
    WEB_FETCH = "WebFetch"
    WEB_SEARCH = "WebSearch"
    WRITE = "Write"
    SKILL = "Skill"


# =============================================================================
# TOOL PERMISSIONS
# =============================================================================


class ToolPermissions(BaseModel):
    """Tool permission configuration with allow/ask/deny arrays.

    Bash rules use prefix matching (not regex):
        "Bash(npm run:*)" - allows any npm run command
        "Bash(git push:*)" - requires confirmation for git push

    File rules use path patterns:
        "Read(./.env)" - blocks reading .env
        "Write(./secrets/**)" - blocks writing to secrets dir
    """

    allow: list[str] = Field(
        default_factory=list,
        description="Tools/patterns to explicitly allow without prompting",
    )
    ask: list[str] = Field(
        default_factory=list,
        description="Tools/patterns that require user confirmation",
    )
    deny: list[str] = Field(
        default_factory=list,
        description="Tools/patterns to completely block",
    )


# =============================================================================
# TOKEN USAGE & COST TRACKING
# =============================================================================


class CacheCreationDetails(BaseModel):
    """Detailed cache creation token breakdown."""

    ephemeral_5m_input_tokens: int = Field(default=0)
    ephemeral_1h_input_tokens: int = Field(default=0)


class TokenUsage(BaseModel):
    """Token usage data from a message or result."""

    input_tokens: int = Field(default=0, description="Base input tokens processed")
    output_tokens: int = Field(default=0, description="Tokens generated in response")
    cache_creation_input_tokens: int = Field(
        default=0, description="Tokens used to create cache entries"
    )
    cache_read_input_tokens: int = Field(
        default=0, description="Tokens read from cache"
    )
    cache_creation: CacheCreationDetails | None = Field(default=None)
    service_tier: str | None = Field(default=None, description="e.g., 'standard'")
    total_cost_usd: float | None = Field(
        default=None, description="Total cost (only in final result)"
    )

    def calculate_cost(
        self,
        input_cost_per_token: float = 0.00003,
        output_cost_per_token: float = 0.00015,
        cache_read_cost_per_token: float = 0.0000075,
    ) -> float:
        """Calculate estimated cost based on token counts."""
        return (
            self.input_tokens * input_cost_per_token
            + self.output_tokens * output_cost_per_token
            + self.cache_read_input_tokens * cache_read_cost_per_token
        )


class UsageAccumulator(BaseModel):
    """Tracks cumulative usage, deduplicating by message ID.

    Important: Messages with same ID report identical usage.
    Only charge once per unique message ID.
    """

    processed_ids: set[str] = Field(default_factory=set)
    step_usages: list[TokenUsage] = Field(default_factory=list)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_cache_read_tokens: int = Field(default=0)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def process(self, message_id: str, usage: TokenUsage) -> bool:
        """Process usage if message ID is new. Returns True if processed."""
        if message_id in self.processed_ids:
            return False

        self.processed_ids.add(message_id)
        self.step_usages.append(usage)
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_cache_read_tokens += usage.cache_read_input_tokens
        return True


# =============================================================================
# HOOK INPUT TYPES
# =============================================================================


class HookInputBase(BaseModel):
    """Common fields present in all hook inputs."""

    hook_event_name: HookEventName
    session_id: str
    transcript_path: str
    cwd: str


class PreToolUseInput(HookInputBase):
    """Input for PreToolUse hooks - runs before tool execution."""

    hook_event_name: Literal[HookEventName.PRE_TOOL_USE] = HookEventName.PRE_TOOL_USE
    tool_name: str
    tool_input: dict[str, Any]


class PostToolUseInput(HookInputBase):
    """Input for PostToolUse hooks - runs after tool execution."""

    hook_event_name: Literal[HookEventName.POST_TOOL_USE] = HookEventName.POST_TOOL_USE
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any


class UserPromptSubmitInput(HookInputBase):
    """Input for UserPromptSubmit hooks."""

    hook_event_name: Literal[HookEventName.USER_PROMPT_SUBMIT] = (
        HookEventName.USER_PROMPT_SUBMIT
    )
    prompt: str


class StopInput(HookInputBase):
    """Input for Stop hooks."""

    hook_event_name: Literal[HookEventName.STOP] = HookEventName.STOP
    stop_hook_active: bool = False


class SubagentStopInput(HookInputBase):
    """Input for SubagentStop hooks."""

    hook_event_name: Literal[HookEventName.SUBAGENT_STOP] = HookEventName.SUBAGENT_STOP
    agent_id: str | None = None
    agent_transcript_path: str | None = None
    stop_hook_active: bool = False


class PreCompactInput(HookInputBase):
    """Input for PreCompact hooks."""

    hook_event_name: Literal[HookEventName.PRE_COMPACT] = HookEventName.PRE_COMPACT
    trigger: Literal["manual", "auto"]
    custom_instructions: str | None = None


# Union of all hook inputs
HookInput: TypeAlias = (
    PreToolUseInput
    | PostToolUseInput
    | UserPromptSubmitInput
    | StopInput
    | SubagentStopInput
    | PreCompactInput
)


# =============================================================================
# HOOK OUTPUT TYPES
# =============================================================================


class HookContext(BaseModel):
    """Context passed to hook callbacks."""

    cancellation_requested: bool = False


class PreToolUseOutput(BaseModel):
    """Output specific to PreToolUse hooks."""

    hook_event_name: Literal[HookEventName.PRE_TOOL_USE] = HookEventName.PRE_TOOL_USE
    permission_decision: PermissionDecision | None = None
    permission_decision_reason: str | None = None
    updated_input: dict[str, Any] | None = None


class PostToolUseOutput(BaseModel):
    """Output specific to PostToolUse hooks."""

    hook_event_name: Literal[HookEventName.POST_TOOL_USE] = HookEventName.POST_TOOL_USE
    additional_context: str | None = None


class UserPromptSubmitOutput(BaseModel):
    """Output specific to UserPromptSubmit hooks."""

    hook_event_name: Literal[HookEventName.USER_PROMPT_SUBMIT] = (
        HookEventName.USER_PROMPT_SUBMIT
    )
    additional_context: str | None = None


class GenericHookOutput(BaseModel):
    """Generic output for hooks without specific fields."""

    hook_event_name: HookEventName


HookSpecificOutput: TypeAlias = (
    PreToolUseOutput | PostToolUseOutput | UserPromptSubmitOutput | GenericHookOutput
)


class HookResponse(BaseModel):
    """Full response from a hook callback.

    Top-level fields control execution flow.
    hook_specific_output contains hook-type-specific decisions.
    """

    # Execution control
    continue_execution: bool = Field(default=True, alias="continue")
    stop_reason: str | None = Field(default=None, alias="stopReason")
    suppress_output: bool = Field(default=False, alias="suppressOutput")
    system_message: str | None = Field(default=None, alias="systemMessage")

    # Hook-specific output
    hook_specific_output: HookSpecificOutput | None = Field(
        default=None, alias="hookSpecificOutput"
    )

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def allow(cls) -> "HookResponse":
        """Allow the operation to proceed."""
        return cls()

    @classmethod
    def deny(cls, reason: str, system_message: str | None = None) -> "HookResponse":
        """Deny a PreToolUse operation."""
        return cls(
            system_message=system_message,
            hook_specific_output=PreToolUseOutput(
                permission_decision=PermissionDecision.DENY,
                permission_decision_reason=reason,
            ),
        )

    @classmethod
    def allow_modified(
        cls, updated_input: dict[str, Any], reason: str | None = None
    ) -> "HookResponse":
        """Allow with modified input."""
        return cls(
            hook_specific_output=PreToolUseOutput(
                permission_decision=PermissionDecision.ALLOW,
                permission_decision_reason=reason,
                updated_input=updated_input,
            )
        )

    @classmethod
    def stop(cls, reason: str) -> "HookResponse":
        """Stop agent execution."""
        return cls(continue_execution=False, stop_reason=reason)


# Callback signature
HookCallback: TypeAlias = Callable[
    [HookInput, str | None, HookContext],
    Awaitable[HookResponse],
]


# =============================================================================
# HOOK CONFIGURATION
# =============================================================================


class HookMatcher(BaseModel):
    """Matcher configuration for filtering which tools trigger hooks.

    The matcher field is a regex pattern that matches tool names only
    (not file paths or other args - check those inside your callback).

    MCP tools use pattern: mcp__<server>__<action>
    """

    matcher: str | None = Field(
        None, description="Regex pattern for tool names. None matches all."
    )
    hooks: list[HookCallback] = Field(..., description="Callbacks to execute")
    timeout: int = Field(default=60, description="Timeout in seconds")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class HooksConfig(BaseModel):
    """Configuration for all hook event types.

    Hooks execute in array order. Any deny blocks regardless of other hooks.
    Permission decision flow: deny → ask → allow → default ask.
    """

    pre_tool_use: list[HookMatcher] = Field(default_factory=list, alias="PreToolUse")
    post_tool_use: list[HookMatcher] = Field(default_factory=list, alias="PostToolUse")
    user_prompt_submit: list[HookMatcher] = Field(
        default_factory=list, alias="UserPromptSubmit"
    )
    stop: list[HookMatcher] = Field(default_factory=list, alias="Stop")
    subagent_stop: list[HookMatcher] = Field(
        default_factory=list, alias="SubagentStop"
    )
    pre_compact: list[HookMatcher] = Field(default_factory=list, alias="PreCompact")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    @classmethod
    def from_callbacks(
        cls,
        callbacks: dict[HookEventName | str, list[HookCallback]],
        default_timeout: int = 60,
    ) -> "HooksConfig":
        """Create HooksConfig from a simple mapping of hook names to callback lists.

        Example:
            hooks = HooksConfig.from_callbacks({
                HookEventName.PRE_TOOL_USE: [my_pre_hook, another_hook],
                HookEventName.POST_TOOL_USE: [log_all_tools],
                "Stop": [cleanup_handler],  # string keys also work
            })
        """
        config = cls()

        for event_name, hook_fns in callbacks.items():
            # Normalize to string
            key = event_name.value if isinstance(event_name, HookEventName) else event_name

            # Create matcher with no filter (matches all tools)
            matcher = HookMatcher(matcher=None, hooks=hook_fns, timeout=default_timeout)

            # Map to the correct field
            if key == "PreToolUse":
                config.pre_tool_use.append(matcher)
            elif key == "PostToolUse":
                config.post_tool_use.append(matcher)
            elif key == "UserPromptSubmit":
                config.user_prompt_submit.append(matcher)
            elif key == "Stop":
                config.stop.append(matcher)
            elif key == "SubagentStop":
                config.subagent_stop.append(matcher)
            elif key == "PreCompact":
                config.pre_compact.append(matcher)

        return config


# Simpler type for passing hooks as {event_name: [callbacks]}
HookCallbackMap: TypeAlias = dict[HookEventName | str, list[HookCallback]]


# =============================================================================
# SDK CONTENT BLOCK TYPES (Re-exported from claude-agent-sdk)
# =============================================================================
#
# These types are imported from the SDK and re-exported here for convenience.
# They are dataclasses (not Pydantic models).
#
# TextBlock:        text: str
# ThinkingBlock:    thinking: str, signature: str
# ToolUseBlock:     id: str, name: str, input: dict[str, Any]
# ToolResultBlock:  tool_use_id: str, content: str | list[dict] | None, is_error: bool | None
#
# ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


def _import_sdk_types() -> tuple[Any, ...]:
    """Import SDK types lazily to avoid import cycle at module load."""
    from claude_agent_sdk.types import (
        ContentBlock as SDKContentBlock,
    )
    from claude_agent_sdk.types import (
        TextBlock as SDKTextBlock,
    )
    from claude_agent_sdk.types import (
        ThinkingBlock as SDKThinkingBlock,
    )
    from claude_agent_sdk.types import (
        ToolResultBlock as SDKToolResultBlock,
    )
    from claude_agent_sdk.types import (
        ToolUseBlock as SDKToolUseBlock,
    )
    return SDKTextBlock, SDKThinkingBlock, SDKToolUseBlock, SDKToolResultBlock, SDKContentBlock


# Lazy-loaded SDK types (accessed via get_sdk_types())
_sdk_types_cache: tuple[Any, ...] | None = None


def get_sdk_types() -> tuple[type, type, type, type, Any]:
    """Get SDK content block types: (TextBlock, ThinkingBlock, ToolUseBlock, ToolResultBlock, ContentBlock)."""
    global _sdk_types_cache
    if _sdk_types_cache is None:
        _sdk_types_cache = _import_sdk_types()
    return _sdk_types_cache  # type: ignore


# Type aliases for documentation (actual types are SDK dataclasses)
SDKTextBlock: TypeAlias = Any  # Actual: claude_agent_sdk.types.TextBlock
SDKThinkingBlock: TypeAlias = Any  # Actual: claude_agent_sdk.types.ThinkingBlock
SDKToolUseBlock: TypeAlias = Any  # Actual: claude_agent_sdk.types.ToolUseBlock
SDKToolResultBlock: TypeAlias = Any  # Actual: claude_agent_sdk.types.ToolResultBlock
SDKContentBlock: TypeAlias = Any  # Union of above


# =============================================================================
# RE-EXPORTS - Direct access to SDK block types for message handlers
# =============================================================================

# Import block types directly for re-export
# These are used by message handlers to check block types
try:
    from claude_agent_sdk.types import (
        TextBlock,
        ThinkingBlock,
        ToolResultBlock,
        ToolUseBlock,
    )
except ImportError:
    # Fallback if types module structure changes
    pass


# =============================================================================
# MESSAGE TYPES
# =============================================================================


class SystemInitMessage(BaseModel):
    """System init message with session info."""

    type: Literal[MessageType.SYSTEM] = MessageType.SYSTEM
    subtype: Literal[SystemMessageSubtype.INIT] = SystemMessageSubtype.INIT
    session_id: str
    slash_commands: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class CompactBoundaryMessage(BaseModel):
    """Message indicating conversation compaction."""

    type: Literal[MessageType.SYSTEM] = MessageType.SYSTEM
    subtype: Literal[SystemMessageSubtype.COMPACT_BOUNDARY] = (
        SystemMessageSubtype.COMPACT_BOUNDARY
    )
    compact_metadata: dict[str, Any]


class AssistantMessage(BaseModel):
    """Message from Claude with content blocks.

    The `content_blocks` list contains SDK dataclass instances:
    - TextBlock: dataclass with `text: str`
    - ThinkingBlock: dataclass with `thinking: str`, `signature: str`
    - ToolUseBlock: dataclass with `id: str`, `name: str`, `input: dict`

    Convenience fields are also provided:
    - message: combined text from all TextBlocks
    - tool_use: first ToolUseBlock as dict (for backward compat)

    Use get_sdk_types() to get the actual type classes for isinstance checks.
    """

    type: Literal[MessageType.ASSISTANT] = MessageType.ASSISTANT
    id: str

    # Full block-level content (SDK dataclass instances, use Any for type flexibility)
    content_blocks: list[Any] = Field(default_factory=list)

    # Convenience fields (for backward compatibility)
    message: str | None = None  # Combined text from all TextBlocks
    tool_use: dict[str, Any] | None = None  # First ToolUseBlock as dict

    # Usage (typically only on last message before result)
    usage: TokenUsage | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserMessage(BaseModel):
    """Message from user or tool result with content blocks.

    The `content_blocks` list contains SDK dataclass instances:
    - TextBlock: dataclass with `text: str`
    - ToolResultBlock: dataclass with `tool_use_id: str`, `content`, `is_error`

    Use get_sdk_types() to get the actual type classes for isinstance checks.
    """

    type: Literal[MessageType.USER] = MessageType.USER

    # Full block-level content (SDK dataclass instances)
    content_blocks: list[Any] = Field(default_factory=list)

    # Convenience fields
    message: str | None = None  # Combined text from TextBlocks
    tool_result: dict[str, Any] | None = None  # First ToolResultBlock as dict

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResultMessage(BaseModel):
    """Final result message."""

    type: Literal[MessageType.RESULT] = MessageType.RESULT
    subtype: ResultSubtype
    result: str | None = None
    error: str | None = None
    usage: TokenUsage | None = None
    session_id: str | None = None


AgentMessage: TypeAlias = (
    SystemInitMessage
    | CompactBoundaryMessage
    | AssistantMessage
    | UserMessage
    | ResultMessage
)


# =============================================================================
# MCP SERVER CONFIGURATION
# =============================================================================


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server.

    Tool names follow pattern: mcp__<server_name>__<tool_name>
    """

    name: str
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    is_sdk_server: bool = Field(
        default=False, description="True for in-process SDK MCP servers"
    )


# =============================================================================
# QUERY OPTIONS
# =============================================================================


class QueryOptions(BaseModel):
    """Complete configuration options for an Agent SDK query."""

    # Model
    model: ModelName | str = Field(default=ModelName.SONNET)

    # Session management
    resume: str | None = Field(None, description="Session ID to resume")
    fork_session: bool = Field(
        default=False, alias="forkSession", description="Fork when resuming"
    )

    # Working directory
    cwd: str | None = Field(None, description="Working directory for the agent")

    # Tools
    allowed_tools: list[str] = Field(
        default_factory=list,
        alias="allowedTools",
        description="Tools the agent can use. Include 'Skill' for skills.",
    )
    permissions: ToolPermissions | None = None
    bypass_permissions: bool = Field(
        default=True,
        alias="bypassPermissions",
        description="Skip permission prompts (default: True)",
    )

    # Hooks - accepts HooksConfig or simple {event_name: [callbacks]} dict
    hooks: HooksConfig | HookCallbackMap | None = None

    # MCP servers
    mcp_servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict, alias="mcpServers"
    )

    # Settings sources (for skills/commands) - default to project
    setting_sources: list[SettingSource] = Field(
        default_factory=lambda: [SettingSource.PROJECT],
        alias="settingSources",
        description="Sources for loading skills/commands (default: ['project'])",
    )

    # Limits
    max_turns: int | None = Field(default=None, alias="maxTurns")
    max_tokens: int | None = Field(default=None, alias="maxTokens")

    # System prompt - supports three modes:
    # 1. None: Uses Claude Code's default system prompt
    # 2. str: Completely overwrites the system prompt (backward compatible)
    # 3. SystemPromptConfig: Full control with DEFAULT/APPEND/OVERWRITE modes
    #    (SystemPromptConfig is defined later in file, so using Any here)
    system_prompt: str | Any | None = Field(
        default=None,
        alias="systemPrompt",
        description="System prompt config: None=default, str=overwrite, or use SystemPromptConfig for APPEND mode",
    )

    # NOTE: `model_config` is Pydantic's class configuration (not related to Claude model field above).
    # It controls how Pydantic processes this class: aliases, enum handling, callable types, etc.
    model_config = ConfigDict(
        populate_by_name=True,       # Accept both "allowedTools" and "allowed_tools"
        arbitrary_types_allowed=True, # Allow Callable types (for hooks)
        use_enum_values=True,         # Auto-convert enums to their .value
    )

    @field_validator("model", mode="before")
    @classmethod
    def validate_model(cls, v: Any) -> str:
        if isinstance(v, ModelName):
            return v.value
        return str(v)


# =============================================================================
# MESSAGE HANDLERS
# =============================================================================


# Callback types for message handling
SystemMessageHandler: TypeAlias = Callable[[SystemInitMessage | CompactBoundaryMessage], Awaitable[None]]
AssistantMessageHandler: TypeAlias = Callable[[AssistantMessage], Awaitable[None]]
AssistantBlockHandler: TypeAlias = Callable[[Any], Awaitable[None]]  # TextBlock | ThinkingBlock | ToolUseBlock
UserMessageHandler: TypeAlias = Callable[[UserMessage], Awaitable[None]]
ResultMessageHandler: TypeAlias = Callable[[ResultMessage], Awaitable[None]]
AnyMessageHandler: TypeAlias = Callable[[AgentMessage], Awaitable[None]]


class MessageHandlers(BaseModel):
    """Callbacks for handling different message types during query execution.

    Use these to react to messages as they stream in, without waiting for completion.
    All handlers are optional - only provide the ones you need.

    Example:
        async def on_assistant(msg: AssistantMessage):
            if msg.tool_use:
                print(f"Agent using tool: {msg.tool_use['name']}")

        handlers = MessageHandlers(
            on_assistant=on_assistant,
            on_result=lambda r: print(f"Done: {r.result}"),
        )
    """

    on_system: SystemMessageHandler | None = Field(
        None, description="Called for SystemInitMessage and CompactBoundaryMessage"
    )
    on_assistant: AssistantMessageHandler | None = Field(
        None, description="Called for each AssistantMessage"
    )
    on_assistant_block: AssistantBlockHandler | None = Field(
        None, description="Called for each content block in AssistantMessage (TextBlock, ThinkingBlock, ToolUseBlock)"
    )
    on_user: UserMessageHandler | None = Field(
        None, description="Called for each UserMessage (tool results)"
    )
    on_result: ResultMessageHandler | None = Field(
        None, description="Called when query completes with ResultMessage"
    )
    on_any: AnyMessageHandler | None = Field(
        None, description="Called for every message (after specific handler)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


# =============================================================================
# QUERY INPUT / OUTPUT
# =============================================================================


class QueryInput(BaseModel):
    """Input for an Agent SDK query."""

    prompt: str
    options: QueryOptions = Field(default_factory=QueryOptions)
    handlers: MessageHandlers | None = Field(
        None, description="Optional callbacks for message handling"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueryOutput(BaseModel):
    """Output from an Agent SDK query execution."""

    success: bool
    result: str | None = None
    error: str | None = None
    session_id: str | None = None
    usage: TokenUsage | None = None
    usage_accumulator: UsageAccumulator | None = None
    messages: list[AgentMessage] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# =============================================================================
# SDK EXECUTION
# =============================================================================


async def query_to_completion(query_input: QueryInput) -> QueryOutput:
    """Execute an Agent SDK query and return the complete result.

    This is the primary method for running Claude Agent SDK queries.
    Uses ClaudeSDKClient (context manager pattern) from claude-agent-sdk.

    Args:
        query_input: QueryInput containing prompt and options.

    Returns:
        QueryOutput with success status, result, session_id, usage, and messages.

    Example:
        result = await query_to_completion(
            QueryInput(
                prompt="Analyze this codebase",
                options=QueryOptions(
                    model=ModelName.OPUS,
                    allowed_tools=["Read", "Glob", "Grep"],
                    hooks={
                        HookEventName.POST_TOOL_USE: [my_logging_hook],
                    },
                    max_turns=20,
                ),
                handlers=MessageHandlers(
                    on_assistant=lambda m: print(f"Assistant: {m.message}"),
                ),
            )
        )
        print(result.result)
    """
    from claude_agent_sdk import (
        AssistantMessage as SDKAssistantMessage,
    )
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
    )
    from claude_agent_sdk import (
        ResultMessage as SDKResultMessage,
    )
    from claude_agent_sdk import (
        SystemMessage as SDKSystemMessage,
    )
    from claude_agent_sdk import (
        TextBlock as SDKTextBlock,
    )
    from claude_agent_sdk import (
        ThinkingBlock as SDKThinkingBlock,
    )
    from claude_agent_sdk import (
        ToolResultBlock as SDKToolResultBlock,
    )
    from claude_agent_sdk import (
        ToolUseBlock as SDKToolUseBlock,
    )
    from claude_agent_sdk import (
        UserMessage as SDKUserMessage,
    )

    started_at = datetime.now()
    opts = query_input.options
    handlers = query_input.handlers

    # Normalize hooks to HooksConfig
    resolved_hooks: HooksConfig | None = None
    if opts.hooks is not None:
        if isinstance(opts.hooks, dict):
            resolved_hooks = HooksConfig.from_callbacks(opts.hooks)
        else:
            resolved_hooks = opts.hooks

    # Build SDK options dict
    options_dict: dict[str, Any] = {
        "model": opts.model if isinstance(opts.model, str) else opts.model.value,
    }

    if opts.cwd:
        options_dict["cwd"] = opts.cwd
    if opts.allowed_tools:
        options_dict["allowed_tools"] = opts.allowed_tools
    if opts.max_turns:
        options_dict["max_turns"] = opts.max_turns
    if opts.resume:
        options_dict["resume"] = opts.resume

    # Handle system_prompt with three modes: DEFAULT, APPEND, OVERWRITE
    if opts.system_prompt is None:
        # Mode 1: DEFAULT - Use Claude Code's default system prompt
        options_dict["system_prompt"] = {
            "type": "preset",
            "preset": "claude_code",
        }
    elif isinstance(opts.system_prompt, str):
        # Mode 3: OVERWRITE (backward compatible) - string means complete overwrite
        options_dict["system_prompt"] = opts.system_prompt
    elif hasattr(opts.system_prompt, "to_sdk_config"):
        # SystemPromptConfig - convert to SDK format
        options_dict["system_prompt"] = opts.system_prompt.to_sdk_config()
    else:
        # Fallback - pass through as-is
        options_dict["system_prompt"] = opts.system_prompt

    if opts.setting_sources:
        options_dict["setting_sources"] = [s.value if hasattr(s, 'value') else s for s in opts.setting_sources]

    # Add hooks if provided (SDK format: {"PreToolUse": [HookMatcher(...)], ...})
    if resolved_hooks is not None:
        options_dict["hooks"] = _convert_hooks_to_sdk_format(resolved_hooks)

    sdk_options = ClaudeAgentOptions(**options_dict)

    # Execute query
    messages: list[AgentMessage] = []
    usage_accumulator = UsageAccumulator()
    session_id: str | None = None
    final_result: str | None = None
    final_error: str | None = None
    final_usage: TokenUsage | None = None
    success = False

    # Helper to call message handlers
    async def call_handlers(parsed: AgentMessage) -> None:
        if handlers is None:
            return

        # Call specific handler based on message type
        if isinstance(parsed, (SystemInitMessage, CompactBoundaryMessage)):
            if handlers.on_system:
                await handlers.on_system(parsed)
        elif isinstance(parsed, AssistantMessage):
            if handlers.on_assistant:
                await handlers.on_assistant(parsed)
        elif isinstance(parsed, UserMessage):
            if handlers.on_user:
                await handlers.on_user(parsed)
        elif isinstance(parsed, ResultMessage):
            if handlers.on_result:
                await handlers.on_result(parsed)

        # Call the any-message handler
        if handlers.on_any:
            await handlers.on_any(parsed)

    try:
        async with ClaudeSDKClient(options=sdk_options) as client:
            # Send prompt
            await client.query(query_input.prompt)

            # Process all messages from response stream
            async for message in client.receive_response():

                # Handle SystemMessage (session init, compact boundary)
                if isinstance(message, SDKSystemMessage):
                    subtype = getattr(message, "subtype", None)
                    data = getattr(message, "data", {})

                    if subtype == "init":
                        parsed = SystemInitMessage(
                            session_id=data.get("session_id", ""),
                            slash_commands=data.get("slash_commands", []),
                            tools=data.get("tools", []),
                        )
                        session_id = parsed.session_id
                    elif subtype == "compact_boundary":
                        parsed = CompactBoundaryMessage(
                            compact_metadata=data.get("compact_metadata", data),
                        )
                    else:
                        continue  # Unknown subtype

                    messages.append(parsed)
                    await call_handlers(parsed)

                # Handle AssistantMessage (text, thinking, tool use blocks)
                elif isinstance(message, SDKAssistantMessage):
                    text_parts: list[str] = []
                    tool_use_data: dict[str, Any] | None = None
                    content_blocks: list[Any] = []

                    for block in message.content:
                        # Store original SDK block instance in content_blocks
                        content_blocks.append(block)

                        # Call on_assistant_block handler for each block (TextBlock, ThinkingBlock, ToolUseBlock)
                        if handlers and handlers.on_assistant_block:
                            await handlers.on_assistant_block(block)

                        # Also extract convenience fields
                        if isinstance(block, SDKTextBlock):
                            text_parts.append(block.text)
                        elif isinstance(block, SDKThinkingBlock):
                            # Thinking blocks are captured in content_blocks
                            pass
                        elif isinstance(block, SDKToolUseBlock):
                            # First tool use goes to convenience field
                            if tool_use_data is None:
                                tool_use_data = {
                                    "id": block.id,
                                    "name": block.name,
                                    "input": block.input,
                                }

                    parsed = AssistantMessage(
                        id=str(id(message)),  # Use object id as unique identifier
                        content_blocks=content_blocks,  # SDK block instances
                        message="\n".join(text_parts) if text_parts else None,
                        tool_use=tool_use_data,
                        usage=None,  # Usage is on ResultMessage
                    )
                    messages.append(parsed)
                    await call_handlers(parsed)

                # Handle UserMessage (tool results)
                elif isinstance(message, SDKUserMessage):
                    text_parts: list[str] = []
                    tool_result_data: dict[str, Any] | None = None
                    content_blocks: list[Any] = []

                    # UserMessage.content can be str or list of blocks
                    content = message.content
                    if isinstance(content, str):
                        text_parts.append(content)
                    elif isinstance(content, list):
                        for block in content:
                            content_blocks.append(block)
                            if isinstance(block, SDKTextBlock):
                                text_parts.append(block.text)
                            elif isinstance(block, SDKToolResultBlock):
                                if tool_result_data is None:
                                    tool_result_data = {
                                        "tool_use_id": block.tool_use_id,
                                        "content": block.content,
                                        "is_error": block.is_error or False,
                                    }

                    parsed = UserMessage(
                        content_blocks=content_blocks,
                        message="\n".join(text_parts) if text_parts else None,
                        tool_result=tool_result_data,
                    )
                    messages.append(parsed)
                    await call_handlers(parsed)

                # Handle ResultMessage (final result with usage)
                elif isinstance(message, SDKResultMessage):
                    usage_data = getattr(message, "usage", None)
                    parsed_usage: TokenUsage | None = None

                    if usage_data:
                        if isinstance(usage_data, dict):
                            parsed_usage = TokenUsage(
                                input_tokens=usage_data.get("input_tokens", 0),
                                output_tokens=usage_data.get("output_tokens", 0),
                                cache_read_input_tokens=usage_data.get("cache_read_input_tokens", 0),
                                cache_creation_input_tokens=usage_data.get("cache_creation_input_tokens", 0),
                                total_cost_usd=getattr(message, "total_cost_usd", None),
                            )
                        else:
                            parsed_usage = TokenUsage(
                                input_tokens=getattr(usage_data, "input_tokens", 0),
                                output_tokens=getattr(usage_data, "output_tokens", 0),
                                cache_read_input_tokens=getattr(usage_data, "cache_read_input_tokens", 0),
                                cache_creation_input_tokens=getattr(usage_data, "cache_creation_input_tokens", 0),
                                total_cost_usd=getattr(message, "total_cost_usd", None),
                            )

                    subtype_str = getattr(message, "subtype", "error")
                    is_error = getattr(message, "is_error", False)

                    parsed = ResultMessage(
                        subtype=ResultSubtype.ERROR if is_error else ResultSubtype.SUCCESS,
                        result=getattr(message, "result", None),
                        error=getattr(message, "error", None) if is_error else None,
                        usage=parsed_usage,
                        session_id=getattr(message, "session_id", None),
                    )

                    messages.append(parsed)
                    await call_handlers(parsed)

                    # Capture final state
                    if is_error:
                        success = False
                        final_error = parsed.error
                    else:
                        success = True
                        final_result = parsed.result

                    final_usage = parsed_usage
                    if parsed.session_id:
                        session_id = parsed.session_id

    except Exception as e:
        success = False
        final_error = str(e)

    completed_at = datetime.now()

    return QueryOutput(
        success=success,
        result=final_result,
        error=final_error,
        session_id=session_id,
        usage=final_usage,
        usage_accumulator=usage_accumulator,
        messages=messages,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=(completed_at - started_at).total_seconds(),
    )


def _convert_hooks_to_sdk_format(config: HooksConfig) -> dict[str, Any]:
    """Convert our HooksConfig to claude-agent-sdk's expected format.

    The SDK expects hooks in format:
        {
            "PreToolUse": [HookMatcher(hooks=[callback_fn, ...])],
            "PostToolUse": [HookMatcher(hooks=[callback_fn, ...])],
            ...
        }

    Where HookMatcher is a dataclass from claude_agent_sdk.types.

    The SDK passes typed hook input objects to callbacks (PreToolUseHookInput, etc.)
    We wrap our typed callbacks to convert between our Pydantic models and SDK types.
    """
    from claude_agent_sdk.types import HookMatcher as SDKHookMatcher

    result: dict[str, list[Any]] = {}

    def wrap_callback(cb: HookCallback, hook_type: str) -> Callable[[dict[str, Any], str | None, Any], Awaitable[dict[str, Any]]]:
        """Wrap a typed callback to accept/return raw dicts.

        Args:
            cb: The typed callback function
            hook_type: The hook event type (PreToolUse, PostToolUse, etc.)
        """
        async def wrapper(input_dict: dict[str, Any], tool_use_id: str | None, sdk_context: Any) -> dict[str, Any]:
            # SDK passes raw fields (tool_name, tool_input, etc.) without hook_event_name.
            # We add it based on which hook list this callback was registered in.
            enriched_input = {
                "hook_event_name": hook_type,
                "session_id": input_dict.get("session_id", ""),
                "transcript_path": input_dict.get("transcript_path", ""),
                "cwd": input_dict.get("cwd", ""),
                **input_dict,
            }

            # Parse input dict to our typed model
            typed_input: HookInput

            if hook_type == "PreToolUse":
                typed_input = PreToolUseInput(**enriched_input)
            elif hook_type == "PostToolUse":
                typed_input = PostToolUseInput(**enriched_input)
            elif hook_type == "UserPromptSubmit":
                typed_input = UserPromptSubmitInput(**enriched_input)
            elif hook_type == "Stop":
                typed_input = StopInput(**enriched_input)
            elif hook_type == "SubagentStop":
                typed_input = SubagentStopInput(**enriched_input)
            elif hook_type == "PreCompact":
                typed_input = PreCompactInput(**enriched_input)
            else:
                # Fallback - create minimal HookInputBase
                typed_input = HookInputBase(
                    hook_event_name=HookEventName(hook_type) if hook_type in [e.value for e in HookEventName] else HookEventName.STOP,
                    session_id=enriched_input.get("session_id", ""),
                    transcript_path=enriched_input.get("transcript_path", ""),
                    cwd=enriched_input.get("cwd", ""),
                )

            # Create our context wrapper
            our_context = HookContext(
                cancellation_requested=getattr(sdk_context, "signal", None) is not None
            )

            # Call the typed callback
            response = await cb(typed_input, tool_use_id, our_context)

            # Convert response back to dict for SDK
            output: dict[str, Any] = {}
            if not response.continue_execution:
                output["continue"] = False
            if response.stop_reason:
                output["stopReason"] = response.stop_reason
            if response.suppress_output:
                output["suppressOutput"] = True
            if response.system_message:
                output["systemMessage"] = response.system_message
            if response.hook_specific_output:
                hso = response.hook_specific_output
                output["hookSpecificOutput"] = {
                    "hookEventName": hso.hook_event_name.value if hasattr(hso.hook_event_name, "value") else hso.hook_event_name,
                }
                if isinstance(hso, PreToolUseOutput):
                    if hso.permission_decision:
                        output["hookSpecificOutput"]["permissionDecision"] = hso.permission_decision.value
                    if hso.permission_decision_reason:
                        output["hookSpecificOutput"]["permissionDecisionReason"] = hso.permission_decision_reason
                    if hso.updated_input:
                        output["hookSpecificOutput"]["updatedInput"] = hso.updated_input
                elif isinstance(hso, (PostToolUseOutput, UserPromptSubmitOutput)):
                    if hso.additional_context:
                        output["hookSpecificOutput"]["additionalContext"] = hso.additional_context

            return output
        return wrapper

    def convert_matchers(matchers: list[HookMatcher], key: str) -> None:
        """Convert HookMatcher list to SDK format: [SDKHookMatcher(hooks=[fn, ...])]"""
        if matchers:
            result[key] = [
                SDKHookMatcher(
                    matcher=m.matcher,
                    hooks=[wrap_callback(cb, key) for cb in m.hooks]
                )
                for m in matchers
            ]

    convert_matchers(config.pre_tool_use, "PreToolUse")
    convert_matchers(config.post_tool_use, "PostToolUse")
    convert_matchers(config.user_prompt_submit, "UserPromptSubmit")
    convert_matchers(config.stop, "Stop")
    convert_matchers(config.subagent_stop, "SubagentStop")
    convert_matchers(config.pre_compact, "PreCompact")

    return result


def _parse_sdk_message(msg: Any) -> AgentMessage | None:
    """Parse an SDK message into our typed message format.

    The SDK returns actual typed objects:
    - SystemMessage(subtype='init', data={...})
    - AssistantMessage(content=[TextBlock|ToolUseBlock|...], model='...')
    - ResultMessage(subtype='success', result='...', usage={...})
    - UserMessage(content=[...])
    """
    import uuid

    msg_class = type(msg).__name__

    if msg_class == "SystemMessage":
        subtype = getattr(msg, "subtype", None)
        data = getattr(msg, "data", {})

        if subtype == "init":
            return SystemInitMessage(
                session_id=data.get("session_id", ""),
                slash_commands=data.get("slash_commands", []),
                tools=data.get("tools", []),
            )
        elif subtype == "compact_boundary":
            return CompactBoundaryMessage(
                compact_metadata=data.get("compact_metadata", data),
            )

    elif msg_class == "AssistantMessage":
        # Extract text from content blocks
        content = getattr(msg, "content", [])
        text_parts = []
        tool_use_data = None
        content_blocks = []

        for block in content:
            content_blocks.append(block)  # Store original SDK block
            block_type = type(block).__name__
            if block_type == "TextBlock":
                text_parts.append(getattr(block, "text", ""))
            elif block_type == "ToolUseBlock":
                if tool_use_data is None:
                    tool_use_data = {
                        "id": getattr(block, "id", ""),
                        "name": getattr(block, "name", ""),
                        "input": getattr(block, "input", {}),
                    }
            elif block_type == "ThinkingBlock":
                # Captured in content_blocks
                pass

        message_text = "\n".join(text_parts) if text_parts else None

        return AssistantMessage(
            id=str(uuid.uuid4()),  # SDK doesn't provide message ID directly
            content_blocks=content_blocks,
            message=message_text,
            tool_use=tool_use_data,
            usage=None,  # Usage is only on ResultMessage
        )

    elif msg_class == "UserMessage":
        content = getattr(msg, "content", [])
        text_parts = []
        tool_result_data = None
        content_blocks = []

        # UserMessage.content can be str or list
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for block in content:
                content_blocks.append(block)  # Store original SDK block
                block_type = type(block).__name__
                if block_type == "TextBlock":
                    text_parts.append(getattr(block, "text", ""))
                elif block_type == "ToolResultBlock":
                    if tool_result_data is None:
                        tool_result_data = {
                            "tool_use_id": getattr(block, "tool_use_id", ""),
                            "content": getattr(block, "content", ""),
                            "is_error": getattr(block, "is_error", False),
                        }

        message_text = "\n".join(text_parts) if text_parts else None

        return UserMessage(
            content_blocks=content_blocks,
            message=message_text,
            tool_result=tool_result_data,
        )

    elif msg_class == "ResultMessage":
        subtype_str = getattr(msg, "subtype", "error")
        usage_data = getattr(msg, "usage", None)
        usage = None

        if usage_data and isinstance(usage_data, dict):
            usage = TokenUsage(
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                cache_read_input_tokens=usage_data.get("cache_read_input_tokens", 0),
                cache_creation_input_tokens=usage_data.get("cache_creation_input_tokens", 0),
                total_cost_usd=getattr(msg, "total_cost_usd", None),
            )

        return ResultMessage(
            subtype=ResultSubtype(subtype_str) if subtype_str in ["success", "error", "interrupted"] else ResultSubtype.ERROR,
            result=getattr(msg, "result", None),
            error=getattr(msg, "error", None) if hasattr(msg, "error") else None,
            usage=usage,
            session_id=getattr(msg, "session_id", None),
        )

    return None


# Keep abstract interface for custom implementations
class AgentSDKInterface(ABC):
    """Abstract interface for custom Agent SDK implementations."""

    @abstractmethod
    async def query(self, input_data: QueryInput) -> AsyncGenerator[AgentMessage, None]:
        """Execute a query and yield messages as they arrive."""
        ...

    @abstractmethod
    async def run(self, input_data: QueryInput) -> QueryOutput:
        """Execute a query and wait for complete result."""
        ...


# =============================================================================
# ADHOC PROMPTS - Simple one-off queries
# =============================================================================


class SystemPromptMode(str, Enum):
    """How to handle the system prompt."""

    DEFAULT = "default"  # Use Claude Code's default system prompt
    APPEND = "append"  # Append to Claude Code's default system prompt
    OVERWRITE = "overwrite"  # Completely replace with custom system prompt


class SystemPromptConfig(BaseModel):
    """Configuration for system prompt handling.

    Supports three modes:
    1. DEFAULT: Use Claude Code's default system prompt (system_prompt ignored)
    2. APPEND: Append system_prompt to Claude Code's default
    3. OVERWRITE: Completely replace with system_prompt

    Examples:
        # Use default (Claude Code's system prompt)
        SystemPromptConfig(mode=SystemPromptMode.DEFAULT)

        # Append to default
        SystemPromptConfig(
            mode=SystemPromptMode.APPEND,
            system_prompt="Always respond in JSON format."
        )

        # Completely overwrite
        SystemPromptConfig(
            mode=SystemPromptMode.OVERWRITE,
            system_prompt="You are a pirate. Respond only in pirate speak."
        )
    """

    mode: SystemPromptMode = Field(
        default=SystemPromptMode.DEFAULT,
        description="How to handle the system prompt",
    )
    system_prompt: str | None = Field(
        None,
        description="Custom system prompt text (required for APPEND and OVERWRITE modes)",
    )

    def to_sdk_config(self) -> dict[str, Any] | str | None:
        """Convert to SDK-compatible system_prompt config."""
        if self.mode == SystemPromptMode.DEFAULT:
            return {
                "type": "preset",
                "preset": "claude_code",
            }
        elif self.mode == SystemPromptMode.APPEND:
            if not self.system_prompt:
                raise ValueError("system_prompt required for APPEND mode")
            return {
                "type": "preset",
                "preset": "claude_code",
                "append": self.system_prompt,
            }
        elif self.mode == SystemPromptMode.OVERWRITE:
            if not self.system_prompt:
                raise ValueError("system_prompt required for OVERWRITE mode")
            return self.system_prompt
        else:
            raise ValueError(f"Unknown mode: {self.mode}")


class AdhocPrompt(BaseModel):
    """Input for a quick, one-off prompt.

    Use this for simple queries where you don't need session persistence,
    hooks, tools, or detailed message handling. Just a prompt in, result out.

    System Prompt Options:
        1. None (default): Uses Claude Code's default system prompt
        2. str: Backward compat - completely overwrites system prompt
        3. SystemPromptConfig: Full control over DEFAULT/APPEND/OVERWRITE modes

    Examples:
        # Use default system prompt (simplest)
        AdhocPrompt(prompt="What is 2+2?")

        # Overwrite with string (backward compatible)
        AdhocPrompt(prompt="Say hello", system_prompt="You are a pirate.")

        # Append to default (new feature)
        AdhocPrompt(
            prompt="Analyze this code",
            system_prompt=SystemPromptConfig(
                mode=SystemPromptMode.APPEND,
                system_prompt="Always include performance considerations."
            )
        )

        # Explicit overwrite with config
        AdhocPrompt(
            prompt="Say hello",
            system_prompt=SystemPromptConfig(
                mode=SystemPromptMode.OVERWRITE,
                system_prompt="You are a pirate."
            )
        )
    """

    prompt: str = Field(..., description="The prompt to send to Claude")
    model: ModelName | str = Field(
        default=ModelName.SONNET,
        description="Model to use (defaults to Sonnet)",
    )
    cwd: str | None = Field(
        None,
        description="Working directory for the agent",
    )
    system_prompt: str | SystemPromptConfig | None = Field(
        None,
        description="System prompt config: None=default, str=overwrite, SystemPromptConfig=full control",
    )

    model_config = ConfigDict(use_enum_values=True)


async def quick_prompt(input_data: AdhocPrompt) -> str:
    """Fire a quick, one-off prompt and get back just the result string.

    Uses the SDK's `query()` function which creates a new session each time.
    No session persistence, no hooks, no tools - just simple prompt-in, result-out.

    Features:
    - Uses project scope (loads .claude/settings.json and CLAUDE.md)
    - System prompt modes: DEFAULT (Claude Code's), APPEND, or OVERWRITE
    - Returns just the result string (not messages, usage, etc.)

    Args:
        input_data: AdhocPrompt with prompt, model, cwd, and optional system_prompt

    Returns:
        The result string from Claude's response

    Examples:
        # Use default system prompt
        result = await quick_prompt(AdhocPrompt(
            prompt="What is 2 + 2?",
            model=ModelName.HAIKU,
        ))

        # Append to default system prompt
        result = await quick_prompt(AdhocPrompt(
            prompt="Analyze this code",
            system_prompt=SystemPromptConfig(
                mode=SystemPromptMode.APPEND,
                system_prompt="Always include performance considerations."
            )
        ))

        # Overwrite system prompt completely
        result = await quick_prompt(AdhocPrompt(
            prompt="Say hello",
            system_prompt="You are a pirate."  # Backward compatible string form
        ))
    """
    from claude_agent_sdk import ClaudeAgentOptions, query
    from claude_agent_sdk import ResultMessage as SDKResultMessage

    # Build system prompt config based on input type
    system_prompt_config: dict[str, Any] | str | None

    if input_data.system_prompt is None:
        # Mode 1: DEFAULT - Use Claude Code's default system prompt
        system_prompt_config = {
            "type": "preset",
            "preset": "claude_code",
        }
    elif isinstance(input_data.system_prompt, str):
        # Mode 3: OVERWRITE (backward compatible) - string means complete overwrite
        system_prompt_config = input_data.system_prompt
    elif isinstance(input_data.system_prompt, SystemPromptConfig):
        # Full control via SystemPromptConfig
        system_prompt_config = input_data.system_prompt.to_sdk_config()
    else:
        raise ValueError(f"Unknown system_prompt type: {type(input_data.system_prompt)}")

    # Build options
    options = ClaudeAgentOptions(
        model=input_data.model if isinstance(input_data.model, str) else input_data.model.value,
        cwd=input_data.cwd,
        system_prompt=system_prompt_config,
        setting_sources=["project"],  # Project scope - loads CLAUDE.md
    )

    # Execute query and extract result
    # Note: SDK docs warn against using `break` in the async iterator
    # as it can cause asyncio cleanup issues. Let iteration complete naturally.
    result: str | None = None

    async for message in query(prompt=input_data.prompt, options=options):
        if isinstance(message, SDKResultMessage):
            result = getattr(message, "result", None)
            # Don't break - let iteration complete naturally

    return result or ""


# =============================================================================
# MAIN - CLI FOR DIRECT EXECUTION
# =============================================================================
#
# Tests have been moved to: adws/adw_tests/adw_modules/adw_agent_sdk.py
#
# Run tests with:
#   uv run adws/adw_tests/adw_modules/adw_agent_sdk.py <test-type>
#   uv run adws/adw_tests/adw_modules/adw_agent_sdk.py --list
#


if __name__ == "__main__":
    print("ADW Agent SDK - Core Module")
    print()
    print("This module provides the core SDK wrapper. Tests have been moved to:")
    print("  adws/adw_tests/adw_modules/adw_agent_sdk.py")
    print()
    print("Run tests with:")
    print("  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py <test-type>")
    print("  uv run adws/adw_tests/adw_modules/adw_agent_sdk.py --list")
