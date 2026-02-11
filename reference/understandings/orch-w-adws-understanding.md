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

## Hook → Event → Database → ADW Connection

This section explains how hooks, events, agents, and ADWs are all connected.

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR AGENT                                │
│                     (Claude SDK with hooks attached)                        │
└─────────────────────────────────────────────────────────────────────────────┘
        │                           │                            │
        │ creates via               │ creates via                │ executes
        │ mcp__mgmt__create_agent   │ mcp__mgmt__start_adw       │ directly
        ▼                           ▼                            ▼
┌───────────────────┐    ┌─────────────────────────┐    ┌─────────────────────┐
│    SUB-AGENT      │    │          ADW            │    │   TOOL EXECUTION    │
│  (agents table)   │    │ (ai_developer_workflows)│    │   (Read, Write...)  │
└───────────────────┘    └─────────────────────────┘    └─────────────────────┘
        │                           │                            │
        │ when commanded            │ spawns background          │
        │ gets own SDK client       │ subprocess                 │
        ▼                           ▼                            │
┌───────────────────┐    ┌─────────────────────────┐             │
│  SDK + HOOKS      │    │   STEP AGENTS           │             │
│  (same pattern)   │    │ (plan, build, review)   │             │
└───────────────────┘    │  Each with SDK + hooks  │             │
        │                └─────────────────────────┘             │
        │                           │                            │
        └───────────────────────────┴────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │         HOOKS FIRE            │
                    │  PreToolUse │ PostToolUse     │
                    │  Stop │ Response Blocks       │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────────┐
        │   agent_logs      │           │   WebSocket Broadcast │
        │   (PostgreSQL)    │           │   (real-time to UI)   │
        └───────────────────┘           └───────────────────────┘
```

### Database Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          orchestrator_agents                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ id (UUID) ◄──────────────────────────────────────────────────────┐  │   │
│  │ session_id                                                       │  │   │
│  │ status: active | completed | failed                              │  │   │
│  │ total_cost, total_tokens                                         │  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐
│      agents         │  │ ai_developer_       │  │   orchestrator_chat     │
│                     │  │ workflows (ADWs)    │  │                         │
│ id (UUID) ◄────┐    │  │                     │  │ orchestrator_agent_id   │
│ orchestrator_  │    │  │ id (UUID) ◄────┐    │  │ role: user|orch|agent   │
│ agent_id ──────┘    │  │ orchestrator_  │    │  │ content                 │
│ adw_id ─────────────┼──┤ agent_id ──────┘    │  └─────────────────────────┘
│ name, status        │  │ workflow_type       │
│ session_id          │  │ current_step        │
│ cost, tokens        │  │ status              │
└─────────────────────┘  └─────────────────────┘
          │                         │
          │                         │ (ADW step agents also
          │                         │  create agents records)
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
          ┌─────────────────────────────────────────────────────────────────┐
          │                         agent_logs                              │
          │  ┌───────────────────────────────────────────────────────────┐ │
          │  │ id (UUID)                                                 │ │
          │  │ agent_id ────────────► links to agents.id                 │ │
          │  │ adw_id ──────────────► links to ai_developer_workflows.id │ │
          │  │ adw_step ────────────► "plan" | "build" | "review" | "fix"│ │
          │  │ event_category ──────► "hook" | "response" | "adw_step"   │ │
          │  │ event_type ──────────► PreToolUse, TextBlock, StepStart...│ │
          │  │ content, payload, summary, timestamp                      │ │
          │  └───────────────────────────────────────────────────────────┘ │
          └─────────────────────────────────────────────────────────────────┘
```

### How Hooks Connect Everything

**Step 1: Hook is attached when SDK client is created**

```
SDK Client Created
       │
       ├── PreToolUse hook ──► Called BEFORE any tool executes
       ├── PostToolUse hook ─► Called AFTER tool returns result
       └── Stop hook ────────► Called when agent finishes
```

**Step 2: Hook fires and captures context**

```
Hook fires with context:
  ┌────────────────────────────────────────────┐
  │ agent_id:      Which agent is running      │
  │ adw_id:        Which ADW (if any)          │
  │ adw_step:      Which step (plan/build/...) │
  │ tool_name:     What tool was called        │
  │ tool_input:    Arguments to the tool       │
  │ tool_result:   Output (PostToolUse only)   │
  │ session_id:    SDK session for resumption  │
  └────────────────────────────────────────────┘
```

**Step 3: Event is logged and broadcast**

```
Hook callback executes:
       │
       ├──► write_agent_log(agent_id, adw_id, adw_step, event_type, ...)
       │         │
       │         └──► INSERT INTO agent_logs (...)
       │
       └──► websocket_manager.broadcast(event)
                 │
                 └──► All connected frontends receive real-time update
```

