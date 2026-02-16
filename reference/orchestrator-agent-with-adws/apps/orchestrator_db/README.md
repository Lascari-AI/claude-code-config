# Orchestrator Database Schema & Models

Central database schema and model definitions for the Multi-Agent Orchestration system.

## 📁 Directory Structure

```
apps/orchestrator_db/
├── migrations/              # Idempotent SQL migration files
│   ├── 0_orchestrator_agents.sql
│   ├── 1_agents.sql
│   ├── 2_prompts.sql
│   ├── 3_agent_logs.sql
│   ├── 4_system_logs.sql
│   ├── 5_indexes.sql
│   ├── 6_functions.sql
│   ├── 7_triggers.sql
│   └── README.md            # Migration system documentation
├── models.py                # Pydantic models (source of truth)
├── run_migrations.py        # Migration runner script
├── sync_models.py           # Model synchronization script
└── README.md                # This file
```

## 🎯 Purpose

This directory serves as the **single source of truth** for:

1. **Database Schema** - PostgreSQL table definitions (via migrations)
2. **Data Models** - Pydantic models for type-safe database operations
3. **Model Distribution** - Syncing models to orchestrator apps

## 🚀 Quick Start

### Apply Database Schema

Run all migrations to set up or update the database:

```bash
uv run apps/orchestrator_db/run_migrations.py
```

This will:
- ✅ Create all 5 tables (orchestrator_agents, agents, prompts, agent_logs, system_logs)
- ✅ Add performance indexes
- ✅ Set up trigger functions for auto-timestamps
- ✅ Preserve existing data (idempotent operations)

### Sync Models to Apps

After modifying `models.py`, sync to both orchestrator apps:

```bash
python apps/orchestrator_db/sync_models.py
```

This copies models to:
- `apps/orchestrator_1_term/modules/orch_database_models.py`
- `apps/orchestrator_2_stream/server/models.py`

## 📋 Files Explained

### `models.py` - Pydantic Models

**Purpose:** Central definition of all database models with automatic type conversion.

**Models:**
- `OrchestratorAgent` - Singleton orchestrator that manages other agents
- `Agent` - Managed agent registry with status and usage tracking
- `Prompt` - Prompt history from engineers or orchestrator
- `AgentLog` - Unified event log (hooks + responses)
- `SystemLog` - Application-level system logs

**Features:**
- Automatic UUID conversion (handles asyncpg UUID objects)
- JSON field parsing (metadata, payload)
- Decimal to float conversion for costs
- Type validation with Pydantic

**Usage:**
```python
from models import Agent, OrchestratorAgent, Prompt, AgentLog, SystemLog

# Automatically handles UUID conversion from database
agent = Agent(**row_dict)
print(agent.id)  # Works with both UUID objects and strings
```

### `migrations/` - Database Schema

**Purpose:** Ordered, idempotent SQL migrations that preserve data.

**Why This Approach:**
- ✅ **No Data Loss** - Uses `CREATE IF NOT EXISTS` instead of `DROP TABLE`
- ✅ **Modularity** - One file per concern
- ✅ **Clear Dependencies** - Numbered by creation order (0-7)
- ✅ **Idempotent** - Safe to run multiple times
- ✅ **Production Ready** - Follows industry best practices

**Order of Execution:**
1. `0_orchestrator_agents.sql` - Singleton orchestrator (no dependencies)
2. `1_agents.sql` - Managed agents (no dependencies)
3. `2_prompts.sql` - Prompt history (FK → agents)
4. `3_agent_logs.sql` - Event logs (FK → agents)
5. `4_system_logs.sql` - System logs (nullable FK → agents)
6. `5_indexes.sql` - Performance indexes (all tables)
7. `6_functions.sql` - Trigger functions (for auto-timestamps)
8. `7_triggers.sql` - Auto-update triggers

**See:** `migrations/README.md` for detailed migration documentation.

### `run_migrations.py` - Migration Runner

**Purpose:** Execute all migrations in order with rich terminal output.

**Features:**
- Rich progress tracking with spinners
- Colorized output (green ✓ / red ✗)
- Summary table of created schema
- Error reporting with details
- Loads DATABASE_URL from root `.env`

**Requirements:**
- psql command-line tool installed
- DATABASE_URL in root `.env` file
- Python 3.12+

### `sync_models.py` - Model Sync Script

**Purpose:** Copy `models.py` to both orchestrator applications.

**Why:**
- Maintains single source of truth
- Prevents model drift between apps
- Simplifies updates (change once, sync everywhere)

**When to Run:**
- After modifying any Pydantic model in `models.py`
- After adding new models
- After changing field types or validators

## 🗄️ Database Schema

### Tables

