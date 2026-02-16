# Orchestrator 3 Stream Backend - Architecture Summary

## Key Backend Nodes - Quick Reference

- **main.py**: FastAPI application entry point that defines all REST endpoints and WebSocket connection management.
- **config.py**: Centralized environment variable and configuration loader supporting runtime working directory overrides.
- **logger.py**: Rich console logging with automatic hourly log file rotation for comprehensive event tracking.
- **database.py**: asyncpg connection pool manager and CRUD operations for all 6 core database tables.
- **websocket_manager.py**: Singleton WebSocket manager that broadcasts all system events to connected clients in real-time.
- **orchestrator_service.py**: Business logic layer that initializes Claude SDK, executes orchestrator agent, and manages session lifecycle.
- **agent_manager.py**: Manages agent creation, execution, and provides 8 management tools to the orchestrator via MCP server.
- **orch_database_models.py**: Pydantic models for type-safe database entity representation with automatic UUID/JSON conversion.
- **hooks.py**: Generic event hook implementations that capture Claude SDK events and broadcast them via WebSocket.
- **orchestrator_hooks.py**: Orchestrator-specific hooks that track management tool usage and orchestrator state changes.
- **command_agent_hooks.py**: Agent command-specific hooks that capture tool usage and file changes during agent execution.
- **subagent_loader.py**: Template registry that discovers and caches subagent templates from `.claude/agents/` directory.
- **slash_command_parser.py**: YAML frontmatter parser that discovers slash commands from `.claude/commands/` directory.
- **file_tracker.py**: Detects and tracks file modifications during agent execution for UI reporting.

---

## Executive Overview

The Orchestrator 3 Stream backend is a FastAPI-based multi-agent orchestration system with PostgreSQL persistence and real-time WebSocket streaming. It implements an event-driven architecture where a central orchestrator agent manages and coordinates multiple subordinate agents while broadcasting all activity to the frontend in real-time.

**Key Characteristics:**
- **Framework**: FastAPI with asyncpg (PostgreSQL)
- **Real-time**: WebSocket streaming for all events
- **Agents**: Claude SDK integration with hook-based event capture
- **Persistence**: PostgreSQL (NeonDB) for all data
- **Architecture**: Modular, service-oriented with clear separation of concerns

---

## Architecture Overview

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3 + Pinia)                             │
└────────────┬──────────────────────────────────────────────────────────────────┘
             │
             │ HTTP REST + WebSocket
             │
┌────────────▼──────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (main.py)                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ API Routes:                                                            │  │
│  │ • GET /health                     - Health check                       │  │
│  │ • GET /get_orchestrator           - Orchestrator metadata             │  │
│  │ • GET /get_headers                - Working directory                 │  │
│  │ • POST /send_chat                 - Send user message                 │  │
│  │ • POST /load_chat                 - Load chat history                 │  │
│  │ • GET /get_events                 - Retrieve unified events            │  │
│  │ • GET /list_agents                - List active agents                │  │
│  │ • POST /api/open-file             - IDE file opening                  │  │
│  │ • WebSocket /ws                   - Real-time event streaming         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────┬────────────────┐
    │                 │              │              │                │
┌───▼────┐    ┌──────▼──────┐  ┌───▼──────┐  ┌──▼────────┐  ┌─────▼─────┐
│ Database│    │ WebSocket   │  │ Orchestr.│  │  Agent    │  │  Logging  │
│ Module  │    │ Manager     │  │ Service  │  │ Manager   │  │ Module    │
└────────┘    └─────────────┘  └──────────┘  └──────────┘  └───────────┘
    │                │              │              │            │
    └────────┬───────┴──────────┬───┴──────────┬──┴──────────┬──┘
             │                  │              │             │