### ADW-Specific Event Flow

When an ADW runs, it creates its own agents for each step:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ADW LIFECYCLE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

1. ORCHESTRATOR CALLS start_adw()
   │
   └──► Creates record in ai_developer_workflows table
        status: "pending", current_step: null
        │
        └──► Spawns background process: uv run adw_plan_build.py --adw-id <id>

2. ADW PROCESS STARTS
   │
   └──► Fetches ADW config from database (prompt, working_dir, model)
        │
        └──► Updates status: "in_progress"

3. PLAN STEP EXECUTES
   │
   ├──► Creates agent record (name: "plan-agent", adw_id: <id>)
   │
   ├──► SDK client with hooks attached
   │         │
   │         ├── PreToolUse  ─► agent_logs (adw_step: "plan")
   │         ├── PostToolUse ─► agent_logs (adw_step: "plan")
   │         └── Response handlers ─► agent_logs (adw_step: "plan")
   │
   └──► Updates: current_step: "plan", completed_steps: 1

4. BUILD STEP EXECUTES
   │
   ├──► Creates agent record (name: "build-agent", adw_id: <id>)
   │
   ├──► SDK client with hooks attached
   │         │
   │         ├── PreToolUse  ─► agent_logs (adw_step: "build")
   │         ├── PostToolUse ─► agent_logs (adw_step: "build")
   │         └── Response handlers ─► agent_logs (adw_step: "build")
   │
   └──► Updates: current_step: "build", completed_steps: 2

5. ADW COMPLETES
   │
   └──► Updates: status: "completed", completed_at: now()
```

### WebSocket Event Types

The system broadcasts different event types for different purposes:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          WEBSOCKET EVENT TYPES                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ORCHESTRATOR EVENTS (from orchestrator_service.py)                        │
│  ├── orchestrator_response_start   → Agent began responding                │
│  ├── orchestrator_response_chunk   → Streaming text chunk                  │
│  ├── orchestrator_response_end     → Agent finished responding             │
│  ├── orchestrator_tool_use         → Tool was called                       │
│  └── orchestrator_error            → Error occurred                        │
│                                                                            │
│  AGENT EVENTS (from agent_manager.py)                                      │
│  ├── agent_created                 → New sub-agent created                 │
│  ├── agent_commanded               → Sub-agent received command            │
│  ├── agent_response                → Sub-agent response chunk              │
│  └── agent_completed               → Sub-agent finished task               │
│                                                                            │
│  ADW EVENTS (from adw_websockets.py)                                       │
│  ├── adw_created                   → New ADW started                       │
│  ├── adw_status                    → Status changed (pending→in_progress)  │
│  ├── adw_step_change               → Step changed (plan→build→review)      │
│  ├── adw_event                     → Hook/response event from ADW agent    │
│  └── adw_event_summary_update      → AI-generated summary ready            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Querying Events for a Specific ADW

To see all events for an ADW, you query `agent_logs` with the `adw_id`:

```sql
-- Get all events for an ADW, grouped by step
SELECT
    adw_step,
    event_category,
    event_type,
    summary,
    timestamp
FROM agent_logs
WHERE adw_id = '<adw-uuid>'
ORDER BY timestamp;

