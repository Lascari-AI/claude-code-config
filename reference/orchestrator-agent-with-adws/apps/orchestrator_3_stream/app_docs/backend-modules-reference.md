# Backend Modules Reference Guide

## Module Specification Table

| Module | File | LOC | Purpose | Key Responsibilities | Main Classes/Functions | Key Dependencies |
|--------|------|-----|---------|---------------------|----------------------|------------------|
| **FastAPI App** | `main.py` | 646 | Application entry point and HTTP routing | Initialize app, manage lifecycle, define REST/WS endpoints, orchestrator initialization | FastAPI app, lifespan context manager, route handlers | config, logger, database, websocket_manager, orchestrator_service, agent_manager |
| **Configuration** | `modules/config.py` | 197 | Environment variable loading and runtime settings | Load .env file, manage working directory, provide configuration constants | `set_working_dir()`, `get_working_dir()`, config variables | python-dotenv, os, pathlib |
| **Logging** | `modules/logger.py` | 182 | Dual-output logging (console + hourly files) | Log to console with Rich formatting and hourly-rotating files | `OrchestratorLogger`, `HourlyRotatingFileHandler` | logging, rich, pathlib |
| **Database** | `modules/database.py` | 1600 | asyncpg connection pool and data operations | Manage connection pool, CRUD operations for all tables | `init_pool()`, `get_connection()`, agent/orchestrator/chat operations, hook logging | asyncpg, uuid, json, config |
| **Database Models** | `modules/orch_database_models.py` | 344 | Pydantic models for all database entities | Type-safe models with UUID/JSON conversion, validation | `OrchestratorAgent`, `Agent`, `Prompt`, `AgentLog`, `SystemLog`, `OrchestratorChat` | pydantic, datetime, uuid, decimal |
| **WebSocket Manager** | `modules/websocket_manager.py` | 257 | WebSocket connection management and broadcasting | Accept/disconnect clients, broadcast events to all clients | `WebSocketManager`, connection metadata tracking, broadcast methods | fastapi, typing, json, logger |
| **Orchestrator Service** | `modules/orchestrator_service.py` | 1009 | Business logic for orchestrator agent execution | Process user messages, execute Claude SDK, manage session/costs, stream responses | `OrchestratorService`, orchestrator tools, hook building | Claude SDK, database, websocket_manager, orchestrator_hooks, subagent_loader |
| **Agent Manager** | `modules/agent_manager.py` | 1397 | Agent lifecycle management and tool registration | Create agents, execute agents, register management tools, background threading | `AgentManager`, 8 management tools (@tool decorated), agent execution | database, Claude SDK, websocket_manager, command_agent_hooks, file_tracker, subagent_loader |
| **Hooks (Generic)** | `modules/hooks.py` | 556 | Claude SDK event hook implementations | Capture hooks, log to database, broadcast, spawn summarization | Hook factory functions: `create_*_hook()`, `_summarize_and_update()` | database, websocket_manager, logger, single_agent_prompt |
| **Orchestrator Hooks** | `modules/orchestrator_hooks.py` | 168 | Orchestrator-specific event hooks | Capture orchestrator tool usage and events | `create_orchestrator_pre_tool_hook()`, `create_orchestrator_post_tool_hook()`, `create_orchestrator_stop_hook()` | logger, websocket_manager, database |
| **Command Agent Hooks** | `modules/command_agent_hooks.py` | 629 | Agent command-specific hooks | Track agent tool usage and file changes | `create_pre_tool_hook()`, `create_post_tool_hook()`, `create_user_prompt_hook()`, `create_stop_hook()`, file tracking | database, websocket_manager, logger, file_tracker |
| **Slash Command Parser** | `modules/slash_command_parser.py` | 267 | Parse and discover slash commands | Scan `.claude/commands/`, parse YAML frontmatter, extract metadata | `SlashCommandFrontmatter`, `parse_slash_command_file()`, `discover_slash_commands()` | pathlib, yaml, pydantic, regex |
| **Subagent Loader** | `modules/subagent_loader.py` | 220 | Discover and cache subagent templates | Scan `.claude/agents/`, parse templates, registry pattern | `SubagentRegistry`, `parse_subagent_file()` | pathlib, yaml, logger, subagent_models |
| **Subagent Models** | `modules/subagent_models.py` | 75 | Pydantic models for subagent templates | Type-safe template metadata | `SubagentFrontmatter`, `SubagentTemplate` | pydantic, pathlib |
| **Event Summarizer** | `modules/event_summarizer.py` | 15 | AI-powered event summarization (stub) | Placeholder for event summarization logic | - | - |
| **Single Agent Prompt** | `modules/single_agent_prompt.py` | 285 | Individual event summarization utility | Summarize single events using Claude | `summarize_event()` | logger |
| **File Tracker** | `modules/file_tracker.py` | 285 | File change detection during execution | Track new/modified files for reporting | `FileTracker` | pathlib, logger |

