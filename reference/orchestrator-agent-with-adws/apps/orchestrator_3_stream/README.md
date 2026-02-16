# Orchestrator 3 Stream

> Real-time streaming multi-agent orchestration with PostgreSQL backend and Vue 3 frontend

A production-ready web-based orchestration system for managing and chatting with an orchestrator agent that coordinates multiple Claude Code agents. Features real-time WebSocket streaming, comprehensive database persistence, hourly rotating logs, and a modern dark-themed UI.

## 🎯 What It Does

This application provides a **web interface** for interacting with an orchestrator agent that can:
- Create and manage specialized Claude Code agents
- Dispatch tasks to agents
- Monitor agent status and progress
- Coordinate multi-agent workflows
- Maintain conversation context across sessions
- Stream responses in real-time via WebSocket

## ✅ Current Status

**FULLY FUNCTIONAL - E2E TESTED** ✓

- ✅ Complete orchestrator chat with Claude SDK integration
- ✅ Real-time WebSocket streaming of responses
- ✅ Database persistence (PostgreSQL)
- ✅ Chat history loading from database
- ✅ Session continuity across interactions
- ✅ Cost tracking (tokens + USD)
- ✅ 3-column UI layout (agents, events, chat)
- ✅ 5/5 backend tests passing (pytest)
- ✅ E2E validation with Playwright MCP
- ✅ Auto-scroll during message send and streaming
- ✅ Typing indicators
- ✅ CLI parameters (--session, --cwd)

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python 3.12+ with Astral UV
- FastAPI (async web framework)
- asyncpg (PostgreSQL connection pooling)
- Claude Agent SDK (claude-agent-sdk)
- WebSockets (real-time streaming)
- Rich (console logging)
- Hourly rotating file logs

**Frontend:**
- Vue 3 with Composition API
- TypeScript (type-safe)
- Vite (dev server + build tool)
- Pinia (state management)
- Axios (HTTP client)
- Native WebSocket API
- Dark theme with cyan/teal accents

**Database:**
- PostgreSQL (NeonDB)
- Shared schema from `apps/orchestrator_db/`
- 6 tables: orchestrator_agents, agents, prompts, agent_logs, system_logs, orchestrator_chat

### Data Flow

```
User (Browser)
    ↓ HTTP POST /send_chat
Backend (FastAPI)
    ↓ process_user_message()
Claude Agent SDK (API call)
    ↓ Streaming response
WebSocket (broadcast chunks)
    ↓ chat_stream events
Frontend (Pinia Store)
    ↓ Accumulate chunks
UI (OrchestratorChat.vue)
    ↓ Display streaming text
Database (PostgreSQL)
    ↓ Persist complete messages
```

## 📁 Complete File Structure

