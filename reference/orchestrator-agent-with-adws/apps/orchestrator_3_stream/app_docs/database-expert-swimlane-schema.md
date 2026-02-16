# Orchestrator Database Analysis & ADW Swimlane Schema Design

> **Generated**: Database architecture expert analysis for Multi-Agent Orchestration System
>
> **Purpose**: Complete documentation of existing tables and proposed ADW (Agent-Directed Workflow) swimlane feature schema

---

## Table of Contents

1. [Existing Database Tables](#part-1-existing-database-tables)
2. [ADW Swimlane Design Philosophy](#part-2-adw-swimlane-design-philosophy)
3. [New ADW Tables Schema](#part-3-new-adw-tables-schema)
4. [Indexes for Performance](#part-4-indexes-for-performance)
5. [Integration with Existing Tables](#part-5-integration-with-existing-tables)
6. [Example Workflow](#part-6-example-workflow)
7. [Pydantic Models](#part-7-pydantic-models)
8. [Migration Files](#part-8-migration-files)

---

## Part 1: Existing Database Tables

The orchestrator database currently has **6 tables** that manage multi-agent orchestration.

### 1.1 `orchestrator_agents`

**Purpose:** Singleton orchestrator agent that manages all other agents in a session.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique orchestrator identifier |
| `session_id` | TEXT | YES | NULL | Claude SDK session ID (UNIQUE constraint) |
| `system_prompt` | TEXT | YES | NULL | Orchestrator system prompt |
| `status` | TEXT | YES | NULL | Current status: `idle`, `executing`, `waiting`, `blocked`, `complete` |
| `working_dir` | TEXT | YES | NULL | Orchestrator working directory |
| `input_tokens` | INTEGER | NO | 0 | Cumulative input tokens consumed |
| `output_tokens` | INTEGER | NO | 0 | Cumulative output tokens generated |
| `total_cost` | DECIMAL(10,4) | NO | 0.0000 | Cumulative cost in USD |
| `archived` | BOOLEAN | NO | false | Soft delete flag |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Orchestrator configuration |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |

**Constraints:**
- `session_id` has UNIQUE constraint (prevents duplicate sessions)

**Indexes:**
- `idx_orchestrator_agents_status` on `status`
- `idx_orchestrator_agents_updated_at` on `updated_at DESC`

---

### 1.2 `agents`

**Purpose:** Agent registry and configuration for managed agents (scoped to orchestrator).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique agent identifier |
| `orchestrator_agent_id` | UUID | NO | - | FK to `orchestrator_agents(id)` ON DELETE CASCADE |
| `name` | TEXT | NO | - | Agent name (unique per orchestrator) |
| `model` | TEXT | NO | - | Claude model ID (e.g., `claude-sonnet-4-5-20250929`) |
| `system_prompt` | TEXT | YES | NULL | Agent custom system prompt |
| `working_dir` | TEXT | YES | NULL | Agent working directory path |
| `git_worktree` | TEXT | YES | NULL | Git worktree path if using worktrees |
| `status` | TEXT | YES | NULL | Current status: `idle`, `executing`, `waiting`, `blocked`, `complete` |
| `session_id` | TEXT | YES | NULL | Current Claude SDK session ID |
| `adw_id` | TEXT | YES | NULL | **AI Developer Workflow ID** (placeholder for swimlane) |
| `adw_step` | TEXT | YES | NULL | **AI Developer Workflow step identifier** |
| `input_tokens` | INTEGER | NO | 0 | Cumulative input tokens consumed |
| `output_tokens` | INTEGER | NO | 0 | Cumulative output tokens generated |
| `total_cost` | DECIMAL(10,4) | NO | 0.0000 | Cumulative cost in USD |
| `archived` | BOOLEAN | NO | false | Soft delete flag |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Agent configuration: allowed_tools, permission_mode, etc. |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |

**Constraints:**
- `unique_agent_name_per_orchestrator` UNIQUE(`orchestrator_agent_id`, `name`)

**Indexes:**
- `idx_agents_status` on `status`
- `idx_agents_archived` on `archived`
- `idx_agents_updated_at` on `updated_at DESC`
- `idx_agents_name` on `name`

**Notable:** Already has `adw_id` and `adw_step` columns as placeholders for ADW integration!

---

### 1.3 `prompts`

**Purpose:** Prompts sent to agents from engineers or orchestrator.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique prompt identifier |
| `agent_id` | UUID | YES | NULL | FK to `agents(id)` ON DELETE CASCADE |
| `task_slug` | TEXT | YES | NULL | Associated task identifier (kebab-case) |
| `author` | TEXT | NO | - | Who sent: `engineer` or `orchestrator_agent` |
| `prompt_text` | TEXT | NO | - | The actual prompt content |
| `summary` | TEXT | YES | NULL | AI-generated summary (50-100 chars) |
| `timestamp` | TIMESTAMPTZ | NO | `NOW()` | When the prompt was sent |
| `session_id` | TEXT | YES | NULL | Claude SDK session ID |

**Indexes:**
- `idx_prompts_agent_id` on `agent_id`
- `idx_prompts_author` on `author`
- `idx_prompts_timestamp` on `timestamp DESC`
- `idx_prompts_task_slug` on `task_slug` WHERE `task_slug IS NOT NULL`

---

### 1.4 `agent_logs`

**Purpose:** Unified event log for hooks and agent responses during task execution.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique log entry identifier |
| `agent_id` | UUID | NO | - | FK to `agents(id)` ON DELETE CASCADE |
| `session_id` | TEXT | YES | NULL | Claude SDK session ID |
| `task_slug` | TEXT | YES | NULL | Task identifier (kebab-case) |
| `adw_id` | TEXT | YES | NULL | **AI Developer Workflow identifier** |
| `adw_step` | TEXT | YES | NULL | **AI Developer Workflow step identifier** |
| `entry_index` | INTEGER | YES | NULL | Sequential index within task for tail reading |
| `event_category` | TEXT | NO | - | Event category: `hook` or `response` |
| `event_type` | TEXT | NO | - | Specific event type (see below) |
| `content` | TEXT | YES | NULL | Text content for text/thinking blocks |
| `payload` | JSONB | NO | `'{}'::jsonb` | Complete event data |
| `summary` | TEXT | YES | NULL | AI-generated summary |
| `timestamp` | TIMESTAMPTZ | NO | `NOW()` | When the event occurred |

**Event Types:**
- Hooks: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`
- Responses: `text`, `thinking`, `tool_use`, `tool_result`

**Indexes:**
- `idx_agent_logs_agent_id` on `agent_id`
- `idx_agent_logs_task_slug` on `task_slug` WHERE `task_slug IS NOT NULL`
- `idx_agent_logs_adw_id` on `adw_id` WHERE `adw_id IS NOT NULL`
- `idx_agent_logs_adw_step` on `adw_step` WHERE `adw_step IS NOT NULL`
- `idx_agent_logs_task_index` on `(task_slug, entry_index)` WHERE `task_slug IS NOT NULL`
- `idx_agent_logs_category` on `event_category`
- `idx_agent_logs_type` on `event_type`
- `idx_agent_logs_category_type` on `(event_category, event_type)`
- `idx_agent_logs_timestamp` on `timestamp DESC`
- `idx_agent_logs_session` on `session_id` WHERE `session_id IS NOT NULL`

**Notable:** Also has `adw_id` and `adw_step` columns for ADW tracking!

---

### 1.5 `system_logs`

**Purpose:** Application-level system logs (global application events only).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique log entry identifier |
| `file_path` | TEXT | YES | NULL | Associated file path where log was written |
| `adw_id` | TEXT | YES | NULL | **Associated ADW identifier** |
| `adw_step` | TEXT | YES | NULL | **AI Developer Workflow step identifier** |
| `level` | TEXT | NO | - | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `message` | TEXT | NO | - | Log message |
| `summary` | TEXT | YES | NULL | AI-generated summary (50-100 chars) |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Additional log context |
| `timestamp` | TIMESTAMPTZ | NO | `NOW()` | When the log was created |

**Indexes:**
- `idx_system_logs_level` on `level`
- `idx_system_logs_timestamp` on `timestamp DESC`
- `idx_system_logs_adw_id` on `adw_id` WHERE `adw_id IS NOT NULL`
- `idx_system_logs_adw_step` on `adw_step` WHERE `adw_step IS NOT NULL`

---

### 1.6 `orchestrator_chat`

**Purpose:** Append-only conversation log for 3-way communication: user ↔ orchestrator ↔ agents.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key - unique message identifier |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |
| `orchestrator_agent_id` | UUID | NO | - | FK to `orchestrator_agents(id)` ON DELETE CASCADE |
| `sender_type` | TEXT | NO | - | Who sent: `user`, `orchestrator`, `agent` |
| `receiver_type` | TEXT | NO | - | Who receives: `user`, `orchestrator`, `agent` |
| `message` | TEXT | NO | - | The message text content |
| `summary` | TEXT | YES | NULL | AI-generated summary (50-100 chars) |
| `agent_id` | UUID | YES | NULL | FK to `agents(id)` ON DELETE CASCADE |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Extensible metadata |

**Constraints:**
- `agent_id_required_for_agents` CHECK: agent_id must be set when sender_type or receiver_type is 'agent'

**Message Flow Examples:**
- `user → orchestrator`: sender='user', receiver='orchestrator', agent_id=NULL
- `orchestrator → user`: sender='orchestrator', receiver='user', agent_id=NULL
- `orchestrator → agent`: sender='orchestrator', receiver='agent', agent_id=builder_id
- `agent → orchestrator`: sender='agent', receiver='orchestrator', agent_id=builder_id

**Indexes:**
- `idx_orchestrator_chat_orch_id` on `orchestrator_agent_id`
- `idx_orchestrator_chat_agent_id` on `agent_id`
- `idx_orchestrator_chat_sender_type` on `sender_type`
- `idx_orchestrator_chat_receiver_type` on `receiver_type`
- `idx_orchestrator_chat_orch_created` on `(orchestrator_agent_id, created_at DESC)`
- `idx_orchestrator_chat_agent_created` on `(agent_id, created_at DESC)`

---

## Part 2: ADW Swimlane Design Philosophy

### Requirements

The ADW (Agent-Directed Workflow) system needs to support:

1. **Pipeline Definition**: Define a sequence of stages with agent assignments
2. **Work Items**: Track individual tasks/items flowing through the pipeline
3. **Stage Transitions**: Record when items move between stages
4. **Agent Handoffs**: Track which agent handled which stage
5. **Parallel Processing**: Multiple items in different stages simultaneously
6. **Observability**: Full audit trail of all transitions

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ADW SWIMLANE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐                          │
│  │ adw_workflows    │────<│ adw_stages       │                          │
│  │ (Pipeline def)   │  1:N │ (Lane definition)│                          │
│  └──────────────────┘     └──────────────────┘                          │
│           │                        │                                     │
│           │ 1:N                    │ 1:N                                 │
│           ▼                        ▼                                     │
│  ┌──────────────────┐     ┌──────────────────┐                          │
│  │ adw_work_items   │────<│ adw_transitions  │                          │
│  │ (Things flowing) │  1:N │ (Movement log)   │                          │
│  └──────────────────┘     └──────────────────┘                          │
│                                                                          │
│  ═══════════════════════════════════════════════════════════════════════ │
│                           DATA FLOW EXAMPLE                              │
│                                                                          │
│   Work Item "feature-123"                                                │
│   ┌────────────┬────────────┬────────────┬────────────┐                 │
│   │   PLAN     │   BUILD    │   REVIEW   │   DEPLOY   │  ← Stages       │
│   │  (Scout)   │ (Builder)  │ (Reviewer) │ (DevOps)   │  ← Agents       │
│   └────────────┴────────────┴────────────┴────────────┘                 │
│        ▲             ▲             ▲             ▲                       │
│        └─────────────┴─────────────┴─────────────┘                       │
│                    Transitions tracked                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Separation of Definition vs Execution**: Workflows/Stages are templates; Work Items/Transitions are runtime
2. **Agent Flexibility**: Stages can have static agent assignment OR dynamic by agent_type
3. **Rich Transition Types**: Support for advance, reject, skip, pause, resume, etc.
4. **Context Accumulation**: Work items carry context that grows as they move through stages
5. **Full Audit Trail**: Every transition is logged with timing, data passed, and reason
6. **Existing Integration**: Leverages existing `adw_id`/`adw_step` columns in agents and logs

---

## Part 3: New ADW Tables Schema

### 3.1 `adw_workflows`

**Purpose:** Defines a workflow/pipeline template.

```sql
-- ============================================================================
-- ADW_WORKFLOWS TABLE
-- ============================================================================
-- Defines a workflow pipeline template for Agent-Directed Workflows
--
-- Dependencies: orchestrator_agents table (FK constraint)

CREATE TABLE IF NOT EXISTS adw_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,

    -- Workflow identification
    name TEXT NOT NULL,
    slug TEXT NOT NULL,  -- kebab-case identifier (e.g., "feature-development")
    description TEXT,

    -- Workflow configuration
    workflow_type TEXT NOT NULL CHECK (workflow_type IN (
        'sequential',     -- Stages must be completed in order
        'parallel',       -- Stages can run simultaneously
        'conditional'     -- Stages run based on conditions
    )) DEFAULT 'sequential',

    -- Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'draft',          -- Being designed
        'active',         -- Ready for use
        'paused',         -- Temporarily stopped
        'archived'        -- Soft deleted
    )) DEFAULT 'draft',

    -- Configuration
    config JSONB DEFAULT '{}'::jsonb,  -- Workflow-level settings
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique workflow name per orchestrator
    CONSTRAINT unique_workflow_per_orchestrator UNIQUE (orchestrator_agent_id, slug)
);

-- Comments
COMMENT ON TABLE adw_workflows IS 'Agent-Directed Workflow pipeline definitions';
COMMENT ON COLUMN adw_workflows.slug IS 'Kebab-case identifier for the workflow (unique per orchestrator)';
COMMENT ON COLUMN adw_workflows.workflow_type IS 'How stages execute: sequential, parallel, or conditional';
COMMENT ON COLUMN adw_workflows.config IS 'Workflow configuration: timeout, retry policies, notifications';
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `orchestrator_agent_id` | UUID | NO | - | FK to `orchestrator_agents(id)` |
| `name` | TEXT | NO | - | Human-readable workflow name |
| `slug` | TEXT | NO | - | Kebab-case identifier for referencing |
| `description` | TEXT | YES | NULL | Workflow description |
| `workflow_type` | TEXT | NO | `'sequential'` | `sequential`, `parallel`, or `conditional` |
| `status` | TEXT | NO | `'draft'` | `draft`, `active`, `paused`, `archived` |
| `config` | JSONB | NO | `'{}'::jsonb` | Timeout settings, retry policies, etc. |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Additional metadata |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |

---

### 3.2 `adw_stages`

**Purpose:** Defines the stages (swimlanes) within a workflow.

```sql
-- ============================================================================
-- ADW_STAGES TABLE
-- ============================================================================
-- Defines stages (swimlanes) within an ADW workflow
--
-- Dependencies: adw_workflows table (FK constraint)

CREATE TABLE IF NOT EXISTS adw_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES adw_workflows(id) ON DELETE CASCADE,

    -- Stage identification
    name TEXT NOT NULL,
    slug TEXT NOT NULL,  -- kebab-case identifier (e.g., "code-review")
    description TEXT,

    -- Stage ordering
    sequence_order INTEGER NOT NULL,  -- Order in sequential workflows (0-indexed)

    -- Agent assignment
    agent_type TEXT,           -- Type of agent for this stage (e.g., "builder", "reviewer")
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,  -- Specific agent assignment (optional)
    agent_config JSONB DEFAULT '{}'::jsonb,  -- Agent configuration for this stage

    -- Stage behavior
    is_entry_point BOOLEAN DEFAULT false,    -- Can work items start here?
    is_exit_point BOOLEAN DEFAULT false,     -- Can work items complete here?
    auto_advance BOOLEAN DEFAULT false,      -- Auto-advance when complete?

    -- Conditions for conditional workflows
    entry_conditions JSONB DEFAULT '[]'::jsonb,   -- Conditions to enter this stage
    exit_conditions JSONB DEFAULT '[]'::jsonb,    -- Conditions to exit this stage

    -- Time limits
    timeout_minutes INTEGER,      -- Max time an item can spend in this stage
    sla_minutes INTEGER,          -- Target time for this stage

    -- Configuration
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique stage slug per workflow
    CONSTRAINT unique_stage_per_workflow UNIQUE (workflow_id, slug),
    -- Unique sequence order per workflow
    CONSTRAINT unique_sequence_per_workflow UNIQUE (workflow_id, sequence_order)
);

-- Comments
COMMENT ON TABLE adw_stages IS 'Stages (swimlanes) within an ADW workflow';
COMMENT ON COLUMN adw_stages.sequence_order IS '0-indexed order for sequential workflows';
COMMENT ON COLUMN adw_stages.agent_type IS 'Type of agent to use (for dynamic assignment)';
COMMENT ON COLUMN adw_stages.agent_id IS 'Specific pre-assigned agent (optional, for static assignment)';
COMMENT ON COLUMN adw_stages.auto_advance IS 'Automatically move to next stage when complete';
COMMENT ON COLUMN adw_stages.entry_conditions IS 'JSON conditions that must be met to enter this stage';
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `workflow_id` | UUID | NO | - | FK to `adw_workflows(id)` |
| `name` | TEXT | NO | - | Human-readable stage name |
| `slug` | TEXT | NO | - | Kebab-case identifier |
| `description` | TEXT | YES | NULL | Stage description |
| `sequence_order` | INTEGER | NO | - | Position in the pipeline (0-indexed) |
| `agent_type` | TEXT | YES | NULL | Type of agent needed (e.g., "planner", "builder") |
| `agent_id` | UUID | YES | NULL | FK to `agents(id)` - pre-assigned specific agent |
| `agent_config` | JSONB | NO | `'{}'::jsonb` | Agent configuration for this stage |
| `is_entry_point` | BOOLEAN | NO | false | Can items start here? |
| `is_exit_point` | BOOLEAN | NO | false | Can items complete here? |
| `auto_advance` | BOOLEAN | NO | false | Auto-move to next stage when done? |
| `entry_conditions` | JSONB | NO | `'[]'::jsonb` | Conditions to enter stage |
| `exit_conditions` | JSONB | NO | `'[]'::jsonb` | Conditions to exit stage |
| `timeout_minutes` | INTEGER | YES | NULL | Max time allowed in stage |
| `sla_minutes` | INTEGER | YES | NULL | Target time for stage |
| `config` | JSONB | NO | `'{}'::jsonb` | Stage configuration |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Additional metadata |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |

---

### 3.3 `adw_work_items`

**Purpose:** Tracks individual work items flowing through a workflow.

```sql
-- ============================================================================
-- ADW_WORK_ITEMS TABLE
-- ============================================================================
-- Tracks work items flowing through ADW workflows
--
-- Dependencies: adw_workflows, adw_stages tables (FK constraints)

CREATE TABLE IF NOT EXISTS adw_work_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES adw_workflows(id) ON DELETE CASCADE,

    -- Work item identification
    title TEXT NOT NULL,
    slug TEXT NOT NULL,  -- kebab-case identifier (e.g., "implement-auth-feature")
    description TEXT,

    -- Current position in workflow
    current_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,
    current_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Status tracking
    status TEXT NOT NULL CHECK (status IN (
        'pending',        -- Not yet started
        'queued',         -- Waiting to be picked up
        'in_progress',    -- Currently being worked on
        'blocked',        -- Waiting on external input
        'review',         -- In review stage
        'completed',      -- Successfully finished
        'failed',         -- Failed with errors
        'cancelled'       -- Manually cancelled
    )) DEFAULT 'pending',

    -- Priority and ordering
    priority INTEGER DEFAULT 0,  -- Higher = more urgent (0-100)

    -- Work item content
    input_data JSONB DEFAULT '{}'::jsonb,    -- Initial input for the work item
    output_data JSONB DEFAULT '{}'::jsonb,   -- Final output/result
    context JSONB DEFAULT '{}'::jsonb,       -- Accumulated context as item moves through stages

    -- Error tracking
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    last_error_at TIMESTAMPTZ,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,

    -- Configuration
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique work item slug per workflow
    CONSTRAINT unique_work_item_per_workflow UNIQUE (workflow_id, slug)
);

-- Comments
COMMENT ON TABLE adw_work_items IS 'Work items flowing through ADW workflows';
COMMENT ON COLUMN adw_work_items.current_stage_id IS 'Current stage in the workflow';
COMMENT ON COLUMN adw_work_items.current_agent_id IS 'Agent currently working on this item';
COMMENT ON COLUMN adw_work_items.input_data IS 'Initial input data for processing';
COMMENT ON COLUMN adw_work_items.output_data IS 'Final output after completion';
COMMENT ON COLUMN adw_work_items.context IS 'Accumulated context passed between stages';
COMMENT ON COLUMN adw_work_items.priority IS 'Priority level 0-100 (higher = more urgent)';
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `workflow_id` | UUID | NO | - | FK to `adw_workflows(id)` |
| `title` | TEXT | NO | - | Human-readable work item title |
| `slug` | TEXT | NO | - | Kebab-case identifier |
| `description` | TEXT | YES | NULL | Work item description |
| `current_stage_id` | UUID | YES | NULL | FK to `adw_stages(id)` - current position |
| `current_agent_id` | UUID | YES | NULL | FK to `agents(id)` - agent working on it |
| `status` | TEXT | NO | `'pending'` | Full lifecycle status |
| `priority` | INTEGER | NO | 0 | Urgency level (0-100) |
| `input_data` | JSONB | NO | `'{}'::jsonb` | Initial input for the work |
| `output_data` | JSONB | NO | `'{}'::jsonb` | Final result |
| `context` | JSONB | NO | `'{}'::jsonb` | Data accumulated across stages |
| `error_message` | TEXT | YES | NULL | Last error message |
| `error_count` | INTEGER | NO | 0 | Retry tracking |
| `last_error_at` | TIMESTAMPTZ | YES | NULL | When last error occurred |
| `started_at` | TIMESTAMPTZ | YES | NULL | When work started |
| `completed_at` | TIMESTAMPTZ | YES | NULL | When work completed |
| `due_at` | TIMESTAMPTZ | YES | NULL | Due date |
| `config` | JSONB | NO | `'{}'::jsonb` | Work item configuration |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Additional metadata |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last update timestamp |

**Status Values:**
- `pending` - Not yet started
- `queued` - Waiting to be picked up
- `in_progress` - Currently being worked on
- `blocked` - Waiting on external input
- `review` - In review stage
- `completed` - Successfully finished
- `failed` - Failed with errors
- `cancelled` - Manually cancelled

---

### 3.4 `adw_transitions`

**Purpose:** Audit log of all stage transitions (the heart of swimlane tracking).

```sql
-- ============================================================================
-- ADW_TRANSITIONS TABLE
-- ============================================================================
-- Audit log of work item transitions between stages
--
-- Dependencies: adw_work_items, adw_stages, agents tables (FK constraints)

CREATE TABLE IF NOT EXISTS adw_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_item_id UUID NOT NULL REFERENCES adw_work_items(id) ON DELETE CASCADE,

    -- Stage transition
    from_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,  -- NULL for initial entry
    to_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,    -- NULL for final exit

    -- Agent handoff
    from_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    to_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Transition details
    transition_type TEXT NOT NULL CHECK (transition_type IN (
        'start',          -- Work item entered workflow
        'advance',        -- Normal progression to next stage
        'skip',           -- Skipped one or more stages
        'reject',         -- Sent back to previous stage
        'reassign',       -- Changed agent within same stage
        'pause',          -- Work item paused
        'resume',         -- Work item resumed
        'complete',       -- Work item finished workflow
        'fail',           -- Work item failed
        'cancel'          -- Work item cancelled
    )),

    -- Transition reason/context
    reason TEXT,          -- Human-readable reason for transition
    trigger TEXT,         -- What caused this: 'auto', 'manual', 'condition', 'timeout'

    -- Data at transition time
    stage_input JSONB DEFAULT '{}'::jsonb,    -- Data passed INTO the new stage
    stage_output JSONB DEFAULT '{}'::jsonb,   -- Data produced by the previous stage

    -- Metrics
    duration_seconds INTEGER,  -- Time spent in previous stage

    -- Configuration
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE adw_transitions IS 'Audit log of work item stage transitions';
COMMENT ON COLUMN adw_transitions.from_stage_id IS 'Stage being exited (NULL for initial entry)';
COMMENT ON COLUMN adw_transitions.to_stage_id IS 'Stage being entered (NULL for final exit)';
COMMENT ON COLUMN adw_transitions.transition_type IS 'Type of transition: advance, reject, skip, etc.';
COMMENT ON COLUMN adw_transitions.trigger IS 'What caused transition: auto, manual, condition, timeout';
COMMENT ON COLUMN adw_transitions.stage_input IS 'Data passed to the new stage';
COMMENT ON COLUMN adw_transitions.stage_output IS 'Data produced by the previous stage';
COMMENT ON COLUMN adw_transitions.duration_seconds IS 'Time spent in the previous stage';
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `work_item_id` | UUID | NO | - | FK to `adw_work_items(id)` |
| `from_stage_id` | UUID | YES | NULL | FK to `adw_stages(id)` - stage being left (NULL for start) |
| `to_stage_id` | UUID | YES | NULL | FK to `adw_stages(id)` - stage being entered (NULL for completion) |
| `from_agent_id` | UUID | YES | NULL | FK to `agents(id)` - agent handing off |
| `to_agent_id` | UUID | YES | NULL | FK to `agents(id)` - agent receiving |
| `transition_type` | TEXT | NO | - | Type of transition |
| `reason` | TEXT | YES | NULL | Human-readable reason for transition |
| `trigger` | TEXT | YES | NULL | What caused it: `auto`, `manual`, `condition`, `timeout` |
| `stage_input` | JSONB | NO | `'{}'::jsonb` | Data passed to new stage |
| `stage_output` | JSONB | NO | `'{}'::jsonb` | Data produced by previous stage |
| `duration_seconds` | INTEGER | YES | NULL | Time spent in previous stage |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Additional metadata |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Transition timestamp |

**Transition Types:**
- `start` - Work item entered workflow
- `advance` - Normal progression to next stage
- `skip` - Skipped one or more stages
- `reject` - Sent back to previous stage
- `reassign` - Changed agent within same stage
- `pause` - Work item paused
- `resume` - Work item resumed
- `complete` - Work item finished workflow
- `fail` - Work item failed
- `cancel` - Work item cancelled

---

## Part 4: Indexes for Performance

```sql
-- ============================================================================
-- ADW INDEXES
-- ============================================================================

-- adw_workflows indexes
CREATE INDEX IF NOT EXISTS idx_adw_workflows_orchestrator ON adw_workflows(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_workflows_status ON adw_workflows(status);
CREATE INDEX IF NOT EXISTS idx_adw_workflows_slug ON adw_workflows(slug);

-- adw_stages indexes
CREATE INDEX IF NOT EXISTS idx_adw_stages_workflow ON adw_stages(workflow_id);
CREATE INDEX IF NOT EXISTS idx_adw_stages_sequence ON adw_stages(workflow_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_adw_stages_agent ON adw_stages(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_adw_stages_entry ON adw_stages(workflow_id) WHERE is_entry_point = true;
CREATE INDEX IF NOT EXISTS idx_adw_stages_exit ON adw_stages(workflow_id) WHERE is_exit_point = true;

-- adw_work_items indexes
CREATE INDEX IF NOT EXISTS idx_adw_work_items_workflow ON adw_work_items(workflow_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_current_stage ON adw_work_items(current_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_current_agent ON adw_work_items(current_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_status ON adw_work_items(status);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_priority ON adw_work_items(priority DESC) WHERE status IN ('pending', 'queued');
CREATE INDEX IF NOT EXISTS idx_adw_work_items_slug ON adw_work_items(slug);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_active ON adw_work_items(workflow_id, status) WHERE status IN ('queued', 'in_progress', 'blocked', 'review');

-- adw_transitions indexes
CREATE INDEX IF NOT EXISTS idx_adw_transitions_work_item ON adw_transitions(work_item_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_from_stage ON adw_transitions(from_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_to_stage ON adw_transitions(to_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_from_agent ON adw_transitions(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_to_agent ON adw_transitions(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_type ON adw_transitions(transition_type);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_created ON adw_transitions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_work_item_timeline ON adw_transitions(work_item_id, created_at DESC);
```

---

## Part 5: Integration with Existing Tables

The existing `adw_id` and `adw_step` columns in `agents`, `agent_logs`, and `system_logs` should reference the new ADW tables:

```sql
-- Update column comments to clarify the relationship
COMMENT ON COLUMN agents.adw_id IS 'References adw_work_items.slug - the work item being processed';
COMMENT ON COLUMN agents.adw_step IS 'References adw_stages.slug - current stage in workflow';

COMMENT ON COLUMN agent_logs.adw_id IS 'References adw_work_items.slug - the work item this log relates to';
COMMENT ON COLUMN agent_logs.adw_step IS 'References adw_stages.slug - the stage this log relates to';

COMMENT ON COLUMN system_logs.adw_id IS 'References adw_work_items.slug - associated work item';
COMMENT ON COLUMN system_logs.adw_step IS 'References adw_stages.slug - associated stage';
```

### Cross-Table Query Example

To get all logs for a specific work item across all stages:

```sql
SELECT
    al.timestamp,
    al.event_type,
    al.content,
    a.name AS agent_name,
    al.adw_step AS stage_slug
FROM agent_logs al
JOIN agents a ON al.agent_id = a.id
WHERE al.adw_id = 'implement-auth-feature'
ORDER BY al.timestamp DESC;
```

---

## Part 6: Example Workflow

### Feature Development Pipeline

```
Workflow: "feature-development"
├── Stage 0: "plan" (Scout Agent)
│   └── Entry point, analyzes requirements
├── Stage 1: "design" (Architect Agent)
│   └── Creates technical design
├── Stage 2: "build" (Builder Agent)
│   └── Implements the feature
├── Stage 3: "review" (Reviewer Agent)
│   └── Code review, can reject → build
├── Stage 4: "test" (QA Agent)
│   └── Runs tests, can reject → build
└── Stage 5: "deploy" (DevOps Agent)
    └── Exit point, deploys to environment
```

### Work Item Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Work Item: "add-user-authentication"                                     │
│ Priority: 80                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [PLAN]──advance──>[DESIGN]──advance──>[BUILD]──advance──>[REVIEW]      │
│    │                                                          │          │
│    └─ Scout Agent                                             │          │
│       Input: {requirements: "..."}                            │          │
│       Output: {plan_doc: "..."}                  reject──────┘          │
│                                                  (back to BUILD)         │
│                                                                          │
│  [REVIEW]──advance──>[TEST]──advance──>[DEPLOY]──complete──>DONE        │
│                         │                                                │
│                         │                                                │
│                         └── reject (back to BUILD)                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Sample Data

```sql
-- Create workflow
INSERT INTO adw_workflows (orchestrator_agent_id, name, slug, workflow_type, status)
VALUES ('orch-uuid', 'Feature Development', 'feature-development', 'sequential', 'active');

-- Create stages
INSERT INTO adw_stages (workflow_id, name, slug, sequence_order, agent_type, is_entry_point, auto_advance)
VALUES
    ('workflow-uuid', 'Plan', 'plan', 0, 'scout', true, true),
    ('workflow-uuid', 'Design', 'design', 1, 'architect', false, true),
    ('workflow-uuid', 'Build', 'build', 2, 'builder', false, false),
    ('workflow-uuid', 'Review', 'review', 3, 'reviewer', false, false),
    ('workflow-uuid', 'Test', 'test', 4, 'qa', false, false),
    ('workflow-uuid', 'Deploy', 'deploy', 5, 'devops', false, true);

-- Create work item
INSERT INTO adw_work_items (workflow_id, title, slug, status, priority, input_data)
VALUES (
    'workflow-uuid',
    'Add User Authentication',
    'add-user-authentication',
    'queued',
    80,
    '{"requirements": "Implement OAuth2 login with Google and GitHub providers"}'
);

-- Record transition (start)
INSERT INTO adw_transitions (work_item_id, to_stage_id, to_agent_id, transition_type, trigger, stage_input)
VALUES (
    'work-item-uuid',
    'plan-stage-uuid',
    'scout-agent-uuid',
    'start',
    'manual',
    '{"requirements": "Implement OAuth2 login with Google and GitHub providers"}'
);
```

---

## Part 7: Pydantic Models

Add these models to `apps/orchestrator_db/models.py`:

```python
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════
# ADW_WORKFLOW MODEL
# ═══════════════════════════════════════════════════════════


class AdwWorkflow(BaseModel):
    """
    Agent-Directed Workflow pipeline definition.

    Maps to: adw_workflows table
    """
    id: UUID
    orchestrator_agent_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    workflow_type: Literal['sequential', 'parallel', 'conditional'] = 'sequential'
    status: Literal['draft', 'active', 'paused', 'archived'] = 'draft'
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('config', 'metadata', mode='before')
    @classmethod
    def parse_jsonb(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# ADW_STAGE MODEL
# ═══════════════════════════════════════════════════════════


class AdwStage(BaseModel):
    """
    Stage (swimlane) within an ADW workflow.

    Maps to: adw_stages table
    """
    id: UUID
    workflow_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    sequence_order: int
    agent_type: Optional[str] = None
    agent_id: Optional[UUID] = None
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    is_entry_point: bool = False
    is_exit_point: bool = False
    auto_advance: bool = False
    entry_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    exit_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    timeout_minutes: Optional[int] = None
    sla_minutes: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'workflow_id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('agent_config', 'config', 'metadata', mode='before')
    @classmethod
    def parse_jsonb_dict(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator('entry_conditions', 'exit_conditions', mode='before')
    @classmethod
    def parse_jsonb_list(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# ADW_WORK_ITEM MODEL
# ═══════════════════════════════════════════════════════════


class AdwWorkItem(BaseModel):
    """
    Work item flowing through an ADW workflow.

    Maps to: adw_work_items table
    """
    id: UUID
    workflow_id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    current_stage_id: Optional[UUID] = None
    current_agent_id: Optional[UUID] = None
    status: Literal['pending', 'queued', 'in_progress', 'blocked', 'review', 'completed', 'failed', 'cancelled'] = 'pending'
    priority: int = 0
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_count: int = 0
    last_error_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'workflow_id', 'current_stage_id', 'current_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('input_data', 'output_data', 'context', 'config', 'metadata', mode='before')
    @classmethod
    def parse_jsonb(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# ADW_TRANSITION MODEL
# ═══════════════════════════════════════════════════════════


class AdwTransition(BaseModel):
    """
    Audit log entry for work item stage transitions.

    Maps to: adw_transitions table
    """
    id: UUID
    work_item_id: UUID
    from_stage_id: Optional[UUID] = None
    to_stage_id: Optional[UUID] = None
    from_agent_id: Optional[UUID] = None
    to_agent_id: Optional[UUID] = None
    transition_type: Literal['start', 'advance', 'skip', 'reject', 'reassign', 'pause', 'resume', 'complete', 'fail', 'cancel']
    reason: Optional[str] = None
    trigger: Optional[str] = None
    stage_input: Dict[str, Any] = Field(default_factory=dict)
    stage_output: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator('id', 'work_item_id', 'from_stage_id', 'to_stage_id', 'from_agent_id', 'to_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('stage_input', 'stage_output', 'metadata', mode='before')
    @classmethod
    def parse_jsonb(cls, v):
        """Parse JSON string to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# UPDATE EXPORT PUBLIC API
# ═══════════════════════════════════════════════════════════

__all__ = [
    "OrchestratorAgent",
    "Agent",
    "Prompt",
    "AgentLog",
    "SystemLog",
    "OrchestratorChat",
    # ADW Models
    "AdwWorkflow",
    "AdwStage",
    "AdwWorkItem",
    "AdwTransition",
]
```

---

## Part 8: Migration Files

Create these migration files in `apps/orchestrator_db/migrations/`:

### `9_adw_workflows.sql`

```sql
-- ============================================================================
-- ADW_WORKFLOWS TABLE
-- ============================================================================
-- Defines workflow pipeline templates for Agent-Directed Workflows
--
-- Dependencies: orchestrator_agents table (FK constraint)

CREATE TABLE IF NOT EXISTS adw_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    workflow_type TEXT NOT NULL CHECK (workflow_type IN ('sequential', 'parallel', 'conditional')) DEFAULT 'sequential',
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'paused', 'archived')) DEFAULT 'draft',
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_workflow_per_orchestrator UNIQUE (orchestrator_agent_id, slug)
);

COMMENT ON TABLE adw_workflows IS 'Agent-Directed Workflow pipeline definitions';
COMMENT ON COLUMN adw_workflows.slug IS 'Kebab-case identifier for the workflow (unique per orchestrator)';
COMMENT ON COLUMN adw_workflows.workflow_type IS 'How stages execute: sequential, parallel, or conditional';
COMMENT ON COLUMN adw_workflows.config IS 'Workflow configuration: timeout, retry policies, notifications';
```

### `10_adw_stages.sql`

```sql
-- ============================================================================
-- ADW_STAGES TABLE
-- ============================================================================
-- Defines stages (swimlanes) within an ADW workflow
--
-- Dependencies: adw_workflows, agents tables (FK constraints)

CREATE TABLE IF NOT EXISTS adw_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES adw_workflows(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    sequence_order INTEGER NOT NULL,
    agent_type TEXT,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    agent_config JSONB DEFAULT '{}'::jsonb,
    is_entry_point BOOLEAN DEFAULT false,
    is_exit_point BOOLEAN DEFAULT false,
    auto_advance BOOLEAN DEFAULT false,
    entry_conditions JSONB DEFAULT '[]'::jsonb,
    exit_conditions JSONB DEFAULT '[]'::jsonb,
    timeout_minutes INTEGER,
    sla_minutes INTEGER,
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_stage_per_workflow UNIQUE (workflow_id, slug),
    CONSTRAINT unique_sequence_per_workflow UNIQUE (workflow_id, sequence_order)
);

COMMENT ON TABLE adw_stages IS 'Stages (swimlanes) within an ADW workflow';
COMMENT ON COLUMN adw_stages.sequence_order IS '0-indexed order for sequential workflows';
COMMENT ON COLUMN adw_stages.agent_type IS 'Type of agent to use (for dynamic assignment)';
COMMENT ON COLUMN adw_stages.agent_id IS 'Specific pre-assigned agent (optional, for static assignment)';
COMMENT ON COLUMN adw_stages.auto_advance IS 'Automatically move to next stage when complete';
COMMENT ON COLUMN adw_stages.entry_conditions IS 'JSON conditions that must be met to enter this stage';
```

### `11_adw_work_items.sql`

```sql
-- ============================================================================
-- ADW_WORK_ITEMS TABLE
-- ============================================================================
-- Tracks work items flowing through ADW workflows
--
-- Dependencies: adw_workflows, adw_stages, agents tables (FK constraints)

CREATE TABLE IF NOT EXISTS adw_work_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES adw_workflows(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    current_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,
    current_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'queued', 'in_progress', 'blocked', 'review', 'completed', 'failed', 'cancelled')) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    context JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    last_error_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    config JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_work_item_per_workflow UNIQUE (workflow_id, slug)
);

COMMENT ON TABLE adw_work_items IS 'Work items flowing through ADW workflows';
COMMENT ON COLUMN adw_work_items.current_stage_id IS 'Current stage in the workflow';
COMMENT ON COLUMN adw_work_items.current_agent_id IS 'Agent currently working on this item';
COMMENT ON COLUMN adw_work_items.input_data IS 'Initial input data for processing';
COMMENT ON COLUMN adw_work_items.output_data IS 'Final output after completion';
COMMENT ON COLUMN adw_work_items.context IS 'Accumulated context passed between stages';
COMMENT ON COLUMN adw_work_items.priority IS 'Priority level 0-100 (higher = more urgent)';
```

### `12_adw_transitions.sql`

```sql
-- ============================================================================
-- ADW_TRANSITIONS TABLE
-- ============================================================================
-- Audit log of work item transitions between stages
--
-- Dependencies: adw_work_items, adw_stages, agents tables (FK constraints)

CREATE TABLE IF NOT EXISTS adw_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_item_id UUID NOT NULL REFERENCES adw_work_items(id) ON DELETE CASCADE,
    from_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,
    to_stage_id UUID REFERENCES adw_stages(id) ON DELETE SET NULL,
    from_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    to_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    transition_type TEXT NOT NULL CHECK (transition_type IN ('start', 'advance', 'skip', 'reject', 'reassign', 'pause', 'resume', 'complete', 'fail', 'cancel')),
    reason TEXT,
    trigger TEXT,
    stage_input JSONB DEFAULT '{}'::jsonb,
    stage_output JSONB DEFAULT '{}'::jsonb,
    duration_seconds INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE adw_transitions IS 'Audit log of work item stage transitions';
COMMENT ON COLUMN adw_transitions.from_stage_id IS 'Stage being exited (NULL for initial entry)';
COMMENT ON COLUMN adw_transitions.to_stage_id IS 'Stage being entered (NULL for final exit)';
COMMENT ON COLUMN adw_transitions.transition_type IS 'Type of transition: advance, reject, skip, etc.';
COMMENT ON COLUMN adw_transitions.trigger IS 'What caused transition: auto, manual, condition, timeout';
COMMENT ON COLUMN adw_transitions.stage_input IS 'Data passed to the new stage';
COMMENT ON COLUMN adw_transitions.stage_output IS 'Data produced by the previous stage';
COMMENT ON COLUMN adw_transitions.duration_seconds IS 'Time spent in the previous stage';
```

### `13_adw_indexes.sql`

```sql
-- ============================================================================
-- ADW INDEXES
-- ============================================================================
-- Performance indexes for ADW tables

-- adw_workflows indexes
CREATE INDEX IF NOT EXISTS idx_adw_workflows_orchestrator ON adw_workflows(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_workflows_status ON adw_workflows(status);
CREATE INDEX IF NOT EXISTS idx_adw_workflows_slug ON adw_workflows(slug);

-- adw_stages indexes
CREATE INDEX IF NOT EXISTS idx_adw_stages_workflow ON adw_stages(workflow_id);
CREATE INDEX IF NOT EXISTS idx_adw_stages_sequence ON adw_stages(workflow_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_adw_stages_agent ON adw_stages(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_adw_stages_entry ON adw_stages(workflow_id) WHERE is_entry_point = true;
CREATE INDEX IF NOT EXISTS idx_adw_stages_exit ON adw_stages(workflow_id) WHERE is_exit_point = true;

-- adw_work_items indexes
CREATE INDEX IF NOT EXISTS idx_adw_work_items_workflow ON adw_work_items(workflow_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_current_stage ON adw_work_items(current_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_current_agent ON adw_work_items(current_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_status ON adw_work_items(status);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_priority ON adw_work_items(priority DESC) WHERE status IN ('pending', 'queued');
CREATE INDEX IF NOT EXISTS idx_adw_work_items_slug ON adw_work_items(slug);
CREATE INDEX IF NOT EXISTS idx_adw_work_items_active ON adw_work_items(workflow_id, status) WHERE status IN ('queued', 'in_progress', 'blocked', 'review');

-- adw_transitions indexes
CREATE INDEX IF NOT EXISTS idx_adw_transitions_work_item ON adw_transitions(work_item_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_from_stage ON adw_transitions(from_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_to_stage ON adw_transitions(to_stage_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_from_agent ON adw_transitions(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_to_agent ON adw_transitions(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_type ON adw_transitions(transition_type);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_created ON adw_transitions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adw_transitions_work_item_timeline ON adw_transitions(work_item_id, created_at DESC);
```

### `14_adw_triggers.sql`

```sql
-- ============================================================================
-- ADW TRIGGERS
-- ============================================================================
-- Auto-update triggers for ADW tables

-- Trigger for adw_workflows updated_at
DROP TRIGGER IF EXISTS update_adw_workflows_updated_at ON adw_workflows;
CREATE TRIGGER update_adw_workflows_updated_at
    BEFORE UPDATE ON adw_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for adw_stages updated_at
DROP TRIGGER IF EXISTS update_adw_stages_updated_at ON adw_stages;
CREATE TRIGGER update_adw_stages_updated_at
    BEFORE UPDATE ON adw_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for adw_work_items updated_at
DROP TRIGGER IF EXISTS update_adw_work_items_updated_at ON adw_work_items;
CREATE TRIGGER update_adw_work_items_updated_at
    BEFORE UPDATE ON adw_work_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Summary

### Existing Tables (6 total)

| Table | Purpose |
|-------|---------|
| `orchestrator_agents` | Singleton orchestrator managing the session |
| `agents` | Agent registry (already has `adw_id`, `adw_step` placeholders) |
| `prompts` | Prompt history from engineers/orchestrator |
| `agent_logs` | Unified event log (has `adw_id`, `adw_step` placeholders) |
| `system_logs` | Application-level logs (has `adw_id`, `adw_step` placeholders) |
| `orchestrator_chat` | 3-way conversation log |

### New ADW Tables (4 total)

| Table | Purpose |
|-------|---------|
| `adw_workflows` | Define pipeline templates (sequential/parallel/conditional) |
| `adw_stages` | Define swimlanes within workflows with agent assignments |
| `adw_work_items` | Track items flowing through pipelines |
| `adw_transitions` | Audit log of all stage transitions and handoffs |

### Key Design Decisions

1. **Separation of Definition vs Execution**: Workflows/Stages are templates; Work Items/Transitions are runtime
2. **Agent Flexibility**: Stages can have static agent assignment OR dynamic by agent_type
3. **Rich Transition Types**: Support for advance, reject, skip, pause, resume, etc.
4. **Context Accumulation**: Work items carry context that grows as they move through stages
5. **Full Audit Trail**: Every transition is logged with timing, data passed, and reason
6. **Existing Integration**: Leverages existing `adw_id`/`adw_step` columns in agents and logs

---

*Generated by Database Architecture Expert Agent*