---

## Module Dependency Matrix (✓ = imports)

| From / To | config | logger | db | models | ws | orch_svc | agent_mgr | hooks | cmd_hooks | orch_hooks | cmd_parser | subagent | subagent_models | single_agent | file_track | event_sum |
|-----------|--------|--------|----|---------|----|----------|-----------|-------|-----------|------------|------------|---------|---------------|-----------|-----------|----------|
| **main.py** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | ✓ | - | - | - | - | - |
| **config** | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **logger** | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **database** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **models** | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **ws_manager** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **orch_service** | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ | - | - | ✓ | - | ✓ | - | - | - | - |
| **agent_mgr** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | ✓ | - | - | ✓ | - | - | ✓ | - |
| **hooks** | - | ✓ | ✓ | - | ✓ | - | - | - | - | - | - | - | - | ✓ | - | - |
| **cmd_hooks** | - | ✓ | ✓ | - | ✓ | - | - | - | - | - | - | - | - | - | ✓ | - |
| **orch_hooks** | - | ✓ | ✓ | - | ✓ | - | - | - | - | - | - | - | - | - | - | - |
| **cmd_parser** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **subagent** | - | ✓ | - | - | - | - | - | - | - | - | - | - | ✓ | - | - | - |
| **subagent_models** | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **single_agent** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **file_track** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **event_sum** | - | ✓ | - | - | - | - | - | - | - | - | - | - | - | - | - | - |

---

## API Endpoints Reference

### Health & Information
| Method | Path | Purpose | Returns | Parameters |
|--------|------|---------|---------|-----------|
| GET | `/health` | Health check | `{status, service, websocket_connections}` | - |
| GET | `/get_orchestrator` | Get orchestrator metadata | Orchestrator data + slash commands + templates | - |
| GET | `/get_headers` | Get working directory | `{cwd}` | - |

### Chat Management
| Method | Path | Purpose | Request Body | Returns |
|--------|------|---------|--------------|---------|
| POST | `/send_chat` | Send user message | `{message, orchestrator_agent_id}` | `{status, message}` |
| POST | `/load_chat` | Load chat history | `{orchestrator_agent_id, limit?}` | `{messages, turn_count}` |

### Data Retrieval
| Method | Path | Purpose | Query Parameters | Returns |
|--------|------|---------|-----------------|---------|
| GET | `/get_events` | Unified event log | `agent_id?, task_slug?, event_types?, limit?, offset?` | `{events, count}` |
| GET | `/list_agents` | List active agents | - | `{agents}` |

### IDE Integration
| Method | Path | Purpose | Request Body | Returns |
|--------|------|---------|--------------|---------|
| POST | `/api/open-file` | Open file in IDE | `{file_path}` | `{status, message}` |

### Real-time
| Protocol | Path | Purpose | Message Types |
|----------|------|---------|---------------|
| WebSocket | `/ws` | Real-time event streaming | agent_log, chat_message, orchestrator_updated, etc. |

---

## Database Tables Overview

### orchestrator_agents
```sql
Singleton orchestrator agent that manages other agents

Columns:
- id (UUID, PK)
- session_id (TEXT, UNIQUE, nullable) - Claude SDK session
- system_prompt (TEXT)
- status (idle|executing|waiting|blocked|complete)
- working_dir (TEXT)
- input_tokens (INTEGER) - Cumulative
- output_tokens (INTEGER) - Cumulative
- total_cost (DECIMAL)
- metadata (JSONB) - Custom fields, system_message_info
- archived (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Key Operations:
- get_orchestrator() - Get active (non-archived)
- get_orchestrator_by_session(id) - Resume session
- create_new_orchestrator() - Fresh start
- update_orchestrator_session() - Set session (once)
- update_orchestrator_costs() - Increment tokens/cost
- update_orchestrator_metadata() - Merge JSONB
```