┌────────────▼──────────────────▼──┬───────────▼──┬──────────▼──┐
│                                  │              │             │
│           PostgreSQL             │ Claude SDK   │ Rich Console│
│         (NeonDB)                 │ Client       │ + File Logs │
│                                  │              │             │
│ Tables:                          │ • Hooks      │ • Hourly    │
│ • orchestrator_agents            │ • Tools      │   rotation  │
│ • agents                         │              │             │
│ • agent_logs                     │              │             │
│ • system_logs                    │              │             │
│ • orchestrator_chat              │              │             │
│ • prompts                        │              │             │
│                                  │              │             │
└──────────────────────────────────┴──────────────┴─────────────┘
```

---

## Core Modules Overview

### 1. **main.py** - FastAPI Application Entry Point
**Purpose**: Initialize FastAPI app, manage lifecycle, define API routes

**Key Responsibilities**:
- Application startup/shutdown (lifespan context manager)
- Database pool initialization and connection management
- REST API endpoint definitions
- WebSocket connection management
- CLI argument parsing (--session, --cwd)
- CORS configuration
- Orchestrator initialization (new or resumed)

**Key Routes**:
- Health check and monitoring endpoints
- Chat message handling (send/load)
- Event aggregation from multiple sources
- Agent listing with stats
- Orchestrator metadata exposure

**Dependencies**: fastapi, asyncpg, WebSocket, config, database, orchestrator_service

---

### 2. **modules/config.py** - Configuration Management
**Purpose**: Centralized environment variable and configuration loading

**Key Features**:
- Environment variable loading from `.env` file
- Runtime working directory override via `set_working_dir()`
- Port configuration (Backend: 8002, Frontend: 5175)
- Database URL configuration
- Logging configuration (hourly rotation, log level)
- Model configuration (Claude Sonnet/Haiku)
- IDE integration settings
- CORS origin configuration

**Configuration Hierarchy**:
1. Environment variables (.env file)
2. Default values (fallback)
3. CLI overrides (--cwd flag)

**Usage Pattern**: `from modules import config; config.get_working_dir()`

---

### 3. **modules/logger.py** - Structured Logging System
**Purpose**: Dual-output logging to console and hourly-rotating files

**Key Components**:
- `HourlyRotatingFileHandler`: Custom handler that rotates logs hourly
- `OrchestratorLogger`: Main logger class with Rich console formatting

**Features**:
- Rich formatted console output with colors and emojis
- Hourly log file rotation (YYYY-MM-DD_HH.log)
- Specialized logging methods:
  - `logger.success()` - Green ✅ with message
  - `logger.error()` - Red ❌ with message
  - `logger.http_request()` - HTTP request logging
  - `logger.websocket_event()` - WebSocket event logging
  - `logger.agent_event()` - Agent-specific events
  - `logger.chat_event()` - Chat interactions
  - `logger.section()` - Section headers

**Log Location**: `backend/logs/YYYY-MM-DD_HH.log`

---

### 4. **modules/database.py** - Database Connection & Operations
**Purpose**: asyncpg connection pool management and database operations

**Major Components**:

#### Connection Pool Management
- `init_pool()` - Initialize asyncpg connection pool
- `get_pool()` - Get existing pool instance
- `close_pool()` - Close all connections
- `get_connection()` - Context manager for acquiring connections

#### Orchestrator Operations
- `create_new_orchestrator()` - Always create fresh orchestrator
- `get_or_create_orchestrator()` - Singleton pattern getter
- `get_orchestrator()` - Get active orchestrator
- `get_orchestrator_by_session()` - Resume session by ID
- `get_orchestrator_by_id()` - Fetch by UUID
- `update_orchestrator_session()` - Update session ID (first-time only)
- `update_orchestrator_costs()` - Increment token usage and costs
- `update_orchestrator_metadata()` - Merge metadata with PostgreSQL merge operator

#### Agent Operations
- `create_agent()`, `get_agent()`, `list_agents()`, `delete_agent()`
- `update_agent_status()`, `update_agent_costs()`, `update_agent_session()`

#### Chat & Log Operations
- `insert_chat_message()` - Log 3-way chat (user ↔ orchestrator ↔ agents)
- `list_orchestrator_chat()` - Retrieve chat history
- `insert_hook_event()` - Log Claude SDK hook events
- `insert_message_block()` - Log response blocks (TextBlock, ThinkingBlock, ToolUseBlock)
- `insert_system_log()` - Log system-level events

#### Query Operations
- `list_agent_logs()`, `get_agent_logs()` - Fetch logs with filtering
- `get_chat_history()` - Load chat messages
- `get_orchestrator_action_blocks()` - Fetch thinking/tool blocks
- `get_turn_count()` - Count total interactions

**Connection String**: PostgreSQL via environment variable `DATABASE_URL`

**Pool Configuration**:
- Min size: 5 connections
- Max size: 20 connections
- Command timeout: 60 seconds

---

### 5. **modules/websocket_manager.py** - Real-time Event Broadcasting
**Purpose**: Manage WebSocket connections and broadcast events to all connected clients

**Key Responsibilities**:
- Accept/disconnect WebSocket clients
- Maintain active connection list
- Broadcast events to all clients simultaneously
- Track connection metadata (client_id, connected_at)

**Core Methods**:
- `connect()` - Accept new WebSocket connection
- `disconnect()` - Remove disconnected client
- `send_to_client()` - Send to specific client
- `broadcast()` - Broadcast to all clients

**Event Broadcasting Methods**:
- `broadcast_agent_created/updated/deleted()`
- `broadcast_agent_status_change()`
- `broadcast_agent_log()` - Agent event logs
- `broadcast_agent_summary_update()`
- `broadcast_orchestrator_updated()`
- `broadcast_system_log()`
- `broadcast_chat_message()`
- `broadcast_chat_stream()` - Real-time chat chunks
- `broadcast_error()` - Error notifications
- `set_typing_indicator()` - Typing status

**Global Instance**: `get_websocket_manager()` - Singleton pattern

---

### 6. **modules/orchestrator_service.py** - Orchestrator Business Logic
**Purpose**: Service layer for orchestrator agent execution with Claude SDK integration

**Key Responsibilities**:
- Initialize Claude SDK client with hooks
- Process user messages asynchronously
- Stream responses via WebSocket in real-time
- Manage orchestrator lifecycle and costs
- Capture system metadata on first interaction
- Load chat history with action blocks merged

**Core Classes**:
- `OrchestratorService` - Main service class

**Key Methods**:
- `process_user_message()` - Main message processing pipeline
- `load_chat_history()` - Load chat with thinking/tool blocks
- `_load_system_prompt()` - Load and inject SUBAGENT_MAP template
- `_create_claude_agent_options()` - Configure Claude SDK options
- `_build_hooks_for_orchestrator()` - Setup event hooks

**Features**:
- Session resumption via Claude SDK
- Streaming text response chunks
- Hook-based event capture (PreToolUse, PostToolUse, Stop)
- MCP server registration for management tools
- Setting sources from project (CLAUDE.md, slash commands)
- Token and cost tracking
- Thinking block and tool use block capture

**Management Tools Exposed**:
- `create_agent()` - Create new managed agent
- `list_agents()` - List all active agents
- `command_agent()` - Send command to agent
- `check_agent_status()` - Check agent status and logs
- `delete_agent()` - Archive/delete agent
- `interrupt_agent()` - Interrupt agent execution
- `read_system_logs()` - Query system logs
- `report_cost()` - Get cost breakdown

---

### 7. **modules/agent_manager.py** - Agent Lifecycle Management
**Purpose**: Centralize agent creation, execution, and monitoring

**Key Responsibilities**:
- Create and manage agent instances
- Execute agents in background threads
- Register management tools for orchestrator
- Track active agent clients and state
- File change tracking via FileTracker
- Subagent template loading and selection

**Core Classes**:
- `AgentManager` - Main manager class

**Key Methods**:
- `create_agent()` - Create new agent (async)
- `command_agent()` - Execute agent with command (async)
- `_execute_agent_in_thread()` - Run agent in background thread
- `create_management_tools()` - Build 8 management tools

**Features**:
- 8 management tools for orchestrator
- Tool result streaming via WebSocket
- File change tracking
- Subagent template support
- Background execution with threading
- Agent client lifecycle management
- Hook registration for event capture

---

### 8. **modules/orch_database_models.py** - Pydantic Data Models
**Purpose**: Type-safe database models with automatic UUID and JSON handling

**Models**:
- `OrchestratorAgent` - Singleton orchestrator (maps to orchestrator_agents table)
- `Agent` - Managed agent (maps to agents table)
- `Prompt` - User/orchestrator prompts (maps to prompts table)
- `AgentLog` - Hook events and responses (maps to agent_logs table)
- `SystemLog` - Application-level logs (maps to system_logs table)
- `OrchestratorChat` - 3-way chat log (maps to orchestrator_chat table)

**Key Features**:
- Automatic UUID conversion from asyncpg
- Decimal to float conversion for costs
- JSON string parsing to dict for metadata
- Pydantic validation and serialization
- ISO datetime format for JSON output

**Usage Pattern**: Parse database rows into Pydantic models for type safety

---

### 9. **modules/hooks.py** - Claude SDK Event Hooks
**Purpose**: Capture Claude SDK events and broadcast them in real-time

**Hook Types**:
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution with results
- `UserPromptSubmit` - User prompt submission
- `Stop` - Agent stop event
- `SubagentStop` - Subagent termination
- `PreCompact` - Before message compaction
- `PostToolFileTracking` - File change tracking

**Hook Factory Functions**:
- `create_pre_tool_hook()` - Pre-tool event handler
- `create_post_tool_hook()` - Post-tool event handler
- `create_user_prompt_hook()` - Prompt submission handler
- `create_stop_hook()` - Agent stop handler

**Functionality**:
- Log events to `agent_logs` table
- Broadcast to WebSocket clients
- Spawn async summarization tasks
- Track entry indices for sequencing
- Capture payload with tool names, inputs, results

---

### 10. **modules/command_agent_hooks.py** - Agent Command Hooks
**Purpose**: Specific hooks for agent command execution

**Hook Types**:
- `PreToolUse` - Command-specific pre-tool hook
- `PostToolUse` - Command-specific post-tool hook
- File tracking hooks for detecting changes

**Key Responsibility**: Track tool usage and file modifications during agent execution

---

### 11. **modules/orchestrator_hooks.py** - Orchestrator Event Hooks
**Purpose**: Hooks specific to orchestrator agent execution

**Hook Types**:
- `PreToolUse` - Orchestrator pre-tool hook
- `PostToolUse` - Orchestrator post-tool hook
- `Stop` - Orchestrator stop event

**Responsibility**: Capture orchestrator management tool usage and propagate events

---

### 12. **modules/slash_command_parser.py** - Slash Command Discovery
**Purpose**: Parse and discover slash commands from `.claude/commands/` directory

**Key Components**:
- `SlashCommandFrontmatter` - Pydantic model for command metadata
- `parse_slash_command_file()` - Extract YAML frontmatter
- `discover_slash_commands()` - Scan and parse all commands

**Frontmatter Fields**:
- `description` - Command description
- `argument-hint` - Usage syntax (e.g., "add [tagId] | remove [tagId]")
- `model` - Specific Claude model
- `allowed_tools` - Tools available to command
- `disable-model-invocation` - Prevent auto-invocation

**Special Handling**: `argument-hint` auto-quoted to handle special YAML characters

---

### 13. **modules/subagent_loader.py** - Subagent Template Registry
**Purpose**: Discover and cache subagent templates from `.claude/agents/` directory

**Key Components**:
- `SubagentRegistry` - Registry class for template management
- `parse_subagent_file()` - Parse single template file

**Features**:
- Discover .md files in `.claude/agents/`
- Parse YAML frontmatter for metadata
- Cache templates by name
- Expose templates to orchestrator for agent creation
- Tools list support (comma-separated or YAML array)

**Registry Methods**:
- `discover_templates()` - Scan directory and parse
- `get_template()` - Retrieve by name
- `list_templates()` - Get all templates with descriptions
- `get_available_names()` - Get sorted template names
- `has_templates()` - Check if any available

---

### 14. **modules/subagent_models.py** - Subagent Pydantic Models
**Purpose**: Type-safe models for subagent templates

**Models**:
- `SubagentFrontmatter` - Frontmatter metadata
- `SubagentTemplate` - Complete template (frontmatter + body)

**Fields**:
- `name` - Template identifier
- `description` - Human-readable description
- `tools` - List of allowed tools
- `model` - Claude model variant
- `color` - UI color hint
- `prompt_body` - System prompt text
- `file_path` - Origin file path

---

### 15. **modules/single_agent_prompt.py** - Event Summarization
**Purpose**: AI-powered summarization of individual events using Claude

**Key Function**:
- `summarize_event()` - Summarize single event using Claude Haiku

**Usage**: Background async summarization of agent logs and prompts

---

### 16. **modules/file_tracker.py** - File Change Detection
**Purpose**: Track file modifications during agent execution

**Key Responsibility**: Detect new/modified files for reporting in UI

---

### 17. **modules/event_summarizer.py** - Event Summary Generation
**Purpose**: Generate summaries of events for UI display

**Features**: Async summarization with caching

---

## Database Schema

### Core Tables

#### `orchestrator_agents`
Singleton orchestrator agent that manages other agents
```sql
id (UUID) | session_id (TEXT, UNIQUE) | system_prompt (TEXT) | status |
working_dir | input_tokens | output_tokens | total_cost | metadata (JSONB) |
archived | created_at | updated_at
```

#### `agents`
Managed agents created by orchestrator
```sql
id (UUID) | orchestrator_agent_id (UUID) | name | model | system_prompt |
working_dir | git_worktree | status | session_id | adw_id | adw_step |
input_tokens | output_tokens | total_cost | metadata (JSONB) | archived |
created_at | updated_at
```

#### `agent_logs`
Unified event log for hooks and responses
```sql
id (UUID) | agent_id (UUID) | session_id | task_slug | adw_id | adw_step |
entry_index | event_category (hook|response) | event_type | content |
payload (JSONB) | summary | timestamp
```

#### `system_logs`
Application-level system events
```sql
id (UUID) | file_path | adw_id | adw_step | level | message | summary |
metadata (JSONB) | timestamp
```

#### `orchestrator_chat`
3-way conversation log (user ↔ orchestrator ↔ agents)
```sql
id (UUID) | orchestrator_agent_id (UUID) | sender_type | receiver_type |
message | summary | agent_id (UUID, nullable) | metadata (JSONB) |
created_at | updated_at
```

#### `prompts`
User/orchestrator prompts sent to agents
```sql
id (UUID) | agent_id (UUID, nullable) | task_slug | author (engineer|orchestrator_agent) |
prompt_text | summary | timestamp | session_id
```

---

## Request/Response Flow

### Example: Send Chat Message

```
1. Frontend: POST /send_chat
   └─> SendChatRequest { message, orchestrator_agent_id }