```
apps/orchestrator_3_stream/
├── .env                                    # Environment config (gitignored, contains secrets)
├── .env.sample                             # Environment template
├── start_be.sh                             # Backend launcher script (port 9403)
├── start_fe.sh                             # Frontend launcher script (port 5175)
├── CLAUDE.md                               # Agent instructions & file summaries
├── README.md                               # This file
│
├── backend/                                # Python FastAPI Backend
│   ├── main.py                             # FastAPI app with endpoints + WebSocket
│   ├── pyproject.toml                      # UV dependencies (claude-agent-sdk, fastapi, etc.)
│   │
│   ├── modules/                            # Backend modules
│   │   ├── config.py                       # Environment loader + orchestrator config
│   │   ├── logger.py                       # Hourly rotating logger + Rich console
│   │   ├── websocket_manager.py            # WebSocket connection manager + broadcasting
│   │   ├── database.py                     # Database pool + queries (NEW - 496 lines)
│   │   ├── orchestrator_service.py         # Orchestrator business logic (NEW - 359 lines)
│   │   └── orch_database_models.py         # Pydantic models (synced from orchestrator_db)
│   │
│   ├── prompts/                            # System prompts
│   │   └── orchestrator_agent_system_prompt.md  # Orchestrator agent instructions
│   │
│   ├── logs/                               # Hourly rotating log files
│   │   └── YYYY-MM-DD_HH.log              # Auto-generated (e.g., 2025-10-27_14.log)
│   │
│   └── tests/                              # Backend tests (NO MOCKING)
│       └── test_database.py                # Database integration tests (5/5 passing)
│
└── frontend/                               # Vue 3 TypeScript Frontend
    ├── package.json                        # npm dependencies (axios, pinia, vue)
    ├── vite.config.ts                      # Vite config (loads .env for ports)
    ├── tsconfig.json                       # TypeScript config
    │
    └── src/
        ├── main.ts                         # Vue app entry point
        ├── App.vue                         # Root component (3-column layout)
        ├── types.d.ts                      # TypeScript interfaces (mirrors DB models)
        │
        ├── components/                     # Vue components
        │   ├── AgentList.vue               # Left sidebar: agent cards (purple theme)
        │   ├── EventStream.vue             # Center: filtered event log
        │   └── OrchestratorChat.vue        # Right sidebar: chat interface (FULLY WIRED)
        │
        ├── stores/                         # Pinia state management
        │   └── orchestratorStore.ts        # Main store (REAL API - no test data)
        │
        ├── services/                       # API layer (NEW)
        │   ├── api.ts                      # Axios configuration (NEW - 41 lines)
        │   └── chatService.ts              # HTTP + WebSocket service (NEW - 125 lines)
        │
        ├── data/
        │   └── testData.ts                 # Sample data (not used by chat anymore)
        │
        └── styles/
            └── global.css                  # Dark theme CSS with cyan/teal accents
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL database (NeonDB recommended)
- Anthropic API key

### Setup

```bash
# 1. Navigate to project directory
cd apps/orchestrator_3_stream

# 2. Copy and configure environment
cp .env.sample .env
# Edit .env and set:
#   - DATABASE_URL (PostgreSQL connection string)
#   - ANTHROPIC_API_KEY (your API key)

# 3. Run database migrations (from project root)
cd ../../
uv run python apps/orchestrator_db/run_migrations.py
cd apps/orchestrator_3_stream

# 4. Install backend dependencies
cd backend
uv sync
cd ..

# 5. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Run

```bash
# Terminal 1 - Start backend
./start_be.sh

# Terminal 2 - Start frontend
./start_fe.sh
```

### Access

- **Frontend**: http://127.0.0.1:5175
- **Backend API**: http://127.0.0.1:9403
- **WebSocket**: ws://127.0.0.1:9403/ws
- **Health Check**: http://127.0.0.1:9403/health

## 🎨 Features

### ✅ Fully Implemented

#### Backend Features

- [x] **Database Integration**
  - Connection pooling with asyncpg
  - Chat message persistence (`orchestrator_chat` table)
  - Orchestrator metadata management
  - Turn counting and session tracking
  - Cost accumulation (tokens + USD)

- [x] **HTTP Endpoints**
  - `GET /health` - Health check with connection count
  - `GET /get_orchestrator` - Fetch orchestrator ID and metadata
  - `POST /load_chat` - Load chat history with pagination
  - `POST /send_chat` - Send message to orchestrator (async)

- [x] **WebSocket Streaming**
  - Real-time connection management
  - `chat_stream` events (response chunks)
  - `chat_typing` events (typing indicators)
  - `connection_established` welcome message
  - Broadcast to multiple clients
  - Auto-reconnection support

- [x] **Orchestrator Service**
  - Three-phase logging (pre → execution → post)
  - Claude SDK integration
  - Session continuity via `session_id`
  - Response streaming via WebSocket
  - Cost tracking and database updates
  - Error handling and logging

- [x] **CLI Parameters**
  - `--session <id>` - Resume existing session
  - `--cwd <path>` - Set working directory
  - Priority: CLI flag > cwd > .env default

- [x] **Logging System**
  - Hourly rotating log files (`backend/logs/YYYY-MM-DD_HH.log`)
  - Rich-formatted console output
  - Dual output (file + console)
  - Chat event tracking
  - WebSocket event tracking

