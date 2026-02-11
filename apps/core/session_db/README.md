# Session Database

SQLModel-based database for tracking session workflows and agent execution in LAI Claude Code Config.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CODEBASE (Files)                                  │
│                                                                             │
│   agents/sessions/{session_slug}/                                           │
│   ├── state.json     ← Session phase, status (quick reads)                  │
│   ├── spec.md        ← What we're building (agent writes)                   │
│   ├── plan.json      ← How we're building it (agent writes)                 │
│   └── research/      ← Research artifacts                                   │
│                                                                             │
│   SOURCE OF TRUTH for: Work artifacts that agents read/write                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ synced/referenced
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE (PostgreSQL)                             │
│                                                                             │
│   sessions           ← Workflow tracking, quick queries                     │
│   agents             ← Agent instances, SDK session IDs for resume          │
│   agent_logs         ← All hook events, observability                       │
│                                                                             │
│   SOURCE OF TRUTH for: Execution events, timing, costs, agent state         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd apps/session_db
uv sync
```

## Usage

### Initialize the Database

```python
from session_db.database import init_db

# Create all tables
await init_db()
```

### Create a Session

```python
from session_db.database import get_async_session
from session_db.crud import create_session
from session_db.models import SessionCreate

async with get_async_session() as db:
    session = await create_session(db, SessionCreate(
        session_slug="2026-01-15_auth-feature",
        title="Implement Authentication",
        working_dir="/path/to/project",
        session_type="full",
    ))
```

### Create an Agent

```python
from session_db.crud import create_agent
from session_db.models import AgentCreate

async with get_async_session() as db:
    agent = await create_agent(db, AgentCreate(
        session_id=session.id,
        agent_type="spec",
        model="claude-sonnet-4-5-20250929",
        model_alias="sonnet",
    ))
```

### Store SDK Session ID (for resumption)

```python
from session_db.crud import update_agent
from session_db.models import AgentUpdate

# After receiving init message from SDK
async with get_async_session() as db:
    await update_agent(db, agent.id, AgentUpdate(
        sdk_session_id="sess_abc123",  # From SDK init message
        status="executing",
        started_at=datetime.utcnow(),
    ))
```

### Log Events

```python
from session_db.crud import create_agent_log
from session_db.models import AgentLogCreate

async with get_async_session() as db:
    await create_agent_log(db, AgentLogCreate(
        agent_id=agent.id,
        session_id=session.id,
        event_category="hook",
        event_type="PreToolUse",
        tool_name="Read",
        tool_input={"file_path": "/src/auth.py"},
    ))
```

## Migrations with Alembic

### Generate a Migration

```bash
cd apps/session_db
uv run alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
uv run alembic upgrade head
```

### Rollback

```bash
uv run alembic downgrade -1
```

## Models

### Session

Workflow container for the spec → plan → build → docs lifecycle.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `session_slug` | str | Folder name (e.g., '2026-01-15_auth-feature') |
| `status` | str | Workflow phase: created, spec, plan, build, docs, complete, failed |
| `session_type` | str | full, quick, or research |
| `working_dir` | str | Absolute path to project root |
| `total_cost` | float | Aggregated cost across all agents |

### Agent

Individual agent invocation within a session.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key to sessions |
| `agent_type` | str | spec, plan, build, research, docs, debug |
| `sdk_session_id` | str | Claude SDK session ID for resumption |
| `model` | str | Claude model ID |
| `status` | str | pending, executing, complete, failed |
| `checkpoint_id` | int | Checkpoint number (for build agents) |

### AgentLog

Execution events for observability.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `agent_id` | UUID | Foreign key to agents |
| `session_id` | UUID | Foreign key to sessions (denormalized) |
| `event_category` | str | hook, response, or phase |
| `event_type` | str | PreToolUse, TextBlock, etc. |
| `tool_name` | str | Tool name for tool events |
| `payload` | JSON | Full event data |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SESSION_DB_URL` | PostgreSQL database URL | `postgresql+asyncpg://localhost/session_db` |

Create a `.env` file in the `apps/session_db/` directory:

```bash
SESSION_DB_URL=postgresql+asyncpg://user:password@localhost:5432/session_db
```

## Development

### Run Tests

```bash
cd apps/session_db
uv run pytest
```

### Reset Database

```python
from session_db.database import reset_db

await reset_db()  # WARNING: Deletes all data!
```