2. main.py:send_chat()
   └─> asyncio.create_task(service.process_user_message())
   └─> Returns immediately with "processing" status

3. OrchestratorService.process_user_message()
   ├─> Log user message to orchestrator_chat table
   ├─> Create Claude SDK client with options
   ├─> Call client.interact() with user message
   └─> Process response in streaming mode

4. Claude SDK Execution
   ├─> PreToolUse hook → Log to agent_logs, Broadcast via WS
   ├─> Tool execution → Management tools from AgentManager
   ├─> PostToolUse hook → Log to agent_logs, Broadcast via WS
   ├─> Response blocks → Log TextBlock, ThinkingBlock, ToolUseBlock
   └─> Stop hook → Finalize execution

5. WebSocket Broadcasting
   ├─> agent_log events as they occur
   ├─> thinking blocks with full thinking text
   ├─> tool use blocks with inputs/results
   ├─> chat_stream chunks for text responses
   └─> orchestrator_updated with final costs

6. Frontend: Receives all events in real-time
   └─> Updates event stream, costs, agent status
```

---

## State Management & Lifecycle

### Application Lifecycle

```
Startup:
1. Parse CLI args (--session, --cwd)
2. Initialize config from .env
3. Load logging system
4. Initialize database connection pool
5. Get or create orchestrator
6. Initialize agent manager
7. Initialize orchestrator service
8. Store in app.state for endpoint access