#### Frontend Features

- [x] **Chat Interface**
  - Load chat history on mount (from database)
  - Send messages to orchestrator
  - Real-time streaming display
  - Typing indicators
  - Auto-scroll on send and streaming
  - Connection status indicator
  - Message timestamps

- [x] **State Management**
  - Pinia store with real API integration
  - WebSocket connection management
  - Chat message accumulation
  - Streaming chunk handling
  - Error handling

- [x] **UI Components**
  - 3-column responsive layout
  - Agent list (purple gradient, modern cards)
  - Event stream (filters, search, quick filters)
  - Chat interface (connected to backend)
  - Dark theme with cyan/teal accents

### 🔜 Future Enhancements

- [ ] Agent management UI (create, list, delete agents)
- [ ] Live agent status updates in sidebar
- [ ] Event stream integration (show agent logs)
- [ ] Markdown rendering in chat messages
- [ ] Code syntax highlighting
- [ ] Message search/filtering
- [ ] Chat export functionality
- [ ] Multi-orchestrator support
- [ ] Message editing/deletion

## 🧪 Testing

### Backend Tests (pytest)

**Location:** `backend/tests/test_database.py`

**Philosophy:** NO MOCKING - Real database + Real Claude SDK

**Results:**
```
5/5 PASSING ✅

✓ test_database_connection - Real PostgreSQL connection
✓ test_get_or_create_orchestrator - Singleton pattern validated
✓ test_insert_and_get_chat_history - Chat persistence verified
✓ test_update_orchestrator_session - Session tracking works
✓ test_update_orchestrator_costs - Cost accumulation works
```

**Run tests:**
```bash
cd backend
uv run pytest tests/ -v
```

### E2E Validation (Playwright MCP)

**Validated with real browser automation:**
```
✅ Frontend loads without errors
✅ WebSocket connects successfully
✅ 21 messages load from database
✅ User can type and send messages
✅ Messages appear immediately in UI
✅ Orchestrator processes via Claude API
✅ Response streams in real-time
✅ All messages persist to database
✅ Auto-scroll works on send and streaming
```

## 📖 Key Implementation Details

### Three-Phase Logging Pattern

Every message interaction follows this pattern:

1. **Pre-Execution**: User message logged to `orchestrator_chat` table immediately
2. **Execution**: Orchestrator agent processes with Claude SDK, streaming via WebSocket
3. **Post-Execution**: Complete response logged, session/costs updated in database

**Code:** `backend/modules/orchestrator_service.py:process_user_message()`

### WebSocket Streaming

**Backend broadcasts:**
```json
{
  "type": "chat_stream",
  "orchestrator_agent_id": "uuid",
  "chunk": "partial response text",
  "is_complete": false,
  "timestamp": "ISO8601"
}

{
  "type": "chat_typing",
  "orchestrator_agent_id": "uuid",
  "is_typing": true
}
```

**Frontend handles:**
- Accumulates chunks in Pinia store
- Updates last message content during streaming
- Finalizes message when `is_complete: true`
- Auto-scrolls to show new content

**Code:**
- Backend: `backend/modules/websocket_manager.py:broadcast_chat_stream()`
- Frontend: `frontend/src/stores/orchestratorStore.ts:handleChatStream()`

### Session Management

- Session ID stored in `orchestrator_agents` table
- Each interaction resumes the session for continuity
- Valid session format: `sess_*` (Claude SDK format)
- Test/invalid sessions start fresh session
- Frontend doesn't manage sessions (handled by backend)

### Database Schema

**Main Tables Used:**

**orchestrator_agents** (Singleton)
- `id` (UUID) - Orchestrator agent identifier
- `session_id` (String, nullable) - Claude SDK session ID
- `working_dir` (String) - Working directory for agent operations
- `input_tokens`, `output_tokens`, `total_cost` - Usage tracking
- `status` - idle|executing|waiting|blocked|complete

