# Orchestrator 3 Stream - Full-Stack Architecture Summary

**Date:** 2025-01-22
**Version:** 1.0
**Purpose:** Comprehensive architectural overview of the multi-agent orchestration system

---

## Key System Nodes - Quick Reference

**Backend Layer:**
- **FastAPI Backend (main.py)**: HTTP/WebSocket server that routes requests to services, manages lifespan, and handles session resumption via CLI flags.
- **WebSocket Manager**: Centralized broadcast hub that pushes real-time events (agent logs, chat, status changes) to all connected frontend clients.
- **Orchestrator Service**: Executes the orchestrator agent with Claude SDK, streams responses via WebSocket, and manages three-phase logging (pre/exec/post).
- **Agent Manager**: Provides 8 management tools (create/command/delete agents) as MCP server, manages agent lifecycle, and captures hook events.
- **Database Module**: asyncpg connection pool that handles all PostgreSQL operations (agents, logs, chat, costs) with Pydantic model parsing.
- **Logger**: Hourly rotating file logs + Rich console output for all backend operations.

**Frontend Layer:**
- **Vue3 Frontend (App.vue)**: 3-column responsive layout (agents sidebar, event stream, chat) with keyboard shortcuts and real-time updates.
- **Pinia Store (orchestratorStore.ts)**: Centralized state management for agents, events, chat messages, WebSocket connection, and cost tracking.
- **Chat Service**: Handles HTTP requests (load history, send messages) and WebSocket connection with typed callbacks for event routing.
- **API Client (Axios)**: Configured HTTP client with base URL, timeout, and error interceptors for all REST API calls.

**Data Layer:**
- **PostgreSQL Database**: Persistent storage for orchestrator state, agents, event logs, chat history, and cost tracking with JSONB metadata fields.

**AI Layer:**
- **Orchestrator Agent**: Primary Claude Sonnet 4.5 agent with management tools that creates/commands subordinate agents via MCP server.
- **Command Agents**: Subordinate Claude agents (Sonnet/Haiku) created and managed by orchestrator to execute specific tasks with hook-based event capture.
- **Management Tools (MCP)**: 8-tool MCP server exposing agent management operations (create_agent, command_agent, etc.) to orchestrator.

---

## Executive Summary

Orchestrator 3 Stream is a **full-stack multi-agent orchestration platform** that enables real-time command and control of multiple Claude SDK agents through a web-based interface. The system uses:

- **Backend**: Python FastAPI with asyncpg (PostgreSQL), Claude Agent SDK
- **Frontend**: Vue 3 + TypeScript + Pinia with real-time WebSocket streaming
- **Database**: PostgreSQL (NeonDB) for persistent agent state and event logging
- **Communication**: REST API for commands, WebSocket for live event streaming

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer (Vue 3 + TypeScript)"
        UI[User Interface<br/>3-Column Layout]
        Store[Pinia Store<br/>orchestratorStore.ts]
        Services[Services Layer]
        WS_Client[WebSocket Client]
        HTTP_Client[Axios HTTP Client]
    end

    subgraph "Backend Layer (FastAPI + Python)"
        API[FastAPI Endpoints<br/>main.py]
        WSManager[WebSocket Manager<br/>Broadcast Hub]
        OrchService[Orchestrator Service<br/>Claude SDK Client]
        AgentMgr[Agent Manager<br/>8 Management Tools]
        Database[Database Module<br/>asyncpg Pool]
    end

    subgraph "Data Layer (PostgreSQL)"
        DB[(NeonDB PostgreSQL)]
        Tables[orchestrator_agents<br/>agents<br/>agent_logs<br/>orchestrator_chat<br/>system_logs]
    end

    subgraph "AI Layer (Claude SDK)"
        Orchestrator[Orchestrator Agent<br/>Claude Sonnet 4.5]
        CommandAgents[Command Agents<br/>Sonnet/Haiku]
        Tools[Management Tools<br/>MCP Server]
    end

    UI --> Store
    Store --> Services
    Services --> HTTP_Client
    Services --> WS_Client

    HTTP_Client -->|REST API| API
    WS_Client -->|WebSocket /ws| API

    API --> WSManager
    API --> OrchService
    API --> AgentMgr
    API --> Database

    WSManager -->|Broadcast Events| WS_Client

    OrchService --> Orchestrator
    OrchService --> Database
    OrchService --> WSManager

    AgentMgr --> CommandAgents
    AgentMgr --> Database
    AgentMgr --> WSManager

    Orchestrator --> Tools
    Tools --> AgentMgr

    Database --> DB
    DB --> Tables

    style UI fill:#c084fc,stroke:#a855f7,color:#000
    style Store fill:#38bdf8,stroke:#0ea5e9,color:#000
    style API fill:#fb923c,stroke:#f97316,color:#000
    style WSManager fill:#4ade80,stroke:#22c55e,color:#000
    style DB fill:#fbbf24,stroke:#f59e0b,color:#000
    style Orchestrator fill:#f472b6,stroke:#ec4899,color:#000