Server Running:
- REST endpoints process requests
- WebSocket receives/broadcasts events
- Background tasks execute agents
- Database persists all activity
- Logs rotate hourly

Shutdown:
1. Close database pool
2. Log shutdown event
3. Flush all log files
```

### Orchestrator State

```
Orchestrator States:
- idle: Waiting for user input
- executing: Processing user message
- waiting: Waiting for tool results
- blocked: Cannot proceed (error)
- complete: Execution finished

Session ID Lifecycle:
- NULL on creation (new orchestrator)
- Set on first interaction (Claude SDK creates)
- Persisted for resumption
- Never overwritten (UNIQUE constraint)
```

---

## Module Dependencies Graph

```
main.py (FastAPI entry)
├─ config (Configuration)
├─ logger (Logging)
├─ database (Data access)
│  └─ orch_database_models (Type models)
├─ websocket_manager (Real-time events)
├─ orchestrator_service (Business logic)
│  ├─ database
│  ├─ websocket_manager
│  ├─ agent_manager
│  ├─ orchestrator_hooks
│  ├─ subagent_loader (Template discovery)
│  ├─ config
│  └─ Claude SDK
└─ agent_manager (Agent lifecycle)
   ├─ database
   ├─ websocket_manager
   ├─ command_agent_hooks
   ├─ file_tracker
   ├─ subagent_loader
   ├─ logger
   └─ Claude SDK