-- Result shows the swimlane timeline:
-- ┌──────────┬──────────┬─────────────┬────────────────────────┐
-- │ adw_step │ category │ event_type  │ summary                │
-- ├──────────┼──────────┼─────────────┼────────────────────────┤
-- │ plan     │ adw_step │ StepStart   │ Starting plan step     │
-- │ plan     │ hook     │ PreToolUse  │ Reading project files  │
-- │ plan     │ hook     │ PostToolUse │ Read 5 files           │
-- │ plan     │ response │ TextBlock   │ I'll create a plan...  │
-- │ plan     │ adw_step │ StepEnd     │ Plan step completed    │
-- │ build    │ adw_step │ StepStart   │ Starting build step    │
-- │ build    │ hook     │ PreToolUse  │ Writing auth.py        │
-- │ ...      │ ...      │ ...         │ ...                    │
-- └──────────┴──────────┴─────────────┴────────────────────────┘
```

### The Connection Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOW IT ALL CONNECTS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. HOOKS are callback functions attached to SDK clients                    │
│     └── They intercept tool calls and agent responses                       │
│                                                                             │
│  2. HOOKS write to agent_logs table with foreign keys:                      │
│     └── agent_id  → which agent generated the event                         │
│     └── adw_id    → which ADW this belongs to (nullable for non-ADW)        │
│     └── adw_step  → which step within the ADW (plan/build/review/fix)       │
│                                                                             │
│  3. AGENTS table tracks all agents:                                         │
│     └── orchestrator_agent_id → parent orchestrator                         │
│     └── adw_id → if created as part of an ADW workflow                      │
│                                                                             │
│  4. ADWs table tracks workflow state:                                       │
│     └── orchestrator_agent_id → which orchestrator started it               │
│     └── current_step, status → progress tracking                            │
│                                                                             │
│  5. WEBSOCKET broadcasts all events in real-time:                           │
│     └── Frontend receives and updates UI immediately                        │
│     └── Enables swimlane visualization of parallel work                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

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

## How Sub-Agents Get Spawned (The Full Flow)

This section explains exactly how the orchestrator creates and commands sub-agents via MCP tools.

### MCP Tool Registration

When the orchestrator starts, it registers management tools as an MCP server:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR STARTUP                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AgentManager.create_management_tools()                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Returns list of @tool decorated functions:                             │ │
│  │   - create_agent_tool                                                  │ │
│  │   - list_agents_tool                                                   │ │
│  │   - command_agent_tool                                                 │ │
│  │   - check_agent_status_tool                                            │ │
│  │   - delete_agent_tool                                                  │ │
│  │   - interrupt_agent_tool                                               │ │
│  │   - start_adw_tool                                                     │ │
│  │   - check_adw_tool                                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OrchestratorService._build_sdk_options()                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ mcp_server = create_sdk_mcp_server(                                    │ │
│  │     name="mgmt",                                                       │ │
│  │     version="1.0.0",                                                   │ │
│  │     tools=self.management_tools   ◄── The @tool functions             │ │
│  │ )                                                                      │ │
│  │                                                                        │ │
│  │ options_dict["mcp_servers"] = {"mgmt": mcp_server}                     │ │
│  │ options_dict["allowed_tools"] = ["mcp__mgmt__create_agent", ...]       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ClaudeSDKClient created with these options                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Claude can now call tools like:                                        │ │
│  │   - mcp__mgmt__create_agent                                            │ │
│  │   - mcp__mgmt__command_agent                                           │ │
│  │   - mcp__mgmt__start_adw                                               │ │
│  │   etc.                                                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Creating a Sub-Agent

When the orchestrator decides to create a sub-agent:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Claude SDK) - processing user request                       │
│                                                                             │
│  "I need to create a specialized agent for this database work..."           │
│                                                                             │
│  Claude decides to call:                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ToolUseBlock(                                                         │ │
│  │      tool_name="mcp__mgmt__create_agent",                              │ │
│  │      input={                                                           │ │
│  │          "name": "db-migration-agent",                                 │ │
│  │          "system_prompt": "You are a database expert...",              │ │
│  │          "model": "sonnet"                                             │ │
│  │      }                                                                 │ │
│  │  )                                                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MCP Server routes to: create_agent_tool(args)                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Validate args (name required)                                      │ │
│  │  2. Resolve model alias ("sonnet" → "claude-sonnet-4-5-20250929")      │ │
│  │  3. Call database: create_agent(                                       │ │
│  │         orchestrator_agent_id=...,                                     │ │
│  │         name="db-migration-agent",                                     │ │
│  │         system_prompt="You are a database expert...",                  │ │
│  │         model="claude-sonnet-4-5-20250929",                            │ │
│  │         status="idle"                                                  │ │
│  │     )                                                                  │ │
│  │  4. Returns: {"content": [{"type": "text", "text": "✅ Created..."}]}  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATABASE: agents table                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  INSERT INTO agents (                                                  │ │
│  │      id, orchestrator_agent_id, name, system_prompt, model, status     │ │
│  │  ) VALUES (                                                            │ │
│  │      'uuid-123', 'orch-uuid', 'db-migration-agent', '...', '...', 'idle'│
│  │  )                                                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Commanding a Sub-Agent (Spawning the SDK Client)

When the orchestrator commands the agent:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR calls:                                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ToolUseBlock(                                                         │ │
│  │      tool_name="mcp__mgmt__command_agent",                             │ │
│  │      input={                                                           │ │
│  │          "agent_name": "db-migration-agent",                           │ │
│  │          "command": "Create a migration for adding user roles table"   │ │
│  │      }                                                                 │ │
│  │  )                                                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  command_agent_tool(args) in AgentManager                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Look up agent by name in database                                  │ │
│  │  2. IMPORTANT: Spawn in background thread!                             │ │
│  │     asyncio.create_task(self.command_agent(agent.id, command))         │ │
│  │  3. Return immediately: "✅ Command dispatched to 'db-migration-agent'"│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Background Task)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AgentManager.command_agent(agent_id, command)                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Get agent from database                                            │ │
│  │  2. Generate task_slug for tracking                                    │ │
│  │  3. Insert prompt to database                                          │ │
│  │  4. Build hooks for this agent                                         │ │
│  │  5. Update status: "idle" → "executing"                                │ │
│  │  6. CREATE NEW SDK CLIENT:                                             │ │
│  │                                                                        │ │
│  │     options = ClaudeAgentOptions(                                      │ │
│  │         system_prompt=agent.system_prompt,                             │ │
│  │         model=agent.model,                                             │ │
│  │         cwd=agent.working_dir,                                         │ │
│  │         resume=agent.session_id,   ◄── Resume previous context!        │ │
│  │         hooks=hooks_dict,          ◄── Hooks for event capture         │ │
│  │         allowed_tools=[...],                                           │ │
│  │         permission_mode="acceptEdits"                                  │ │
│  │     )                                                                  │ │
│  │                                                                        │ │
│  │     async with ClaudeSDKClient(options=options) as client:             │ │
│  │         await client.query(command)   ◄── Send the command             │ │
│  │         # Process response messages...                                 │ │
│  │                                                                        │ │
│  │  7. Update status: "executing" → "idle"                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (While executing, hooks fire)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  HOOKS CAPTURE EVENTS → agent_logs → WebSocket → Frontend                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: Background Execution

The critical pattern is that `command_agent_tool` **dispatches in background** and returns immediately:

```python
# In command_agent_tool:
asyncio.create_task(self.command_agent(agent.id, command))  # Fire and forget
return {"content": [{"text": "✅ Command dispatched..."}]}  # Return NOW
```

This means:
1. **Orchestrator doesn't block** - it can continue working while sub-agent runs
2. **Multiple agents can run concurrently** - each in its own background task
3. **Status is tracked via database** - check with `check_agent_status` tool
4. **Events stream via WebSocket** - UI sees real-time updates

### ADW vs Sub-Agent: The Difference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUB-AGENT (via command_agent)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  - Runs in SAME PROCESS as orchestrator (asyncio background task)           │
│  - Single SDK client per command                                            │
│  - Good for one-off tasks                                                   │
│  - Can be resumed (session_id preserved)                                    │
│  - Orchestrator can interrupt it                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADW (via start_adw)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  - Runs in SEPARATE PROCESS (subprocess.Popen with start_new_session=True)  │
│  - Multiple SDK clients (one per step: plan, build, review, fix)            │
│  - Good for multi-step autonomous workflows                                 │
│  - Completely detached - survives if orchestrator dies                      │
│  - Has structured step progression and status tracking                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Flow Example

```
User: "Add a new user roles feature to the database"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR thinks...                                                     │
│  "This is a multi-step task. I'll use an ADW workflow."                     │
│                                                                             │
│  Calls: mcp__mgmt__start_adw({                                              │
│      name_of_adw: "user-roles-feature",                                     │
│      workflow_type: "plan_build_review",                                    │
│      prompt: "Add user roles table and migration...",                       │
│      description: "Implements RBAC database schema"                         │
│  })                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  start_adw_tool executes:                                                   │
│  1. Create ADW record in ai_developer_workflows table                       │
│  2. Spawn: subprocess.Popen(["uv", "run", "adw_plan_build_review.py", ...]) │
│  3. Return: "✅ ADW 'user-roles-feature' started"                           │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKGROUND PROCESS (adw_plan_build_review.py)                              │
│                                                                             │
│  Step 1: PLAN                                                               │
│  ├── Creates agent record (name: "plan-agent", adw_id: ...)                 │
│  ├── SDK client executes /plan prompt                                       │
│  ├── Hooks → agent_logs (adw_step: "plan")                                  │
│  └── WebSocket broadcasts events                                            │
│                                                                             │
│  Step 2: BUILD                                                              │
│  ├── Creates agent record (name: "build-agent", adw_id: ...)                │
│  ├── SDK client executes /build with plan file                              │
│  ├── Hooks → agent_logs (adw_step: "build")                                 │
│  └── WebSocket broadcasts events                                            │
│                                                                             │
│  Step 3: REVIEW                                                             │
│  ├── Creates agent record (name: "review-agent", adw_id: ...)               │
│  ├── SDK client executes /review                                            │
│  ├── Hooks → agent_logs (adw_step: "review")                                │
│  └── WebSocket broadcasts events                                            │
│                                                                             │
│  ADW completes: status → "completed"                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

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