**orchestrator_chat** (Append-only log)
- `id` (UUID) - Message identifier
- `orchestrator_agent_id` (UUID FK) - Links to orchestrator
- `sender_type` - user|orchestrator|agent
- `receiver_type` - user|orchestrator|agent
- `message` (Text) - Message content
- `agent_id` (UUID, nullable) - For agent messages
- `metadata` (JSONB) - Extra data like tools_used
- `created_at`, `updated_at` - Timestamps

**Reference:** `apps/orchestrator_db/models.py`

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Backend Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9403

# Frontend Configuration
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175
VITE_API_BASE_URL=http://127.0.0.1:9403

# WebSocket
WEBSOCKET_URL=ws://127.0.0.1:9403/ws

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Orchestrator Configuration
ORCHESTRATOR_MODEL=claude-sonnet-4-20250514
ORCHESTRATOR_WORKING_DIR=/path/to/your/project

# API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs

# CORS
CORS_ORIGINS=http://127.0.0.1:5175,http://localhost:5175
```

### CLI Parameters

**Start backend with options:**

```bash
# Default (new session, cwd from .env or current directory)
./start_be.sh

# Resume existing session
uv run python backend/main.py --session "sess_abc123..."

# Set custom working directory
uv run python backend/main.py --cwd /path/to/project

# Combine both
uv run python backend/main.py --session "sess_abc123..." --cwd /path/to/project
```

**Priority:** `--cwd flag > os.getcwd() > .env ORCHESTRATOR_WORKING_DIR`

## 💬 Using the Chat Interface

### Basic Usage

1. **Open browser** to http://127.0.0.1:5175
2. **Chat loads automatically** with history from database
3. **Type a message** in the input field
4. **Click Send** or press Enter
5. **Watch response stream** in real-time
6. **All messages persist** to database

### Example Conversations

**Create an agent:**
```
You: Create an agent called builder for Python development
Orchestrator: [uses create_agent tool] Created agent 'builder'!
```

**Check agent status:**
```
You: How is the builder agent doing?
Orchestrator: [uses check_agent_status tool] Builder is currently idle...
```

**Send task to agent:**
```
You: Tell builder to implement a FastAPI endpoint
Orchestrator: [uses command_agent tool] Dispatched task to builder!
```

### Session Persistence

- Refresh page → Chat history loads from database
- Send message → Context maintained from previous turns
- Restart backend → Resume with `--session <id>` (optional)

## 📊 Code Statistics

**Total Implementation: ~1,850 lines**

### Backend (1,350 lines)

| File                              | Lines | Purpose                                   |
| --------------------------------- | ----- | ----------------------------------------- |
| `modules/database.py`             | 496   | Database pool, orchestrator ops, chat ops |
| `modules/orchestrator_service.py` | 359   | Business logic, Claude SDK, streaming     |
| `main.py`                         | 336   | FastAPI app, endpoints, WebSocket, CLI    |
| `modules/config.py`               | 155   | Environment config, orchestrator settings |
| `modules/websocket_manager.py`    | 245   | WebSocket manager with streaming methods  |
| `modules/logger.py`               | 181   | Hourly rotating logger with Rich output   |
| `tests/test_database.py`          | 179   | Integration tests (5 passing)             |

### Frontend (500 lines)

| File                              | Lines | Purpose                                       |
| --------------------------------- | ----- | --------------------------------------------- |
| `stores/orchestratorStore.ts`     | 372   | Pinia store with real API integration         |
| `services/chatService.ts`         | 125   | HTTP client + WebSocket handler               |
| `services/api.ts`                 | 41    | Axios configuration                           |
| `types.d.ts`                      | 219   | TypeScript interfaces (DB models + API types) |
| `components/OrchestratorChat.vue` | 265   | Chat UI with reactivity and auto-scroll       |

## 🔍 API Reference

### HTTP Endpoints

**GET /health**
- Returns: `{ status, service, websocket_connections }`
- Purpose: Health check

**GET /get_orchestrator**
- Returns: `{ status, orchestrator: { id, session_id, status, tokens, cost } }`
- Purpose: Get orchestrator metadata for frontend initialization

**POST /load_chat**
- Body: `{ orchestrator_agent_id, limit? }`
- Returns: `{ status, messages[], turn_count }`
- Purpose: Load chat history from database

**POST /send_chat**
- Body: `{ message, orchestrator_agent_id }`
- Returns: `{ status, message }`
- Purpose: Send message to orchestrator (async, streams via WebSocket)

### WebSocket Events

**Sent by Backend:**

```typescript
// Streaming response chunk
{
  type: "chat_stream",
  orchestrator_agent_id: string,
  chunk: string,
  is_complete: boolean,
  timestamp: string
}