Hook modules:
├─ hooks.py (Generic hooks)
├─ command_agent_hooks.py (Agent-specific)
├─ orchestrator_hooks.py (Orchestrator-specific)
└─ Database + WebSocket for logging

Utilities:
├─ slash_command_parser (CLI discovery)
├─ subagent_models (Template types)
├─ single_agent_prompt (Event summarization)
├─ file_tracker (Change detection)
└─ event_summarizer (Summary generation)
```

---

## Key Design Patterns

### 1. **Singleton Pattern**
- WebSocket Manager: Single global instance
- Logger: Single global instance
- Database Pool: Single global connection pool
- Orchestrator: Single active orchestrator (multiple sessions possible)

### 2. **Service Layer Pattern**
- OrchestratorService abstracts Claude SDK operations
- AgentManager abstracts agent lifecycle
- Database module abstracts SQL operations

### 3. **Hook-based Event Capture**
- Claude SDK hooks capture all events
- Hooks log to database AND broadcast via WebSocket
- Async summarization runs in background

### 4. **Streaming/Real-time Pattern**
- WebSocket manager broadcasts all events
- Text responses streamed in chunks
- Thinking blocks sent as they occur
- Tool use blocks sent with results

### 5. **Registry Pattern**
- SubagentRegistry caches templates
- SlashCommand parser caches discovered commands
- Prevents repeated file I/O

### 6. **Context Manager Pattern**
- Database connections managed via context manager
- Ensures proper cleanup
- Used throughout for resource management

### 7. **Factory Pattern**
- Hook factory functions create closures
- Bind specific agent context to hooks
- Support multiple concurrent agents

---

## Performance Considerations

### Database
- Connection pooling (5-20 connections)
- Async queries with asyncpg
- Batch operations where possible
- JSONB for flexible metadata

### WebSocket
- Non-blocking broadcast to all clients
- Automatic disconnection cleanup
- Per-client metadata tracking

### Logging
- Hourly log rotation (prevents huge files)
- Rich console formatting (async)
- File I/O in separate handler

### Background Tasks
- Agent execution in threads
- Summarization async tasks
- No blocking in main loop

---

## Error Handling

**Key Principle**: Never silently fail - always raise and log

```python
# Pattern used throughout:
try:
    # Operation
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise  # Always re-raise
```

**Error Propagation**:
- Database errors → HTTP 500
- Missing resources → HTTP 404
- Validation errors → HTTP 400
- Business logic errors → HTTP 500 with detail

---

## Environment Variables Reference

```bash
# Server Ports
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9403
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175

