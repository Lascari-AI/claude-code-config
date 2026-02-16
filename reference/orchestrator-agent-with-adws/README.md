# AI Developer Workflows, Multi-Agent Orchestration and Agent Experts

This repository demonstrates three powerful patterns for building production-ready AI agent systems:

1. **AI Developer Workflows (ADW)** - Autonomous multi-step workflows that plan, build, review, and fix code
2. **Multi-Agent Orchestration** - A meta-agent pattern where one agent coordinates specialized sub-agents
3. **Agent Experts** - Self-improving agents that learn from their actions and build domain expertise

---

## 🤖 AI Developer Workflows (ADW)

> **The highest leverage point of agentic coding**: deterministic orchestration meets non-deterministic intelligence.

AI Developer Workflows represent a fundamental shift in how we build with AI agents. The insight is simple but profound:

**Raw agents are unreliable. Raw code is inflexible. Combined, they're unstoppable.**

Traditional software engineering gave us **deterministic workflows**—predictable, repeatable, but rigid. AI agents gave us **non-deterministic intelligence**—creative, adaptive, but unpredictable. ADWs fuse these paradigms: **deterministic Python code orchestrates non-deterministic Claude agents**, giving you the reliability of traditional engineering with the capability of frontier AI.

This is the past and future of engineering, combined as one.

### The Core Insight: Composable Workflow Steps

Each workflow is built from **interchangeable, composable steps**:

```
/plan   : always creates a spec file at a known path
/build  :  agent implements creatively based on spec
/review : always outputs risk-tiered report with PASS/FAIL
/fix    :  agent resolves issues based on review
```

The **orchestration is deterministic** (step order, file paths, status updates, database writes). The **execution is non-deterministic** (agent reasoning, code generation, problem-solving). You get predictable structure with intelligent flexibility.

**Why this outperforms raw agents:**
- Agents can't reliably chain multi-step tasks—they lose context, forget goals, hallucinate state
- ADWs enforce structure: each step has clear inputs, outputs, and success criteria
- Failures are isolated to specific steps, not catastrophic workflow collapses
- This keeps each agent focused on ONE SINGLE TASK. Remember, One Agent, One Prompt, One Purpose.

**Why this outperforms raw code:**
- Traditional automation can't adapt to novel problems or ambiguous requirements
- ADWs leverage frontier model reasoning for creative problem-solving
- The agent handles the hard part (thinking), the code handles the boring part (orchestration)

### Workflow Types

Workflows are **composable**—mix and match steps for your use case:

| Workflow                | Steps | Use Case                                                    |
| ----------------------- | ----- | ----------------------------------------------------------- |
| `plan_build`            | 2     | Quick features—plan the implementation, then build it       |
| `plan_build_review`     | 3     | Quality-focused—adds risk-tiered code review after building |
| `plan_build_review_fix` | 4     | Full automation—automatically fixes issues found in review  |

**Build your own**: Create `adw_<your_workflow>.py` by composing steps. Want `plan_build_test`? Copy a workflow, swap `/review` for `/test`. The pattern is the product.

### How It Works

```
1. TRIGGER   →  User says "start adw: plan_build: Build a todo app"
2. CREATE    →  Backend creates ADW record in PostgreSQL
3. SPAWN     →  Background process: `uv run adws/adw_workflows/adw_plan_build.py --adw-id <uuid>`
4. EXECUTE   →  Workflow runs steps sequentially, each step:
                - Creates an agent record
                - Runs a slash command (/plan, /build, /review, /fix)
                - Logs events to agent_logs table
                - Broadcasts via WebSocket in real-time
5. COMPLETE  →  ADW marked complete/failed, duration recorded
```

### Architecture

