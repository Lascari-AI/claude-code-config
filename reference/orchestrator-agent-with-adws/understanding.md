# Understanding the Multi-Agent Orchestration System

This document explains the core data flow and execution architecture of this system.

---

## How Work Actually Gets Done

### The Claude Agent SDK (Not CLI Subprocess)

The system uses the **Claude Agent SDK Python library** directly - NOT subprocess invocation of the Claude CLI. All execution happens via SDK imports and client instantiation:

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)
```

**Key insight:** When you interact with this system, it's making direct API calls to Claude through the SDK, not spawning `claude` CLI processes.

### Execution Flow: User Message → Claude Response

```
User sends message (WebSocket or HTTP)
    ↓
FastAPI backend receives it
    ↓
OrchestratorService.process_user_message()
    ↓
Log user message to PostgreSQL database
    ↓
Create ClaudeSDKClient with options:
  - System prompt (with injected subagent/workflow info)
  - Model selection (defaults to Opus 4.5)
  - Working directory
  - Hooks for event capture
  - MCP tools for agent management
    ↓
client.query(user_message)  ← Sends to Claude API
    ↓
async for message in client.receive_response():
  - TextBlock → Stream to WebSocket
  - ToolUseBlock → Log tool call
  - ThinkingBlock → Process reasoning
    ↓
Log orchestrator response to database
    ↓
Update costs/tokens in database
```

### The SDK Client Pattern

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query(user_message)  # Send prompt

    async for message in client.receive_response():  # Stream response
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Handle text output
                elif isinstance(block, ToolUseBlock):
                    # Handle tool execution
```

**Location:** `apps/orchestrator_3_stream/backend/modules/orchestrator_service.py` (lines 582-852)

---

## Data Flow Architecture

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3 + Pinia)                     │
│  - HTTP: /send_chat, /load_chat, /get_events                        │
│  - WebSocket: /ws (real-time streaming)                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI + asyncpg)                     │
│  - OrchestratorService (Claude SDK execution)                       │
│  - AgentManager (sub-agent lifecycle)                               │
│  - WebSocketManager (broadcast events)                              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL (NeonDB)                            │
│  - orchestrator_agents, agents, agent_logs                          │
│  - orchestrator_chat, ai_developer_workflows                        │
└─────────────────────────────────────────────────────────────────────┘
```

### What Gets Stored Where

| Table | Purpose |
|-------|---------|
| `orchestrator_agents` | The main orchestrator session - session_id, costs, tokens, metadata |
| `agents` | Sub-agents created by orchestrator |
| `agent_logs` | Every hook event (PreToolUse, PostToolUse, Stop) and response block |
| `orchestrator_chat` | 3-way chat log: user ↔ orchestrator ↔ agents |
| `ai_developer_workflows` | Multi-step workflow tracking (plan → build → review) |

### Real-Time Event Flow

1. **Claude SDK executes** with hooks attached
2. **Hooks fire** (PreToolUse, PostToolUse, Stop)
3. **Events logged** to `agent_logs` table
4. **WebSocket broadcasts** event to all connected clients
5. **Frontend store updates** reactively
6. **UI re-renders** with new data

---

## Three Types of Execution

### 1. Orchestrator Agent

The main agent that manages everything. Uses Claude SDK directly:

- Creates SDK client with system prompt + MCP management tools
- Streams responses to WebSocket
- Can create/command sub-agents via MCP tools

**Location:** `apps/orchestrator_3_stream/backend/modules/orchestrator_service.py`

### 2. Sub-Agents

Created by the orchestrator via `mcp__mgmt__create_agent` tool:

- Each sub-agent gets its own database record
- When commanded, a new SDK client is created for that task
- Session ID stored for resumption

**Location:** `apps/orchestrator_3_stream/backend/modules/agent_manager.py`

### 3. AI Developer Workflows (ADWs)

The **ONLY place subprocess spawning occurs**:

```python
cmd = ["uv", "run", str(workflow_path), "--adw-id", adw_id]
process = subprocess.Popen(cmd, start_new_session=True)  # Detached
```

ADWs spawn background processes that then use the SDK internally. This allows multi-step workflows (plan → build → review) to run independently.

**Locations:**
- Trigger: `adws/adw_triggers/adw_scripts.py`
- Workflows: `adws/adw_workflows/adw_plan_build.py`
- SDK wrapper: `adws/adw_modules/adw_agent_sdk.py`

---

## Session Management

### How Sessions Work

1. **New session**: `orchestrator_agents.session_id` starts as NULL
2. **First interaction**: Claude SDK generates session_id, we store it
3. **Resume session**: CLI `--session <id>` loads existing orchestrator
4. **Singleton pattern**: Only 1 active orchestrator (`archived=false`)

### Session Resumption Flow

```
CLI: python main.py --session abc123
    ↓