# Database
DATABASE_URL=postgresql://user:pass@host/db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs

# CORS
CORS_ORIGINS=http://127.0.0.1:5175

# Models
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
DEFAULT_AGENT_MODEL=claude-sonnet-4-5-20250929

# Paths
ORCHESTRATOR_SYSTEM_PROMPT_PATH=backend/prompts/orchestrator_agent_system_prompt.md
AGENT_SYSTEM_PROMPT_TEMPLATE_PATH=backend/prompts/managed_agent_system_prompt_template.md
ORCHESTRATOR_WORKING_DIR=/path/to/project

# IDE Integration
IDE_COMMAND=code
IDE_ENABLED=true

# Limits
MAX_AGENT_TURNS=500
DEFAULT_AGENT_LOG_LIMIT=50
DEFAULT_SYSTEM_LOG_LIMIT=50
DEFAULT_CHAT_HISTORY_LIMIT=300
```

---

## Testing Strategy

The backend uses **real database connections** (no mocking):
- Tests create ephemeral test data
- Database state reset after each test
- Tests verify complete flow end-to-end
- Location: `backend/tests/`

---

## Module Interdependencies Matrix

| Module | Config | Logger | DB | WebSocket | Service | AgentMgr | Hooks | SDK |
|--------|--------|--------|----|-----------|---------|---------|----|-----|
| main.py | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| config.py | - | - | - | - | - | - | - | - |
| logger.py | - | - | - | - | - | - | - | - |
| database.py | - | ✓ | - | - | - | - | - | - |
| websocket_manager | - | ✓ | - | - | - | - | - | - |
| orchestrator_service | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| agent_manager | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ |
| hooks.py | - | ✓ | ✓ | ✓ | - | - | - | ✓ |
| slash_command_parser | - | - | - | - | - | - | - | - |
| subagent_loader | - | ✓ | - | - | - | - | - | - |