// Typing indicator
{
  type: "chat_typing",
  orchestrator_agent_id: string,
  is_typing: boolean,
  timestamp: string
}

// Error notification
{
  type: "error",
  message: string,
  details: object
}

// Connection confirmation
{
  type: "connection_established",
  client_id: string,
  timestamp: string
}
```

**Sent by Frontend:**

```typescript
// Chat message (alternative to HTTP)
{
  type: "chat_message",
  message: string,
  orchestrator_agent_id: string
}
```

## 🐛 Troubleshooting

### Backend Won't Start

**Check:**
1. Is port 9403 available? `lsof -ti:9403 | xargs kill -9`
2. Is DATABASE_URL set in .env?
3. Are migrations run? `uv run python apps/orchestrator_db/run_migrations.py`

### Frontend Can't Connect

**Check:**
1. Is backend running on port 9403?
2. Is VITE_API_BASE_URL correct in .env?
3. Check browser console for CORS errors
4. Verify WebSocket URL matches backend port

### Messages Not Loading

**Check:**
1. Browser console for API errors
2. Backend logs for database errors
3. Orchestrator exists in database: `SELECT * FROM orchestrator_agents WHERE archived = false`
4. Chat history exists: `SELECT COUNT(*) FROM orchestrator_chat`

### Orchestrator Not Responding

**Check:**
1. Backend logs for Claude SDK errors
2. Is ANTHROPIC_API_KEY set in .env?
3. Check session ID format (should be `sess_*` or null)
4. Backend console for exception tracebacks

### Port Already in Use

```bash
# Kill process on backend port
lsof -ti:9403 | xargs kill -9