### agents
```sql
Managed agents created by orchestrator

Columns:
- id (UUID, PK)
- orchestrator_agent_id (UUID, FK) - Parent orchestrator
- name (TEXT) - User-friendly name
- model (TEXT) - Claude model variant
- system_prompt (TEXT)
- working_dir (TEXT)
- git_worktree (TEXT, nullable)
- status (idle|executing|waiting|blocked|complete)
- session_id (TEXT, nullable) - Claude SDK session
- adw_id, adw_step (nullable) - ADW tracking
- input_tokens, output_tokens, total_cost (tracking)
- metadata (JSONB)
- archived (BOOLEAN)
- created_at, updated_at (TIMESTAMP)

Key Operations:
- create_agent() - Create new managed agent
- list_agents() - List active agents for orchestrator
- get_agent() - Get by ID
- get_agent_by_name() - Get by name (scoped to orchestrator)
- update_agent_status() - Change status
- update_agent_costs() - Increment tokens/cost
- delete_agent() - Archive agent
```

### agent_logs
```sql
Unified event log for hooks and agent responses

Columns:
- id (UUID, PK)
- agent_id (UUID, FK)
- session_id (TEXT, nullable)
- task_slug (TEXT, nullable) - Task identifier
- adw_id, adw_step (nullable) - ADW tracking
- entry_index (INTEGER) - Sequence number
- event_category (hook|response) - Event source
- event_type (TEXT) - PreToolUse, PostToolUse, etc.
- content (TEXT) - Human-readable summary
- payload (JSONB) - Detailed event data
- summary (TEXT) - AI-generated summary
- timestamp (TIMESTAMP)

Event Types:
- Hook: PreToolUse, PostToolUse, UserPromptSubmit, Stop
- Response: TextBlock, ThinkingBlock, ToolUseBlock

Key Operations:
- insert_hook_event() - Log hook event
- insert_message_block() - Log response block
- list_agent_logs() - Retrieve for agent
- get_agent_logs() - Filtered query
- update_log_summary() - Update AI summary
```

### orchestrator_chat
```sql
3-way conversation log: user ↔ orchestrator ↔ agents

Columns:
- id (UUID, PK)
- orchestrator_agent_id (UUID, FK)
- sender_type (user|orchestrator|agent)
- receiver_type (user|orchestrator|agent)
- message (TEXT) - Message content
- summary (TEXT) - AI summary
- agent_id (UUID, FK, nullable) - If agent involved
- metadata (JSONB)
- created_at, updated_at (TIMESTAMP)

Key Operations:
- insert_chat_message() - Log chat
- list_orchestrator_chat() - Retrieve for orchestrator
- get_chat_history() - Load with merging
- update_chat_summary() - Update AI summary
```

### prompts
```sql
Prompts sent to agents from engineers or orchestrator

Columns:
- id (UUID, PK)
- agent_id (UUID, FK, nullable)
- task_slug (TEXT, nullable)
- author (engineer|orchestrator_agent)
- prompt_text (TEXT)
- summary (TEXT)
- timestamp (TIMESTAMP)
- session_id (TEXT, nullable)

Key Operations:
- insert_prompt() - Log prompt
- update_prompt_summary() - Update AI summary
```

### system_logs
```sql
Application-level system events (not agent-specific)

Columns:
- id (UUID, PK)
- file_path (TEXT, nullable)
- adw_id, adw_step (nullable)
- level (DEBUG|INFO|WARNING|ERROR)
- message (TEXT)
- summary (TEXT)
- metadata (JSONB)
- timestamp (TIMESTAMP)

Key Operations:
- insert_system_log() - Log system event
- list_system_logs() - Retrieve logs
- update_system_log_summary() - Update AI summary
```

---

## Configuration Variables Reference

### Server Configuration
```python
BACKEND_HOST        = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT        = int(os.getenv("BACKEND_PORT", "9403"))
FRONTEND_HOST       = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT       = int(os.getenv("FRONTEND_PORT", "5175"))
BACKEND_URL         = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL        = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
WEBSOCKET_URL       = os.getenv("WEBSOCKET_URL", f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws")
```

### Database Configuration
```python
DATABASE_URL        = os.getenv("DATABASE_URL", "postgresql://localhost:5432/orchestrator")
DATABASE_POOL_SIZE  = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
```

### Logging Configuration
```python
LOG_LEVEL           = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR             = Path(os.getenv("LOG_DIR", "backend/logs"))
```