```

---

## Data Flow & Communication Patterns

### 1. User Sends Chat Message

```mermaid
sequenceDiagram
    participant User
    participant UI as Vue UI
    participant Store as Pinia Store
    participant HTTP as HTTP Service
    participant API as FastAPI
    participant OrchSvc as Orchestrator Service
    participant SDK as Claude SDK
    participant DB as PostgreSQL
    participant WS as WebSocket Manager

    User->>UI: Types message & clicks send
    UI->>Store: sendUserMessage(message)
    Store->>Store: Add user message to UI immediately
    Store->>HTTP: POST /send_chat
    HTTP->>API: HTTP Request
    API->>OrchSvc: process_user_message()

    OrchSvc->>DB: insert_chat_message (user → orch)
    OrchSvc->>WS: broadcast orchestrator_chat event
    WS-->>Store: WebSocket message received
    Store->>UI: Update event stream

    OrchSvc->>SDK: query(user_message)

    loop Streaming Response
        SDK-->>OrchSvc: TextBlock
        OrchSvc->>DB: insert_chat_message (orch → user)
        OrchSvc->>WS: broadcast orchestrator_chat event
        WS-->>Store: WebSocket stream
        Store->>UI: Append to chat UI

        SDK-->>OrchSvc: ThinkingBlock
        OrchSvc->>DB: insert_system_log
        OrchSvc->>WS: broadcast thinking_block event
        WS-->>Store: WebSocket stream
        Store->>UI: Show thinking in chat

        SDK-->>OrchSvc: ToolUseBlock
        OrchSvc->>DB: insert_system_log
        OrchSvc->>WS: broadcast tool_use_block event
        WS-->>Store: WebSocket stream
        Store->>UI: Show tool use in chat
    end

    SDK-->>OrchSvc: ResultMessage (costs, tokens)
    OrchSvc->>DB: update_orchestrator_costs()
    OrchSvc->>WS: broadcast orchestrator_updated
    WS-->>Store: Cost update received
    Store->>UI: Update header stats
```

### 2. Orchestrator Creates Command Agent

```mermaid
sequenceDiagram
    participant Orch as Orchestrator Agent
    participant Tools as Management Tools (MCP)
    participant AgentMgr as Agent Manager
    participant SDK as Claude SDK
    participant DB as PostgreSQL
    participant WS as WebSocket Manager
    participant UI as Frontend

    Orch->>Tools: create_agent(name, prompt, model)
    Tools->>AgentMgr: create_agent()
    AgentMgr->>DB: create_agent in agents table
    DB-->>AgentMgr: agent_id

    AgentMgr->>SDK: Create ClaudeSDKClient with hooks
    SDK->>SDK: Initialize agent session
    SDK-->>AgentMgr: session_id

    AgentMgr->>DB: update_agent_session()
    AgentMgr->>WS: broadcast_agent_created()
    WS-->>UI: agent_created WebSocket event
    UI->>UI: Add agent to sidebar

    AgentMgr-->>Tools: {"ok": true, "agent_id": "...", "session_id": "..."}
    Tools-->>Orch: Agent created successfully
```

### 3. Orchestrator Commands Agent to Execute Task

```mermaid
sequenceDiagram
    participant Orch as Orchestrator Agent
    participant Tools as Management Tools
    participant AgentMgr as Agent Manager
    participant Agent as Command Agent (SDK)
    participant DB as PostgreSQL
    participant WS as WebSocket Manager
    participant UI as Frontend

    Orch->>Tools: command_agent(name, command)
    Tools->>AgentMgr: command_agent()
    AgentMgr->>DB: insert_prompt (orchestrator → agent)
    AgentMgr->>DB: update_agent_status('executing')
    AgentMgr->>WS: broadcast agent_status_changed
    WS-->>UI: Status update in sidebar

    AgentMgr->>Agent: Resume session + query(command)

    loop Agent Execution with Hooks
        Agent-->>AgentMgr: PreToolUse hook
        AgentMgr->>DB: insert_hook_event
        AgentMgr->>WS: broadcast agent_log (hook)
        WS-->>UI: Event stream update

        Agent-->>AgentMgr: TextBlock response
        AgentMgr->>DB: insert_message_block
        AgentMgr->>WS: broadcast agent_log (response)
        WS-->>UI: Event stream update

        Agent-->>AgentMgr: ToolUseBlock
        AgentMgr->>DB: insert_message_block
        AgentMgr->>WS: broadcast agent_log (tool_use)
        WS-->>UI: Event stream update + pulse animation

        Agent-->>AgentMgr: PostToolUse hook
        AgentMgr->>DB: insert_hook_event + file tracking
        AgentMgr->>WS: broadcast agent_log (hook)
        WS-->>UI: Event stream update
    end

    Agent-->>AgentMgr: ResultMessage (costs, tokens)
    AgentMgr->>DB: update_agent_costs()
    AgentMgr->>DB: update_agent_status('idle')
    AgentMgr->>WS: broadcast agent_updated (tokens/cost)
    AgentMgr->>WS: broadcast agent_status_changed
    WS-->>UI: Sidebar shows updated cost + status