# Kill process on frontend port
lsof -ti:5175 | xargs kill -9
```

## 📈 Performance & Scaling

### Database Connection Pooling

- Min connections: 5
- Max connections: 20
- Connection timeout: 60s
- Configured in `modules/database.py:init_pool()`

### WebSocket Scalability

- Supports multiple concurrent connections
- Broadcast to all connected clients
- Connection metadata tracking
- Graceful disconnect handling

### Chat History Pagination

- Default limit: 50 messages
- Configurable via `load_chat` endpoint
- Oldest messages first (ASC order)

## 🎓 Development

### Adding New Features

**Add HTTP endpoint:**
1. Add Pydantic request/response models in `main.py`
2. Create endpoint handler with `@app.post()` or `@app.get()`
3. Use `app.state.orchestrator_service` for business logic
4. Log with `logger.http_request()`

**Add WebSocket event:**
1. Add broadcast method in `websocket_manager.py`
2. Call from orchestrator_service or endpoint
3. Handle in frontend `chatService.ts` callbacks

**Update database schema:**
1. Modify `apps/orchestrator_db/migrations/*.sql`
2. Run migrations: `uv run python apps/orchestrator_db/run_migrations.py`
3. Sync models: `uv run python apps/orchestrator_db/sync_models.py`

### Running Tests

```bash
# Backend integration tests (real database)
cd backend
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=modules --cov-report=html

# Frontend type checking
cd frontend
npm run type-check

# Frontend build test
npm run build
```

## 📚 Related Documentation

- **Main Project**: `../../README.md`
- **Database Schema**: `../orchestrator_db/README.md`
- **Implementation Spec**: `../../specs/orchestrator-3-stream-chat-implementation.md`
- **Agent Instructions**: `CLAUDE.md`

## 🙏 Credits

Built following patterns from `orchestrator_1_term` (production CLI orchestrator).

**Key References:**
- `orchestrator_1_term/modules/orchestrator_agent.py` - Agent execution loop
- `orchestrator_1_term/modules/database/orchestrator_chat_db.py` - Chat operations
- `orchestrator_1_term/modules/database/database.py` - Connection pooling

---

## 🔄 Complete Data Flow Architecture

### System Component Diagram

```mermaid
graph TB
    subgraph "Frontend (Vue 3 + TypeScript)"
        subgraph "Components"
            OrchestratorChat["OrchestratorChat.vue<br/>Chat Interface"]
            EventStream["EventStream.vue<br/>Event Log Stream"]
            AgentList["AgentList.vue<br/>Agent Sidebar"]
            AppHeader["AppHeader.vue<br/>Header Bar"]
            FilterControls["FilterControls.vue<br/>Filters"]
        end

        subgraph "Pinia Store"
            Store["orchestratorStore.ts<br/>State Management"]
        end

        subgraph "Services"
            ChatService["chatService.ts<br/>HTTP + WebSocket"]
            API["api.ts<br/>Axios Client"]
        end

        subgraph "State"
            chatMessages["chatMessages: Array ChatMessage"]
            eventStreamEntries["eventStreamEntries: Array EventStreamEntry"]
            agents["agents: Array Agent"]
            orchestratorInfo["orchestratorInfo"]
            isTyping["isTyping: boolean"]
        end
    end

    subgraph "Backend (FastAPI + asyncpg)"
        subgraph "API Layer"
            FastAPI["main.py<br/>FastAPI Server"]
            WSEndpoint["WebSocket /ws"]
        end

        subgraph "Business Logic"
            OrchService["orchestrator_service.py<br/>Orchestrator Execution"]
            AgentManager["agent_manager.py<br/>Agent Lifecycle"]
            WSManager["websocket_manager.py<br/>WebSocket Broadcasting"]
        end

        subgraph "Data Layer"
            Database["database.py<br/>PostgreSQL Operations"]
            OrchHooks["orchestrator_hooks.py<br/>Orchestrator Event Hooks"]
            CmdHooks["command_agent_hooks.py<br/>Command Agent Event Hooks"]
        end

        subgraph "Database Tables"
            OrchTable[("orchestrator_agents")]
            ChatTable[("orchestrator_chat")]
            AgentsTable[("agents")]
            LogsTable[("agent_logs")]
        end

        subgraph "External"
            ClaudeSDK["Claude Agent SDK<br/>ClaudeSDKClient"]
        end
    end

    %% Frontend Internal Flow
    OrchestratorChat --> Store
    EventStream --> Store
    AgentList --> Store
    AppHeader --> Store

    Store --> ChatService
    Store --> API

    Store --> chatMessages
    Store --> eventStreamEntries
    Store --> agents
    Store --> orchestratorInfo
    Store --> isTyping

    %% Frontend to Backend HTTP
    API -->|HTTP POST /send_chat| FastAPI
    API -->|HTTP POST /load_chat| FastAPI
    API -->|HTTP GET /get_orchestrator| FastAPI
    API -->|HTTP GET /get_events| FastAPI
    API -->|HTTP GET /list_agents| FastAPI

    %% WebSocket Connection
    ChatService -->|WebSocket Connect| WSEndpoint
    WSEndpoint -->|Events| ChatService

    %% Backend Internal Flow
    FastAPI --> OrchService
    FastAPI --> Database

    OrchService --> ClaudeSDK
    OrchService --> Database
    OrchService --> WSManager
    OrchService --> AgentManager

    AgentManager --> ClaudeSDK
    AgentManager --> Database
    AgentManager --> WSManager

    WSManager -->|Broadcast| WSEndpoint

    %% Hooks Flow
    ClaudeSDK -->|Events| OrchHooks
    ClaudeSDK -->|Events| CmdHooks
    OrchHooks --> Database
    OrchHooks --> WSManager
    CmdHooks --> Database
    CmdHooks --> WSManager

    %% Database Operations
    Database --> OrchTable
    Database --> ChatTable
    Database --> AgentsTable
    Database --> LogsTable
```

### User Sends Chat Message - Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant OrchestratorChat
    participant Store
    participant ChatService
    participant FastAPI
    participant OrchService
    participant Database
    participant WSManager
    participant ClaudeSDK

    User->>OrchestratorChat: Type message & click send
    OrchestratorChat->>Store: sendMessage(text)

    Note over Store: Add optimistic message<br/>to chatMessages

    Store->>ChatService: sendMessage(text, orchId)
    ChatService->>FastAPI: POST /send_chat

    Note over FastAPI: Returns immediately<br/>(async processing)

    FastAPI-->>ChatService: {status: "success"}

    FastAPI->>OrchService: process_user_message(text, orchId)

    Note over OrchService: PHASE 1: Pre-execution

    OrchService->>Database: insert_chat_message(user → orchestrator)
    Database->>ChatTable: INSERT
    Database-->>OrchService: chat_id

    OrchService->>WSManager: broadcast(orchestrator_chat)
    WSManager->>FastAPI: WebSocket.send()
    FastAPI-->>Store: onOrchestratorChat(message)

    Note over Store: User message appears<br/>in event stream + chat UI

    Note over OrchService: PHASE 2: Execution

    OrchService->>WSManager: set_typing_indicator(true)
    WSManager->>FastAPI: WebSocket.send()
    FastAPI-->>Store: onTyping(true)

    Note over Store: Show typing indicator

    OrchService->>ClaudeSDK: client.query(text)

    loop For each response block
        ClaudeSDK-->>OrchService: TextBlock/ThinkingBlock/ToolUseBlock

        alt TextBlock
            OrchService->>Database: insert_chat_message(orchestrator → user)
            Database->>ChatTable: INSERT
            Database-->>OrchService: message_id

            OrchService->>WSManager: broadcast(orchestrator_chat)
            WSManager->>FastAPI: WebSocket.send()
            FastAPI-->>Store: onOrchestratorChat(message)

            Note over Store: Response chunk appears<br/>in chat UI immediately

        else ThinkingBlock
            OrchService->>Database: insert_system_log(thinking)
            OrchService->>WSManager: broadcast(thinking_block)
            WSManager->>FastAPI: WebSocket.send()
            FastAPI-->>Store: onThinkingBlock(data)

        else ToolUseBlock
            OrchService->>Database: insert_system_log(tool_use)
            OrchService->>WSManager: broadcast(tool_use_block)
            WSManager->>FastAPI: WebSocket.send()
            FastAPI-->>Store: onToolUseBlock(data)
        end
    end

    ClaudeSDK-->>OrchService: ResultMessage

    Note over OrchService: PHASE 3: Post-execution

    OrchService->>Database: update_orchestrator_session(orchId, sessionId)
    OrchService->>Database: update_orchestrator_costs(tokens, cost)

    OrchService->>WSManager: set_typing_indicator(false)
    WSManager->>FastAPI: WebSocket.send()
    FastAPI-->>Store: onTyping(false)

    Note over Store: Hide typing indicator
```

### Initial Page Load - Sequence Diagram

```mermaid
sequenceDiagram
    participant Browser
    participant App
    participant Store
    participant API
    participant ChatService
    participant FastAPI
    participant Database

    Browser->>App: Load page
    App->>Store: init()

    par Parallel HTTP Requests
        Store->>API: GET /get_orchestrator
        API->>FastAPI: HTTP Request
        FastAPI->>Database: get_orchestrator()
        Database-->>FastAPI: orchestrator data
        FastAPI-->>API: {orchestrator: {...}}
        API-->>Store: orchestrator info

        Note over Store: Store orchestrator ID,<br/>session_id, tokens, cost
    and
        Store->>API: POST /load_chat
        API->>FastAPI: HTTP Request
        FastAPI->>Database: get_chat_history(limit=200)
        Database-->>FastAPI: messages[]
        FastAPI-->>API: {messages: [...]}
        API-->>Store: chat history

        Note over Store: Populate chatMessages<br/>with history
    and
        Store->>API: GET /get_events
        API->>FastAPI: HTTP Request
        FastAPI->>Database: list_agent_logs() + list_orchestrator_chat()
        Database-->>FastAPI: events[]
        FastAPI-->>API: {events: [...]}
        API-->>Store: event history

        Note over Store: Populate eventStreamEntries<br/>with history
    and
        Store->>API: GET /list_agents
        API->>FastAPI: HTTP Request
        FastAPI->>Database: list_agents()
        Database-->>FastAPI: agents[]
        FastAPI-->>API: {agents: [...]}
        API-->>Store: agents list

        Note over Store: Populate agents array
    end

    Store->>ChatService: connectWebSocket(url, callbacks)
    ChatService->>FastAPI: WebSocket Connect /ws
    FastAPI-->>ChatService: Connection established

    Note over Store: isConnected = true<br/>Ready for real-time updates
```

### WebSocket Event Types

| Event Type             | Trigger                               | Data Structure                                                    | Frontend Handler                                                             |
| ---------------------- | ------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `orchestrator_chat`    | User message or orchestrator response | `{type, message: {id, sender_type, receiver_type, message, ...}}` | `addOrchestratorChatEvent()` → Updates `chatMessages` + `eventStreamEntries` |
| `chat_stream`          | Response streaming                    | `{type, chunk, is_complete}`                                      | `handleChatStream()` → Shows typing indicator                                |
| `chat_typing`          | Typing indicator                      | `{type, is_typing}`                                               | `handleTyping()` → Updates `isTyping`                                        |
| `thinking_block`       | Orchestrator thinking                 | `{type, data: {thinking, ...}}`                                   | `addThinkingBlockEvent()` → Updates `eventStreamEntries`                     |
| `tool_use_block`       | Tool execution                        | `{type, data: {tool_name, tool_input, ...}}`                      | `addToolUseBlockEvent()` → Updates `eventStreamEntries`                      |
| `agent_log`            | Command agent hook event              | `{type, log: {event_type, payload, ...}}`                         | `addAgentLogEvent()` → Updates `eventStreamEntries`                          |
| `agent_created`        | New agent created                     | `{type, agent: {...}}`                                            | `handleAgentCreated()` → Updates `agents`                                    |
| `agent_status_changed` | Agent status update                   | `{type, agent_id, status}`                                        | `handleAgentStatusChange()` → Updates agent in `agents`                      |
| `agent_summary_update` | AI summary generated                  | `{type, agent_id, summary}`                                       | `handleAgentSummaryUpdate()` → Updates latest summary                        |
| `error`                | Error occurred                        | `{type, error_message, details}`                                  | `handleWebSocketError()` → Shows error                                       |

### Critical Vue Reactivity Pattern

**ALWAYS use spread operator for array updates to trigger Vue reactivity:**

```typescript
// ❌ WRONG - May not trigger reactivity during rapid updates
chatMessages.value.push(newMessage)

// ✅ CORRECT - Always triggers reactivity
chatMessages.value = [...chatMessages.value, newMessage]
```

This pattern is used in:
- `addOrchestratorChatEvent()` - Updates `chatMessages` and `eventStreamEntries`
- `addAgentLogEvent()` - Updates `eventStreamEntries`
- `addEventStreamEntry()` - Updates `eventStreamEntries`
- `addThinkingBlockEvent()` - Updates `eventStreamEntries`
- `addToolUseBlockEvent()` - Updates `eventStreamEntries`

---

**Status**: ✅ Production Ready | E2E Tested | Chat Fully Functional

For detailed file-by-file summaries, see [CLAUDE.md](./CLAUDE.md).