Query: SELECT * FROM orchestrator_agents WHERE session_id = 'abc123'
    ↓
Load existing state (costs, tokens, metadata)
    ↓
Initialize SDK with same session_id
    ↓
Next interaction continues conversation context
```

---

## Hook System

Hooks capture Claude's internal events during execution:

| Hook | When | Purpose |
|------|------|---------|
| `PreToolUse` | Before tool called | Log intent, validate |
| `PostToolUse` | After tool returns | Log result |
| `Stop` | Agent completes | Cleanup, final logging |

Hooks are attached to the SDK client:

```python
options_dict["hooks"] = {
    "PreToolUse": [{"hooks": [create_orchestrator_pre_tool_hook(...)]}],
    "PostToolUse": [{"hooks": [create_orchestrator_post_tool_hook(...)]}],
    "Stop": [{"hooks": [create_orchestrator_stop_hook(...)]}],
}
```

Each hook event:
1. Gets logged to `agent_logs` table
2. Gets broadcast via WebSocket
3. Shows up in the UI event stream

---

## Management Tools (MCP)

The orchestrator's management tools are registered as MCP tools:

```python
mcp_server = create_sdk_mcp_server(
    name="mgmt", version="1.0.0", tools=self.management_tools
)

options_dict["allowed_tools"] = [
    "mcp__mgmt__create_agent",
    "mcp__mgmt__list_agents",
    "mcp__mgmt__command_agent",
    "mcp__mgmt__start_adw",
    # ... more
]
```

This allows Claude to manage agents and workflows through natural tool calls.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `apps/orchestrator_3_stream/backend/main.py` | FastAPI entry, WebSocket handling, session args |
| `apps/orchestrator_3_stream/backend/modules/orchestrator_service.py` | Claude SDK execution, hooks, streaming |
| `apps/orchestrator_3_stream/backend/modules/agent_manager.py` | Sub-agent CRUD and command execution |
| `apps/orchestrator_3_stream/backend/modules/database.py` | All PostgreSQL operations (~1930 lines) |
| `apps/orchestrator_3_stream/backend/modules/websocket_manager.py` | WebSocket broadcast management |
| `apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts` | Pinia state management |
| `apps/orchestrator_db/migrations/` | SQL schema definitions |
| `adws/adw_modules/adw_agent_sdk.py` | SDK wrapper for ADW workflows |
| `adws/adw_workflows/adw_plan_build.py` | Example multi-step workflow |

---

## Summary

| Question | Answer |
|----------|--------|
| How does Claude run? | **Claude Agent SDK** - direct Python library, not CLI subprocess |
| Where is data stored? | **PostgreSQL** (NeonDB) - not filesystem |
| How do events stream? | **WebSocket** broadcasts from backend to frontend |
| How are sub-agents managed? | **MCP tools** registered with the SDK |
| When are subprocesses used? | **Only for ADW workflows** - background detached processes |
| How are sessions tracked? | **session_id** in database, generated by SDK on first interaction |