```

---

## Component Responsibilities

### Backend Components

| Component                | File                      | Responsibilities                                                                                                                                                                                                        |
| ------------------------ | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FastAPI Main**         | `main.py`                 | - HTTP endpoints<br/>- WebSocket endpoint `/ws`<br/>- CORS configuration<br/>- Lifespan management (startup/shutdown)<br/>- Session resumption via `--session` CLI                                                      |
| **Configuration**        | `config.py`               | - Environment variable loading<br/>- Port configuration (BE:9403, FE:5175)<br/>- Database URL management<br/>- Working directory override support                                                                       |
| **WebSocket Manager**    | `websocket_manager.py`    | - Manage active WebSocket connections<br/>- Broadcast events to all clients<br/>- Event types: agent_log, orchestrator_chat, thinking_block, tool_use_block, agent_created/updated/deleted                              |
| **Orchestrator Service** | `orchestrator_service.py` | - Execute orchestrator agent with Claude SDK<br/>- Stream responses via WebSocket<br/>- Three-phase logging (pre, execution, post)<br/>- Cost tracking and session management<br/>- SystemMessage metadata capture      |
| **Agent Manager**        | `agent_manager.py`        | - 8 management tools for orchestrator<br/>- Create/list/command/delete agents<br/>- Hook registration for agent events<br/>- Background agent execution<br/>- File tracking integration<br/>- Subagent template loading |
| **Database Module**      | `database.py`             | - asyncpg connection pool<br/>- Orchestrator CRUD operations<br/>- Agent CRUD operations<br/>- Chat message logging<br/>- Event logging (agent_logs, system_logs)<br/>- Query methods for frontend                      |
| **Logger**               | `logger.py`               | - Hourly rotating file logs<br/>- Rich console output<br/>- Structured logging for all events                                                                                                                           |

### Frontend Components

| Component                | File                     | Responsibilities                                                                                                                                                        |
| ------------------------ | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Main App**             | `App.vue`                | - 3-column layout (agents, stream, chat)<br/>- Responsive grid system<br/>- Keyboard shortcuts (Cmd+K)<br/>- Component orchestration                                    |
| **Pinia Store**          | `orchestratorStore.ts`   | - Centralized state management<br/>- WebSocket connection lifecycle<br/>- Event stream state<br/>- Chat messages state<br/>- Agent list state<br/>- Cost/token tracking |
| **Chat Service**         | `chatService.ts`         | - HTTP: loadChatHistory(), sendMessage()<br/>- WebSocket: connectWebSocket() with callbacks<br/>- Message type routing<br/>- Typing indicator management                |
| **API Client**           | `api.ts`                 | - Axios instance with base URL<br/>- Error interceptors<br/>- Timeout configuration                                                                                     |
| **Agent List**           | `AgentList.vue`          | - Display active agents<br/>- Status indicators (idle, executing, blocked)<br/>- Pulsing animations on activity<br/>- Agent selection                                   |
| **Event Stream**         | `EventStream.vue`        | - Combined event feed<br/>- Filtering (Combined, Errors, Performance)<br/>- Auto-scroll toggle<br/>- Agent name filtering                                               |
| **Orchestrator Chat**    | `OrchestratorChat.vue`   | - Chat interface<br/>- Message rendering (text, thinking, tool_use)<br/>- Typing indicator<br/>- Send message input                                                     |
| **Global Command Input** | `GlobalCommandInput.vue` | - Cmd+K overlay<br/>- System info display<br/>- Slash commands as badges<br/>- Agent templates as badges                                                                |

---

## Database Schema

### Core Tables

```mermaid
erDiagram
    orchestrator_agents ||--o{ agents : owns
    orchestrator_agents ||--o{ orchestrator_chat : "has messages"
    agents ||--o{ agent_logs : "generates logs"
    agents ||--o{ prompts : "receives prompts"

    orchestrator_agents {
        uuid id PK
        varchar session_id UK
        text system_prompt
        varchar status
        varchar working_dir
        int input_tokens
        int output_tokens
        decimal total_cost
        boolean archived
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    agents {
        uuid id PK
        uuid orchestrator_agent_id FK
        varchar name
        varchar model
        text system_prompt
        varchar working_dir
        varchar status
        varchar session_id UK
        int input_tokens
        int output_tokens
        decimal total_cost
        boolean archived
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    agent_logs {
        uuid id PK
        uuid agent_id FK
        varchar session_id
        varchar task_slug
        int entry_index
        varchar event_category
        varchar event_type
        text content
        text summary
        jsonb payload
        timestamp timestamp
    }

    orchestrator_chat {
        uuid id PK
        uuid orchestrator_agent_id FK
        varchar sender_type
        varchar receiver_type
        text message
        uuid agent_id FK
        jsonb metadata
        timestamp created_at
    }

    system_logs {
        uuid id PK
        varchar level
        text message
        text summary
        jsonb metadata
        timestamp timestamp
    }

    prompts {
        uuid id PK
        uuid agent_id FK
        varchar task_slug
        varchar author
        text prompt_text
        text summary
        timestamp timestamp
    }
```

---

## Key Integration Points

### 1. Frontend ↔ Backend Communication

**REST API Endpoints:**
- `GET /health` - Health check
- `GET /get_orchestrator` - Fetch orchestrator info + slash commands + templates
- `POST /load_chat` - Load chat history
- `POST /send_chat` - Send user message (async, returns immediately)
- `GET /get_events` - Fetch event history (agent_logs, orchestrator_chat, system_logs)
- `GET /list_agents` - List all agents with log counts
- `POST /api/open-file` - Open file in IDE (Cursor/VS Code)

**WebSocket Events (Backend → Frontend):**
- `agent_log` - Agent event (hook, response, tool use)
- `orchestrator_chat` - Chat message (user ↔ orchestrator)
- `thinking_block` - Orchestrator thinking
- `tool_use_block` - Orchestrator tool use
- `agent_created` - New agent created
- `agent_updated` - Agent costs/tokens updated
- `agent_deleted` - Agent removed
- `agent_status_changed` - Status change (idle ↔ executing)
- `agent_summary_update` - Latest AI summary for agent
- `orchestrator_updated` - Orchestrator costs updated
- `chat_typing` - Typing indicator
- `error` - Error notification

### 2. Orchestrator ↔ Command Agents

**Management Tools (via MCP Server):**
```typescript
// 8 management tools registered as MCP server tools
mcp__mgmt__create_agent(name, system_prompt?, model?, subagent_template?)
mcp__mgmt__list_agents()
mcp__mgmt__command_agent(agent_name, command)
mcp__mgmt__check_agent_status(agent_name, tail_count?, verbose_logs?)
mcp__mgmt__delete_agent(agent_name)
mcp__mgmt__interrupt_agent(agent_name)
mcp__mgmt__read_system_logs(offset?, limit?, message_contains?, level?)
mcp__mgmt__report_cost()
```

**Subagent Template System:**
- Templates stored in `.claude/agents/*.md`
- YAML frontmatter with name, description, tools, model, color
- Dynamic injection into orchestrator system prompt via `{{SUBAGENT_MAP}}`
- Template-based agent creation with pre-configured tools

### 3. Claude SDK ↔ Database

**Hook Events Captured:**
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution + file tracking
- `UserPromptSubmit` - Prompt received
- `Stop` - Agent stopped
- `SubagentStop` - Subagent stopped
- `PreCompact` - Before context compaction

**Message Blocks Captured:**
- `TextBlock` - Agent text responses
- `ThinkingBlock` - Agent reasoning
- `ToolUseBlock` - Tool invocation
- `ResultMessage` - Final costs and session ID

---

## Data Flow Summary

### User Interaction Flow
1. **User sends message** → Frontend pre-adds to UI → POST /send_chat → Backend queues
2. **Backend processes** → Orchestrator agent executes → WebSocket streams events
3. **Frontend receives** → Updates event stream + chat UI in real-time
4. **Database persists** → All events logged for replay/history

### Agent Creation Flow
1. **Orchestrator uses create_agent tool** → Agent Manager creates in DB
2. **Claude SDK initializes** → Agent gets session ID
3. **WebSocket broadcasts** → Frontend adds agent to sidebar
4. **Agent ready** → Can receive commands from orchestrator

### Agent Execution Flow
1. **Orchestrator uses command_agent tool** → Agent Manager queues task
2. **Agent executes** → Hooks capture all events → DB + WebSocket
3. **Frontend updates** → Event stream shows hooks/responses
4. **Agent completes** → Costs updated → Status returns to idle

---

## Special Features

### 1. Real-Time Cost Tracking
- **Backend**: Extracts costs from Claude SDK `ResultMessage`
- **Database**: Incremental updates to `total_cost`, `input_tokens`, `output_tokens`
- **WebSocket**: Broadcasts `orchestrator_updated` and `agent_updated` events
- **Frontend**: Header bar shows live cost updates

### 2. File Tracking
- **PostToolUse Hook**: Captures git diffs after Read/Write/Edit tool use
- **FileTracker**: Generates summaries of modified/read files
- **Database**: Stored in `agent_logs.payload` JSONB field
- **Frontend**: Displays file changes inline with agent responses

### 3. AI Summarization
- **Background Tasks**: All events (prompts, responses, hooks) get AI summaries
- **Fast Model**: Uses Claude Haiku for speed/cost
- **Database**: Summaries stored in `summary` columns
- **Frontend**: Uses summaries for quick overview in event stream

### 4. Agent Pulse Animations
- **Trigger**: Tool use, hook events, thinking blocks
- **Debouncing**: 300ms debounce to prevent flicker
- **Cleanup**: Automatic cleanup on unmount to prevent memory leaks
- **Visual Feedback**: Pulsing glow indicates active agent

### 5. Session Resumption
- **CLI Flag**: `--session <session_id>` to resume existing orchestrator
- **Database Lookup**: Validates session_id exists in `orchestrator_agents`
- **State Recovery**: Loads costs, tokens, working directory
- **Claude SDK**: Resumes conversation history from session

---

## Configuration & Deployment

### Environment Variables (.env)
```bash
# Backend
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9403

# Frontend
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175
VITE_API_BASE_URL=http://127.0.0.1:9403

# WebSocket
WEBSOCKET_URL=ws://127.0.0.1:9403/ws

# Database
DATABASE_URL=postgresql://...
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Orchestrator
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_WORKING_DIR=/path/to/project

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs

# IDE Integration
IDE_COMMAND=code
IDE_ENABLED=true
```

### Startup Scripts
```bash
# Backend (port 9403)
./start_be.sh

# Frontend (port 5175)
./start_fe.sh

# With session resumption
./start_be.sh --session <session_id>

# With custom working directory
./start_be.sh --cwd /path/to/project
```

---

## Architecture Strengths

### ✅ Scalability
- **Connection pooling**: asyncpg pool handles concurrent database operations
- **WebSocket broadcasting**: Efficient fan-out to multiple clients
- **Background tasks**: AI summarization and cost updates don't block responses

### ✅ Real-Time Updates
- **WebSocket streaming**: Sub-second latency for events
- **Incremental rendering**: Chat messages stream as they're generated
- **Live cost tracking**: Costs update immediately after each interaction

### ✅ Persistence
- **PostgreSQL**: All events, costs, and state persisted
- **Session resumption**: Continue conversations across restarts
- **Event replay**: Load history from database on page refresh

### ✅ Developer Experience
- **Type safety**: TypeScript types mirror Python Pydantic models
- **Hot reload**: Vue HMR + FastAPI auto-reload
- **Rich logging**: Hourly rotating logs + Rich console output
- **Error handling**: Comprehensive try/catch with WebSocket error broadcasts

---

## Future Enhancements

### Potential Improvements
1. **Multi-user support**: Add authentication and user-scoped orchestrators
2. **Agent templates marketplace**: Share and discover community templates
3. **Performance metrics**: Track agent execution time, token efficiency
4. **Agent collaboration**: Enable agents to communicate directly
5. **Cost budgets**: Set spending limits and alerts
6. **Export/import**: Export agent configurations and chat history

---

## Conclusion

Orchestrator 3 Stream is a **production-ready, full-stack multi-agent orchestration platform** that demonstrates:

- **Robust architecture**: Clean separation of concerns across layers
- **Real-time capabilities**: WebSocket streaming with sub-second latency
- **Comprehensive logging**: Every event captured and persisted
- **Type safety**: End-to-end TypeScript + Pydantic validation
- **Developer-friendly**: Rich CLI, hot reload, excellent error handling

The system successfully bridges the gap between Claude SDK agent capabilities and a modern web-based control interface, enabling sophisticated multi-agent workflows with full observability and control.

---

**Document Version:** 1.0
**Last Updated:** 2025-01-22
**Maintainer:** Orchestrator 3 Stream Team