```
adws/
├── adw_modules/           # Core infrastructure
│   ├── adw_agent_sdk.py   # Typed Pydantic wrapper for Claude Agent SDK
│   ├── adw_logging.py     # Step lifecycle logging (log_step_start, log_step_end)
│   ├── adw_websockets.py  # Real-time WebSocket broadcasting to frontend
│   ├── adw_summarizer.py  # AI-powered event summaries using Claude Haiku
│   └── adw_database.py    # PostgreSQL operations (agents, logs, ADWs)
│
├── adw_workflows/         # Multi-step workflow implementations
│   ├── adw_plan_build.py           # 2-step: /plan → /build
│   ├── adw_plan_build_review.py    # 3-step: /plan → /build → /review
│   └── adw_plan_build_review_fix.py # 4-step: /plan → /build → /review → /fix
│
└── adw_triggers/          # How workflows get started
    ├── adw_manual_trigger.py  # CLI trigger for testing
    └── adw_scripts.py         # Spawns background processes via `uv run`
```

### The ADW UI: Swimlane Visualization

The frontend provides a **swimlane view** where each ADW displays as a card with:

- **Status indicator**: Pending, In Progress, Completed, Failed (color-coded)
- **Step lanes**: Each step (plan, build, review, fix) gets its own colored lane
- **Event squares**: Every event rendered as a clickable square with icons:
  - 💬 Response (TextBlock)
  - 🛠️ Tool (ToolUseBlock)
  - 🧠 Thinking (ThinkingBlock)
  - 🪝 Hook (PreToolUse, PostToolUse)
  - ⚙️ System (StepStart, StepEnd, Stop)
- **Event detail panel**: Click any square to see the AI-generated summary and payload
- **Real-time updates**: Events appear as they happen via WebSocket

### Starting an ADW

**Via Orchestrator Chat:**
```
start adw: plan_build_review: Create a markdown preview app with live rendering
```

**Via CLI (for testing):**
```bash
uv run adws/adw_triggers/adw_manual_trigger.py \
  "markdown-preview" \
  "plan_build_review" \
  "Create a markdown preview app with live rendering" \
  "/path/to/project"
```

### Key Implementation Details

**Typed Agent SDK Wrapper** (`adw_agent_sdk.py`):
- Pydantic models for all Claude SDK types (QueryInput, HooksConfig, MessageHandlers)
- ModelName enum with OPUS, SONNET, HAIKU aliases
- `query_to_completion()` for full agent runs with hooks
- `quick_prompt()` for fast single-shot queries

**Real-time WebSocket Broadcasting** (`adw_websockets.py`):
- Resilient client that fails silently if server unavailable
- Event types: `adw_created`, `adw_event`, `adw_step_change`, `adw_status`
- Broadcasts flow: ADW Process → Backend WebSocket → All Connected Frontends

**AI Event Summaries** (`adw_summarizer.py`):
- Uses Claude Haiku for cheap, fast summarization
- Generates 1-sentence summaries (50-100 chars) for each event
- Summaries displayed in swimlane UI and event detail panel

### Learn More: Talk to the ADW Expert

Want to understand how ADWs work in this codebase? Ask the ADW agent expert:

```bash
/experts:adw:question "How do I create a new workflow type?"
/experts:adw:question "How does the swimlane UI receive real-time updates?"
/experts:adw:question "What happens when I call start_adw?"
```

The expert has deep knowledge of the ADW architecture, workflows, triggers, UI, and WebSocket integration. It reads from a curated expertise file (`.claude/commands/experts/adw/expertise.yaml`) and validates against the actual codebase to give you accurate, up-to-date answers.

---

## 🧠 Agent Experts

> Finally, agents that actually learn.

The massive problem with agents is this: **your agents forget**. And that means your agents don't learn. Traditional software improves as it's used—storing analytics, patterns, and data that create better algorithms. Agents of today don't.

**Agent Experts** solve this with a three-step workflow that transforms forgetful agents into self-improving specialists.

### The Core Pattern: ACT → LEARN → REUSE

```
ACT    →  Agent takes a useful action (builds, fixes, answers)
LEARN  →  Agent stores new information in its expertise file
REUSE  →  Agent uses that expertise on the next execution
```

The difference between a generic agent and an Agent Expert is simple: **one executes and forgets, the other executes and learns**.

## 📁 Mental Models, Not Sources of Truth

The **expertise file** is your agent's mental model—a data structure that evolves over time. Just like the working memory you have of your codebases, this is NOT another source of truth.

> The code is always the source of truth. The expertise file is your agent's working memory that it validates against the code.