| Table                | Purpose                           | Key Relationships   |
| -------------------- | --------------------------------- | ------------------- |
| `orchestrator_agents`| Singleton orchestrator agent      | None                |
| `agents`             | Managed agent registry            | None                |
| `prompts`            | Prompt history                    | FK → agents         |
| `agent_logs`         | Event logs (hooks + responses)    | FK → agents         |
| `system_logs`        | Application logs                  | Nullable FK → agents|

### Indexes

36 total indexes for query performance:
- Status indexes for filtering active agents
- Timestamp indexes for chronological queries
- Foreign key indexes for join performance
- Partial indexes for nullable columns

### Triggers

Auto-update `updated_at` timestamps:
- `orchestrator_agents` - Updates on any row change
- `agents` - Updates on any row change

## 🔧 Common Tasks

### Modify a Table

1. Edit the appropriate migration file in `migrations/`
2. If adding columns, use `ALTER TABLE ADD COLUMN IF NOT EXISTS`
3. Run migrations: `uv run apps/orchestrator_db/run_migrations.py`

**IMPORTANT: Never use `DROP TABLE` in migration files!**
- Migration files must be idempotent and non-destructive
- Use `CREATE TABLE IF NOT EXISTS` instead
- To drop tables, use the dedicated `drop_table.py` utility (see below)

### Add a New Table

1. Create `8_new_table.sql` in `migrations/`
2. Use `CREATE TABLE IF NOT EXISTS`
3. Consider dependencies (foreign keys)
4. Update `run_migrations.py` MIGRATIONS list
5. Run migrations

### Update Pydantic Models

1. Edit `models.py`
2. Add/modify model classes
3. Sync to apps: `python apps/orchestrator_db/sync_models.py`
4. Update database schema if needed

### Drop Individual Tables (Development Only)

**⚠️ WARNING: This destroys table data!**

Use the dedicated drop utility with explicit table flags:

```bash
# Drop a specific table
uv run apps/orchestrator_db/drop_table.py --table orchestrator_chat

# Drop multiple tables
uv run apps/orchestrator_db/drop_table.py --table prompts --table agent_logs

# List available tables
uv run apps/orchestrator_db/drop_table.py --list
```

Available tables:
- `orchestrator_agents`
- `agents`
- `prompts`
- `agent_logs`
- `system_logs`
- `orchestrator_chat`

After dropping tables, recreate them:
```bash
uv run apps/orchestrator_db/run_migrations.py
```

### Reset Database (Development Only)

**⚠️ WARNING: This destroys all data!**

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

Then run migrations:
```bash
uv run apps/orchestrator_db/run_migrations.py
```

## 📚 Related Documentation

- **Migration System:** `migrations/README.md` - Detailed migration docs
- **Main README:** `../../README.md` - Project overview
- **Database Schema Spec:** `../../specs/cli-orch-db-structures.md` - Original design

## 🤝 Contributing

### Guidelines

1. **Never modify models directly in apps** - Always update `models.py` and sync
2. **Use idempotent SQL** - All migrations should use `IF NOT EXISTS`
3. **Test migrations** - Always test on development DB first
4. **Document changes** - Update READMEs when adding features
5. **Follow naming** - Use numbered migration files (0-9)

### Workflow

```bash
# 1. Make changes to models.py
vim apps/orchestrator_db/models.py

# 2. Sync to apps
python apps/orchestrator_db/sync_models.py

# 3. Update migrations if schema changed
vim apps/orchestrator_db/migrations/X_table.sql

# 4. Apply migrations
uv run apps/orchestrator_db/run_migrations.py

# 5. Test in app
cd apps/orchestrator_1_term
uv run pytest tests/
```

## 🚨 Troubleshooting

### "relation does not exist"

**Cause:** Database tables not created yet.

**Solution:**
```bash
uv run apps/orchestrator_db/run_migrations.py
```

### "DATABASE_URL not found"

**Cause:** Environment variable not set.

**Solution:**
```bash
# Copy sample .env
cp .env.sample .env

# Edit and add your DATABASE_URL
vim .env
```

### Models out of sync between apps

**Cause:** Forgot to run sync script after updating models.

**Solution:**
```bash
python apps/orchestrator_db/sync_models.py
```

### Migration fails

**Cause:** Various reasons (syntax error, constraint violation, etc.)

**Solution:**
1. Check migration output for specific error
2. Review SQL syntax in migration file
3. Check PostgreSQL logs
4. Verify data doesn't violate new constraints

## 📊 Statistics

- **5 Tables** - orchestrator_agents, agents, prompts, agent_logs, system_logs
- **36 Indexes** - Optimized for common query patterns
- **2 Triggers** - Auto-update timestamps
- **8 Migrations** - Ordered, idempotent schema setup
- **5 Models** - Type-safe Pydantic classes

---

**Last Updated:** 2025-10-22
**Maintainer:** Agentic Engineer Team