### CORS Configuration
```python
CORS_ORIGINS        = os.getenv("CORS_ORIGINS", f"http://{FRONTEND_HOST}:{FRONTEND_PORT}").split(",")
```

### Model Configuration
```python
DEFAULT_MODEL       = "claude-sonnet-4-5-20250929"
FAST_MODEL          = "claude-haiku-4-5-20251001"
ORCHESTRATOR_MODEL  = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)
DEFAULT_AGENT_MODEL = os.getenv("DEFAULT_AGENT_MODEL", DEFAULT_MODEL)
AVAILABLE_MODELS    = ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"]
```

### Path Configuration
```python
PROJECT_ROOT        = Path(__file__).parent.parent.parent  # orchestrator_3_stream/
BACKEND_DIR         = Path(__file__).parent.parent.resolve()
DEFAULT_CODEBASE_PATH = str(BACKEND_DIR.parent.parent.parent)
ORCHESTRATOR_WORKING_DIR = os.getenv("ORCHESTRATOR_WORKING_DIR", DEFAULT_CODEBASE_PATH)
ORCHESTRATOR_SYSTEM_PROMPT_PATH = str(BACKEND_DIR / "prompts" / "orchestrator_agent_system_prompt.md")
AGENT_SYSTEM_PROMPT_TEMPLATE_PATH = str(BACKEND_DIR / "prompts" / "managed_agent_system_prompt_template.md")
```

### Runtime Configuration
```python
MAX_AGENT_TURNS     = int(os.getenv("MAX_AGENT_TURNS", "500"))
DEFAULT_AGENT_LOG_LIMIT = int(os.getenv("DEFAULT_AGENT_LOG_LIMIT", "50"))
DEFAULT_SYSTEM_LOG_LIMIT = int(os.getenv("DEFAULT_SYSTEM_LOG_LIMIT", "50"))
DEFAULT_CHAT_HISTORY_LIMIT = int(os.getenv("DEFAULT_CHAT_HISTORY_LIMIT", "300"))
```

### IDE Integration
```python
IDE_COMMAND         = os.getenv("IDE_COMMAND", "code")
IDE_ENABLED         = os.getenv("IDE_ENABLED", "true").lower() in ["true", "1", "yes"]
```

### Working Directory (Runtime Override)
```python
def set_working_dir(path: str) -> None:
    """Override working directory at runtime (--cwd flag)"""
    global _current_working_dir
    _current_working_dir = path

def get_working_dir() -> str:
    """Get current working directory (with --cwd override)"""
    return _current_working_dir
```

---

## Claude SDK Integration Points

### Option Configuration
```python
ClaudeAgentOptions(
    system_prompt=str,           # From database
    model=str,                   # From config
    cwd=str,                     # Working directory
    resume=str,                  # Session ID for resumption
    env=dict,                    # API key forwarding
    hooks=dict,                  # Event hooks (Pre/PostToolUse, Stop)
    mcp_servers=dict,            # Management tools MCP server
    allowed_tools=list,          # Tool whitelist
    setting_sources=list         # ["project"] for CLAUDE.md
)
```

### Hook Integration
```python
hooks = {
    "PreToolUse": [{"hooks": [create_orchestrator_pre_tool_hook(...)]}],
    "PostToolUse": [{"hooks": [create_orchestrator_post_tool_hook(...)]}],
    "Stop": [{"hooks": [create_orchestrator_stop_hook(...)]}],
}
```

### Management Tools (via MCP)
```python
@tool("create_agent", "Description", {"param": type})
async def create_agent_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tool implementation"""
    return {"content": [{"type": "text", "text": "Result"}]}

# Tools exposed:
- create_agent
- list_agents
- command_agent
- check_agent_status
- delete_agent
- interrupt_agent
- read_system_logs
- report_cost
```

---

## Error Handling Patterns

### Pattern Used Throughout Codebase
```python
try:
    # Operation
    result = await some_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise  # Always re-raise
```

### HTTP Error Responses
```python
# HTTP 400 - Bad Request
raise HTTPException(status_code=400, detail="Validation failed")

# HTTP 404 - Not Found
raise HTTPException(status_code=404, detail="Orchestrator not found")

# HTTP 500 - Internal Server Error
raise HTTPException(status_code=500, detail=str(e))
```