**Key insight**: You don't manually update expertise files. You teach your agents how to learn by writing self-improve prompts. The agent manages its own mental model.

## 🎯 Two Types of Agent Experts

### 1. Codebase Experts

Deploy experts for high-risk or complex areas of your codebase:

| Expert Domain | Use Case                                   |
| ------------- | ------------------------------------------ |
| **Database**  | Schema changes, migrations, query patterns |
| **WebSocket** | Real-time events, streaming architecture   |
| **Billing**   | Payment flows, subscription logic          |
| **Security**  | Auth patterns, permission systems          |

**See implementation**: [`.claude/commands/experts/`](.claude/commands/experts/)

**🥚 Easter Egg - Autocomplete Expert**: A concrete Agent Expert lives inside the orchestrator itself! See [`apps/orchestrator_3_stream/backend/modules/autocomplete_agent.py`](apps/orchestrator_3_stream/backend/modules/autocomplete_agent.py) - it uses the Claude Agent SDK with session persistence and learns from accepted/rejected completions via its own [`expertise.yaml`](apps/orchestrator_3_stream/backend/prompts/experts/orch_autocomplete/expertise.yaml).

For example, each expert can have:
- `expertise.yaml` - The mental model (~600-1000 lines of structured knowledge)
- `question.md` - Query the expert without making changes (reuse)
- `self-improve.md` - Sync expertise against the source of truth (the code) (learn)
- `plan.md` - Create domain-aware implementation plans (reuse)
- `plan_build_improve.md` - Composite prompt chain (or agentic workflow) that plans, builds, and improves the expertise file. (True expert workflow: act → learn → reuse)
- `other.md` - Other prompts that use the expertise file (act or reuse) that specializes in the experts domain.

### 2. Product Experts

Build adaptive user experiences where agents personalize based on behavior:

**See demo**: [`apps/nile/README.md`](apps/nile/README.md) - Adaptive shopping with the ACT → LEARN → REUSE pattern

```
ACT    →  User views product, adds to cart, or checks out
LEARN  →  System updates user's Expertise JSONB in database
REUSE  →  Agent generates personalized home page sections
```

## 🔧 Building Your Own Agent Expert

### Step 1: Create the Expertise File (Mental Model)

```yaml
# .claude/commands/experts/<domain>/expertise.yaml
overview:
  description: "What this system does"
  key_files:
    - "path/to/critical/file.py"

core_implementation:
  # Structure your domain knowledge here
  # Let the agent define and maintain this structure
```

### Step 2: Create the Self-Improve Prompt

The self-improve prompt teaches your agent HOW to learn:

```markdown
# Purpose
Maintain expertise accuracy by comparing against actual codebase.

# Workflow
1. Optionally check git diff for recent changes
2. Read current expertise file
3. Validate against codebase (READ the actual files)
4. Identify discrepancies
5. Update expertise file
6. Enforce line limit (keep it focused)
```

### Step 3: Create Domain-Specific Commands

- **Question prompt**: Query expertise without changes
- **Plan prompt**: Create expertise-informed implementation plans
- **Action prompts**: Domain-specific workflows

### Step 4: Run Self-Improve Until Stable

```bash
# Run until your agent stops finding new things to update
/experts:<domain>:self-improve true
```

## 📂 Expert Files Reference

```
.claude/commands/experts/
├── database/
│   ├── expertise.yaml      # Database mental model
│   ├── question.md         # Query without coding
│   └── self-improve.md     # Sync expertise with code
│
└── websocket/
    ├── expertise.yaml      # WebSocket mental model
    ├── question.md         # Query without coding
    ├── plan.md             # Create WS-aware plans
    ├── self-improve.md     # Sync expertise with code
    └── plan_build_improve.md  # Full workflow: plan → build → update expertise
```

---

## 🤖 Multi-Agent Orchestration

This repository also includes a production-ready orchestration system for deploying and coordinating multiple Agent Experts at scale.

This project provides a **full-stack platform** for orchestrating multiple AI agents through a web interface. An orchestrator agent (powered by the Claude Code ecosystem) manages other specialized agents, coordinating complex multi-agent workflows with:

- 🌐 **Real-time web UI** with WebSocket streaming
- 🗄️ **PostgreSQL database** for persistent state and event logging
- 🤖 **Natural language control** via an orchestrator agent that manages other agents
- 📊 **Comprehensive observability** - every event, cost, and interaction tracked
- 💰 **Automatic cost tracking** with per-agent token usage and USD totals

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Anthropic API key** ([Get one here](https://console.anthropic.com/))
- **PostgreSQL database** - We recommend [NeonDB](https://neon.tech) (free serverless PostgreSQL)

### 2. Create Your Database

**Option A: NeonDB (Recommended - Free Tier Available)**

1. Go to [NeonDB Console](https://console.neon.tech/) and sign up
2. Create a new project (e.g., "multi-agent-orchestration")
3. Copy your connection string - it looks like:
   ```
   postgresql://username:password@ep-xxx-xxx.aws.neon.tech/neondb?sslmode=require
   ```

**Option B: Docker (Quick Local Setup)**

```bash
# Pull and run PostgreSQL in Docker
docker run --name postgres-orch \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=orchestrator \
  -p 5432:5432 \
  -d postgres:15

# Connection string:
# DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/orchestrator
```

**Option C: Local PostgreSQL**

```bash
# Install PostgreSQL (macOS example)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb orchestrator
```

### 3. Setup

```bash
# Install Astral UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Bun (JavaScript runtime and package manager)
curl -fsSL https://bun.sh/install | bash
```

### 4. Configure Environment Variables

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env and set your values:
# - ANTHROPIC_API_KEY (required)
# - DATABASE_URL (required - your PostgreSQL connection string)
code .env

# Copy .env to both application directories
cp .env apps/orchestrator_3_stream/.env
cp .env apps/orchestrator_db/.env
```

**Required Environment Variables:**
```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Database (from NeonDB or your PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 5. Initialize Database

```bash
# Run database migrations (creates all tables, indexes, triggers)
uv run apps/orchestrator_db/run_migrations.py
```

This creates 6 tables:
- `orchestrator_agents` - Singleton orchestrator state
- `agents` - Managed agent registry
- `prompts` - Prompt history
- `agent_logs` - Event logs with AI summaries
- `system_logs` - Application logs
- `orchestrator_chat` - 3-way conversation log

### 6. Start the Application

**Terminal 1 - Backend (FastAPI + Python):**
```bash
cd apps/orchestrator_3_stream
./start_be.sh
# Backend starts on http://127.0.0.1:9403
```

**Terminal 2 - Frontend (Vue 3 + TypeScript):**
```bash
cd apps/orchestrator_3_stream/frontend
bun install  # First time only
cd ..
./start_fe.sh
# Frontend starts on http://127.0.0.1:5175
```

### 7. Open Your Browser

Navigate to **http://127.0.0.1:5175**

You'll see a 3-column interface:
- **Left**: Agent sidebar (agents you create will appear here)
- **Center**: Event stream (real-time log of all agent activities)
- **Right**: Orchestrator chat (send commands in natural language)

### 8. Try It Out!

In the chat interface, type:

```
Create an agent called alice for Python development
```

The orchestrator will:
1. Create a new agent named "alice"
2. Initialize it with Claude SDK
3. Show it in the left sidebar
4. You can now command alice to do tasks!

Then try:
```
Tell alice to create a simple FastAPI hello world app
```

### CLI Options (Backend)

```bash
# Resume existing session (this continues prior state)
uv run python backend/main.py --session sess_abc123...

# Set custom working directory
uv run python backend/main.py --cwd /path/to/project

# Combine both
uv run python backend/main.py --session sess_xyz --cwd /my/project
```

## 🏗️ Architecture


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

### Applications

This repository contains **two main applications**:

#### 1. `apps/orchestrator_3_stream/` - Web Orchestrator (Production)

**Status:** ✅ Fully Functional | E2E Tested | Production Ready

A full-stack web application with:
- **Backend**: FastAPI + asyncpg + Claude Agent SDK
- **Frontend**: Vue 3 + TypeScript + Pinia
- **Real-time**: WebSocket streaming for live updates
- **Persistence**: PostgreSQL with connection pooling
- **Observability**: Comprehensive logging and cost tracking

**Features:**
- Chat with orchestrator agent in natural language
- Create and manage specialized agents
- Real-time event stream showing all agent activities
- Cost tracking (tokens + USD) per agent
- File change tracking with git diffs
- Session persistence and resumption
- Dark theme UI with responsive layout

**Tech Stack:**
```
Frontend: Vue 3, TypeScript, Pinia, Vite
Backend:  Python 3.12, FastAPI, asyncpg, Claude Agent SDK
Database: PostgreSQL (NeonDB)
Real-time: WebSocket
```

#### 2. `apps/orchestrator_db/` - Database Schema & Models

Central database schema and Pydantic models shared across applications.

**Purpose:**
- Single source of truth for database schema
- Type-safe Pydantic models with automatic UUID/JSON conversion
- Idempotent SQL migrations (safe to run multiple times)
- Model synchronization to other apps

**Features:**
- 6 core tables with 36+ performance indexes
- Auto-update triggers for timestamps
- JSONB fields for flexible metadata
- Automatic cost/token accumulation
- AI-generated summaries for all events

### Data Flow

```
User (Browser)
    ↓ HTTP POST /send_chat
Backend (FastAPI)
    ↓ process_user_message()
Orchestrator Agent (Claude SDK)
    ↓ Natural language → Tool calls
Agent Manager (MCP Server)
    ↓ create_agent / command_agent
Command Agents (Claude SDK)
    ↓ Execute tasks
PostgreSQL (Persist)
    ↓ Log events, costs, state
WebSocket (Stream)
    ↓ Real-time updates
Frontend (Vue)
    ↓ Update UI
```

## 📖 How It Works

### Orchestrator Agent Pattern

The system uses a **meta-agent pattern**:

1. **Orchestrator Agent** (Claude Sonnet 4.5) - The "conductor"
   - Interprets natural language commands from you
   - Has access to 8 management tools via MCP server
   - Creates, commands, and monitors other agents
   - Maintains conversation context

2. **Command Agents** (Claude Sonnet/Haiku) - The "performers"
   - Created by orchestrator for specific tasks
   - Execute with specialized system prompts
   - Report status back to orchestrator
   - Can be reused across multiple tasks

3. **Management Tools** (MCP Server)
   ```typescript
   create_agent(name, system_prompt?, model?, template?)
   command_agent(agent_name, command)
   check_agent_status(agent_name)
   list_agents()
   delete_agent(agent_name)
   interrupt_agent(agent_name)
   read_system_logs()
   report_cost()
   ```

### Example Workflows

**Create a specialized agent:**
```
You: Create a code reviewer agent called ReviewBot
Orchestrator: [uses create_agent tool] Created ReviewBot with session xyz
```

**Command an agent:**
```
You: Tell ReviewBot to review the authentication code
Orchestrator: [uses command_agent tool] ReviewBot is analyzing auth files...
```

**Multi-agent collaboration:**
```
You: Create BuilderBot for implementation and TesterBot for testing
Orchestrator: Created both agents
You: Have BuilderBot implement user login, then TesterBot write tests
Orchestrator: [coordinates both agents sequentially]
```

## 🗂️ Project Structure

```
multi-agent-orchestration/
├── .env                          # Root environment config (copy to apps)
├── .env.sample                   # Sample with all available options
│
├── apps/
│   ├── orchestrator_db/          # Database schema & models
│   │   ├── models.py             # Pydantic models (source of truth)
│   │   ├── migrations/           # SQL migration files (0-8)
│   │   │   ├── 0_orchestrator_agents.sql
│   │   │   ├── 1_agents.sql
│   │   │   ├── 2_prompts.sql
│   │   │   ├── 3_agent_logs.sql
│   │   │   ├── 4_system_logs.sql
│   │   │   ├── 5_indexes.sql
│   │   │   ├── 6_functions.sql
│   │   │   ├── 7_triggers.sql
│   │   │   └── 8_orchestrator_chat.sql
│   │   ├── run_migrations.py     # Apply migrations to database
│   │   ├── sync_models.py        # Sync models to apps
│   │   └── README.md             # Database documentation
│   │
│   └── orchestrator_3_stream/    # Web orchestrator application
│       ├── .env                  # App-specific config (copied from root)
│       ├── start_be.sh           # Start backend (port 9403)
│       ├── start_fe.sh           # Start frontend (port 5175)
│       │
│       ├── .claude/              # Claude Code configuration
│       │   ├── agents/           # Specialized sub-agent templates
│       │   │   ├── build-agent.md           # Implements single files from detailed specs in parallel workflows
│       │   │   ├── docs-scraper.md          # Fetches and saves documentation from URLs as markdown
│       │   │   ├── meta-agent.md            # Generates new sub-agent configuration files from descriptions
│       │   │   ├── playwright-validator.md  # Validates web interactions with browser automation and screenshots
│       │   │   ├── review-agent.md          # Analyzes git diffs and produces risk-tiered validation reports
│       │   │   ├── scout-report-suggest.md  # Investigates codebase issues and suggests resolutions (Sonnet)
│       │   │   └── scout-report-suggest-fast.md  # Fast codebase analysis and reporting (Haiku)
│       │   │
│       │   └── commands/         # Slash command workflows
│       │       ├── build.md                # Implements plan top-to-bottom with validation
│       │       ├── load_ai_docs.md         # Scrapes documentation URLs into local markdown files
│       │       ├── orch_one_shot_agent.md  # Creates agent for task, executes, then deletes
│       │       ├── orch_plan_w_scouts_build_review.md  # Three-phase: plan → build → review workflow
│       │       ├── orch_scout_and_build.md # Two-phase: scout problem → build solution workflow
│       │       ├── plan.md                 # Creates detailed implementation specifications
│       │       ├── prime.md                # Analyzes codebase structure and summarizes understanding
│       │       └── question.md             # Answers questions about project without making changes
│       │
│       ├── backend/              # Python FastAPI backend
│       │   ├── main.py           # FastAPI app + WebSocket
│       │   ├── modules/
│       │   │   ├── config.py           # Environment loader
│       │   │   ├── database.py         # PostgreSQL operations
│       │   │   ├── orchestrator_service.py  # Orchestrator logic
│       │   │   ├── agent_manager.py    # Agent lifecycle + MCP tools
│       │   │   ├── websocket_manager.py  # WebSocket broadcasting
│       │   │   └── logger.py           # Hourly rotating logs
│       │   ├── prompts/
│       │   │   └── orchestrator_agent_system_prompt.md
│       │   └── tests/            # Integration tests (5/5 passing)
│       │
│       └── frontend/             # Vue 3 TypeScript frontend
│           ├── src/
│           │   ├── App.vue       # 3-column layout
│           │   ├── components/
│           │   │   ├── AgentList.vue          # Left: agent sidebar
│           │   │   ├── EventStream.vue        # Center: event log
│           │   │   └── OrchestratorChat.vue   # Right: chat
│           │   ├── stores/
│           │   │   └── orchestratorStore.ts   # Pinia state
│           │   └── services/
│           │       ├── api.ts           # HTTP client
│           │       └── chatService.ts   # WebSocket client
│           └── package.json
│
├── CLAUDE.md                     # Engineering rules for AI agents
└── README.md                     # This file
```

## 💡 Key Features

### Real-Time Streaming
- WebSocket broadcasts every agent event
- Chat messages stream as they're generated
- Cost updates appear immediately
- Sub-second latency from backend to UI

### Comprehensive Observability
- **Event Logs**: Every hook, tool use, and response captured
- **AI Summaries**: 15-word summaries for each event
- **File Tracking**: Git diffs for Read/Write/Edit operations
- **Cost Tracking**: Token usage + USD costs per agent
- **Session History**: Load previous conversations from database

### Persistent State
- All interactions saved to PostgreSQL
- Session resumption via `--session` flag
- Chat history loads automatically
- Agent state preserved across restarts

### Type Safety
- Pydantic models for all database operations
- TypeScript interfaces mirror Python models
- Automatic UUID/JSON/Decimal conversion
- Runtime validation on all data

## 🔧 Configuration

### Environment Variables

See `.env.sample` for all available options. Key variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...

# Backend (defaults shown)
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9403

# Frontend (defaults shown)
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175

# Orchestrator
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_WORKING_DIR=/path/to/project

# Database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs
```

## 🧪 Testing

### Backend Tests (No Mocking)

**Philosophy:** Real database + Real Claude SDK

```bash
cd apps/orchestrator_3_stream/backend
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=modules --cov-report=html
```

**Tests (5/5 passing):**
- ✅ Database connection and pool
- ✅ Orchestrator singleton pattern
- ✅ Chat message persistence
- ✅ Session tracking
- ✅ Cost accumulation

### E2E Validation

Validated with Playwright MCP:
- ✅ Frontend loads without errors
- ✅ WebSocket connects successfully
- ✅ Chat history loads from database
- ✅ User can send messages
- ✅ Orchestrator processes and responds
- ✅ Real-time streaming works
- ✅ Messages persist to database

## 📊 Database Schema

### Core Tables

| Table                 | Purpose                      | Key Relationships        |
| --------------------- | ---------------------------- | ------------------------ |
| `orchestrator_agents` | Singleton orchestrator state | None (singleton)         |
| `agents`              | Managed agent registry       | FK → orchestrator_agents |
| `prompts`             | Prompt history               | FK → agents              |
| `agent_logs`          | Unified event log            | FK → agents              |
| `system_logs`         | Application logs             | None                     |
| `orchestrator_chat`   | 3-way conversation log       | FK → orchestrator_agents |

### Key Fields

**orchestrator_agents:**
- `id`, `session_id`, `status`, `working_dir`
- `input_tokens`, `output_tokens`, `total_cost`
- `metadata` (JSONB) - SystemMessage info, slash commands, templates

**agents:**
- `id`, `orchestrator_agent_id`, `name`, `model`
- `session_id`, `status`, `working_dir`
- `input_tokens`, `output_tokens`, `total_cost`

**agent_logs:**
- `agent_id`, `event_category` (hook/response)
- `event_type` (PreToolUse, TextBlock, etc.)
- `content`, `summary` (AI-generated)
- `payload` (JSONB) - Full event data

**orchestrator_chat:**
- `orchestrator_agent_id`, `agent_id`
- `sender_type` (user/orchestrator/agent)
- `receiver_type` (user/orchestrator/agent)
- `message`, `summary`

## 🛠️ Development

### Modifying Database Schema

```bash
# 1. Edit migration file
code apps/orchestrator_db/migrations/X_table.sql

# 2. Run migrations
uv run apps/orchestrator_db/run_migrations.py

# 3. Update models if needed
code apps/orchestrator_db/models.py

# 4. Sync models to apps
uv run apps/orchestrator_db/sync_models.py
```

### Adding New Features

**Backend endpoint:**
1. Add to `apps/orchestrator_3_stream/backend/main.py`
2. Use `app.state.orchestrator_service` for business logic
3. Broadcast events via `app.state.ws_manager`

**Frontend component:**
1. Add to `apps/orchestrator_3_stream/frontend/src/components/`
2. Connect to Pinia store for state
3. Use `chatService` for WebSocket events

**Management tool:**
1. Add to `apps/orchestrator_3_stream/backend/modules/agent_manager.py`
2. Register in `get_management_tools()` function
3. Orchestrator can now use it via MCP

## 🚨 Troubleshooting

### "Database connection failed"
- Check `DATABASE_URL` in `.env`
- Verify database is running
- Run migrations: `uv run apps/orchestrator_db/run_migrations.py`

### "Port already in use"
```bash
# Kill process on backend port
lsof -ti:9403 | xargs kill -9

# Kill process on frontend port
lsof -ti:5175 | xargs kill -9
```

### "ANTHROPIC_API_KEY not found"
- Add to root `.env` file
- Copy `.env` to `apps/orchestrator_3_stream/.env`
- Restart backend

### Frontend won't connect to backend
- Check backend is running on port 9403
- Verify `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors

## 📚 Resources

- **Full-Stack Architecture**: `apps/orchestrator_3_stream/app_docs/full-stack-architecture-summary.md`
- **Database Documentation**: `apps/orchestrator_db/README.md`
- **Application README**: `apps/orchestrator_3_stream/README.md`
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **NeonDB Console**: https://console.neon.tech