### WebSocket Error Broadcasting
```python
await ws_manager.broadcast_error(
    error_message="Operation failed",
    details={"code": "OPERATION_ERROR", "info": "..."}
)
```

---

## Testing Strategy

### Test Organization
- Location: `backend/tests/`
- Files: `test_database.py`, `test_websocket_raw.py`, `test_agent_events.py`, `test_display.py`
- Runner: `uv run pytest`

### Key Principles
- **Real Database**: Use actual PostgreSQL (ephemeral connections)
- **No Mocks**: Real Claude SDK agents when testing
- **Cleanup**: Delete test data after each test
- **State Reset**: Database returns to original state

### Test Patterns
```python
# Create test data
async def test_example():
    # 1. Create test data
    orch = await create_new_orchestrator(...)

    # 2. Test operation
    result = await get_orchestrator_by_id(orch.id)

    # 3. Assert
    assert result.id == orch.id

    # 4. Cleanup
    await delete_orchestrator(orch.id)  # Clean up
```

---

## Best Practices & Conventions

### 1. **Always Use Async/Await**
```python
# ✓ Correct
async def fetch_data():
    return await database.get_orchestrator()

# ✗ Wrong
def fetch_data():
    return database.get_orchestrator()  # Can't await
```

### 2. **Use Pydantic Models for Validation**
```python
# ✓ Correct
class SendChatRequest(BaseModel):
    message: str
    orchestrator_agent_id: str

# ✗ Wrong
def send_chat(request_dict):
    message = request_dict.get("message")  # No validation
```

### 3. **Log Errors Before Raising**
```python
# ✓ Correct
try:
    operation()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise

# ✗ Wrong
try:
    operation()
except Exception:
    raise  # Silent failure
```

### 4. **Use Context Managers for Resources**
```python
# ✓ Correct
async with database.get_connection() as conn:
    result = await conn.fetchrow(...)

# ✗ Wrong
conn = await pool.acquire()
result = await conn.fetchrow(...)
# Might forget to release
```

### 5. **Always Broadcast WebSocket Events**
```python
# ✓ Correct
await ws_manager.broadcast_agent_log(event_data)

# ✗ Wrong
# Log to DB but don't notify frontend
await database.insert_agent_log(event_data)
```

### 6. **UUID Handling**
```python
# ✓ Correct - Pydantic converts automatically
agent = Agent(**database_row)
print(agent.id)  # UUID object

# ✗ Wrong
agent_id = database_row["id"]  # Might be asyncpg UUID
str(agent_id)  # Need explicit conversion
```

---

## Performance Notes

### Database Performance
- **Connection pooling**: Min 5, Max 20 connections
- **Async queries**: All I/O is non-blocking with asyncpg
- **JSONB**: Efficient for metadata (supports indexing)
- **Batch operations**: Group inserts when possible

### WebSocket Scaling
- Broadcasts to all connected clients simultaneously
- Connection cleanup on disconnection
- No server-side message queuing (real-time only)

### Logging Performance
- Hourly rotation prevents massive files
- Console Rich output runs async
- File I/O in separate handler thread

### Memory Usage
- Hook closures capture context (agent_id, task_slug)
- WebSocket manager holds all active connections
- Database pool holds max 20 connections
- Caching: SubagentRegistry, SlashCommand parser

---

## Security Considerations

### Environment Variables
- Database credentials via `DATABASE_URL`
- API key forwarding to subprocess: `ANTHROPIC_API_KEY`
- Never hardcode secrets

### CORS
- Configured via `CORS_ORIGINS` environment variable
- Defaults to frontend URL from config
- All origins allowed if misconfigured (not recommended)

### SQL Injection
- **asyncpg parameterized queries**: All SQL uses `$1, $2` placeholders
- User input never concatenated into SQL

### File Operations
- IDE file opening: Path validation before execution
- Template loading: Restricted to `.claude/` directories
- Log files: Write-only access

---

## Integration Checklist

- [ ] Environment variables configured (.env file)
- [ ] PostgreSQL database accessible and initialized
- [ ] Claude API key available (ANTHROPIC_API_KEY)
- [ ] Backend port available (default 9403)
- [ ] Frontend port available (default 5175)
- [ ] Log directory writable (default `backend/logs/`)
- [ ] Working directory specified (--cwd flag or config)
- [ ] `.claude/agents/` directory exists for templates
- [ ] `.claude/commands/` directory exists for slash commands
- [ ] System prompt file at configured path

