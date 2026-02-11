# Spec: Build Initial Management UI

**Session ID**: `2026-02-11_build-initial-management-ui_mn3z2n`
**Status**: ✅ Finalized
**Created**: 2026-02-11
**Finalized**: 2026-02-11

---

## Overview

Building the initial management UI for the LAI Claude Code Config system, inspired by the orchestrator_3_stream reference implementation.

## Context: What Already Exists

### In This Codebase (apps/core/)
- **session_db/** - SQLModel database models for:
  - **Session**: Workflow container (spec → plan → build → docs)
  - **Agent**: Individual SDK invocations with resumption support
  - **AgentLog**: Unified event log (hooks, responses, phases)
- Async PostgreSQL support via asyncpg
- CRUD operations for all models
- Alembic migration infrastructure (ready but no migrations yet)

### Reference Implementation (orchestrator_3_stream)
- **Frontend**: Vue 3 + TypeScript + Pinia (3-column layout)
- **Backend**: FastAPI + asyncpg + WebSocket manager
- **Database**: PostgreSQL with JSONB metadata fields
- **Real-time**: WebSocket event streaming
- **ADW**: Swimlane workflows with plan → build → review → fix

### Agent Architecture Drafts
- docs/.drafts/agent-architecture/ defines the full vision
- Session lifecycle: SPEC → PLAN → BUILD → DOCS
- Agent taxonomy: Orchestrator → Session agents → Utility agents
- Hybrid storage: Files for artifacts, DB for execution state

---

## Initial Understanding

The UI will provide visibility and control over:
1. **Sessions** - View/manage spec → plan → build → docs workflows
2. **Agents** - See agent status, costs, logs in real-time
3. **Events** - Stream of tool calls, responses, thinking blocks
4. **Observability** - Full traceability of what agents are doing

---

## High-Level Goals

1. **Session Dashboard MVP** - View and manage sessions without an orchestrator
2. **Event Stream** - Leverage existing universal hook logger, adapt to write to database
3. **Swimlane Visualization** - Session flows grouped by project
4. **Project Onboarding** - Bring codebases into the managed system

---

## Mid-Level Goals

- **Project Management**
  - Onboard new projects (codebases/repos) into the system
  - Project statuses to track lifecycle
  - List projects as top-level navigation

- **Session Management**
  - Sessions belong to a project
  - Click project → see sessions for that project
  - Click session → drill down to agents and events

- **Event Stream**
  - Hook logger writes to database (not just JSONL)
  - Swimlane view showing session phase progression (SPEC → PLAN → BUILD → DOCS)

---

## Data Model Evolution

### New: Project Model
A **Project** represents a codebase that has been onboarded into the managed system.

```
Project
├── id (UUID)
├── name (string) - Human-friendly name
├── slug (string) - URL-safe identifier
├── path (string) - Absolute path to codebase root
├── repo_url (string, optional) - GitHub/GitLab URL
├── status (enum) - Project lifecycle status
├── onboarding_status (JSON) - Track onboarding steps completed
├── metadata (JSON) - Extensible config
└── timestamps
```

**Project Statuses**:
- `pending` - Registered but not yet set up
- `onboarding` - Setup in progress
- `active` - Fully managed, sessions can be created
- `paused` - Temporarily inactive
- `archived` - No longer managed

### Onboarding Steps (Tracked in `onboarding_status`)

The SDK loads skills/agents/hooks relative to `cwd`. For a project to use LAI config's capabilities:

| Step | Description | Required? |
|------|-------------|-----------|
| `path_validated` | Project path exists and is accessible | Yes |
| `claude_dir_exists` | `.claude/` directory exists in project | Yes |
| `settings_configured` | `.claude/settings.json` has hook logger | MVP |
| `skills_linked` | Core skills symlinked/copied to project | Future |
| `agents_linked` | Core agents symlinked/copied to project | Future |
| `docs_foundation` | Documentation interview completed | Future |

**MVP Scope**: Just validate path and check for `.claude/` directory. Track steps completed for future automation.

```json
{
  "onboarding_status": {
    "path_validated": true,
    "claude_dir_exists": true,
    "settings_configured": false,
    "skills_linked": false,
    "agents_linked": false,
    "docs_foundation": false
  }
}
```

### Updated: Session Model
Add `project_id` foreign key to link sessions to their project.

```
Session
├── project_id (UUID, FK) - Which project this session belongs to
├── ... existing fields ...
```

---

## Hierarchy

```
Projects (codebases)
└── Sessions (spec/plan/build workflows)
    └── Agents (individual SDK invocations)
        └── AgentLogs (events, tool calls, responses)
```

---

## What Already Exists

### Universal Hook Logger
Location: `.claude/hooks/logging/universal_hook_logger.py`

Currently captures to JSONL files:
- **Events**: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, etc.
- **Output**: `agents/logging/hook_logs/{session_id}/{hook_name}.jsonl`
- **Format**: `{"timestamp": "...", "payload": {...}}`

### Context Bundle Builder
Location: `.claude/hooks/logging/context_bundle_builder.py`

Captures file operations and prompts:
- **Output**: `agents/logging/context_bundles/{DAY_HOUR}_{session_id}.jsonl`
- 200+ existing JSONL files showing active logging

### Database Models (session_db)
- Session, Agent, AgentLog models ready
- Async CRUD operations
- PostgreSQL + asyncpg infrastructure

---

## UI Structure

### Project View (Swimlane)
Sessions as horizontal lanes, each progressing through phases:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Project: LAI-claude-code-config                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Session: build-initial-management-ui                                    │
│ ┌──────────┬──────────┬──────────┬──────────┐                          │
│ │   SPEC   │   PLAN   │  BUILD   │   DOCS   │                          │
│ │    ✓     │    ●     │          │          │  ← Click phase to drill  │
│ └──────────┴──────────┴──────────┴──────────┘                          │
│                                                                         │
│ Session: agent-session-overhaul                                         │
│ ┌──────────┬──────────┬──────────┬──────────┐                          │
│ │   SPEC   │   PLAN   │  BUILD   │   DOCS   │                          │
│ │    ✓     │    ✓     │    ✓     │    ✓     │                          │
│ └──────────┴──────────┴──────────┴──────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Legend: ✓ = complete, ● = in progress, (empty) = not started
```

### Phase Drill-Down (Click into a phase)

| Phase | What it shows |
|-------|---------------|
| **SPEC** | Rendered `spec.md` - the requirements document |
| **PLAN** | Rendered `plan.json` - checkpoints, tasks, visual hierarchy |
| **BUILD** | Agents list with status, events/logs from build phase |
| **DOCS** | What documentation was updated (or "no updates needed") |

### Navigation Flow

```
Projects List
    └── Project View (swimlane of sessions)
            └── Phase View (SPEC / PLAN / BUILD / DOCS)
                    └── (For BUILD) Agent Detail with events
```

---

## Requirements

### Backend (FastAPI API)
- **Projects**: CRUD endpoints
- **Sessions**: List by project, get with phase details
- **Agents**: List by session, get with events
- **Events**: List by agent or session (from database)
- Hook logger adaptation to write to database

### Frontend (React + Next.js)
- **Framework**: Next.js (App Router)
- **State**: Zustand store
- **Styling**: TBD (Tailwind? shadcn/ui?)
- Projects list (simple cards or table)
- Project swimlane view (sessions as lanes)
- Phase views (spec renderer, plan renderer, build agents list, docs summary)
- Basic status indicators and navigation

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Frontend** | Next.js (App Router) | React-based, familiar ecosystem |
| **State** | Zustand | Lightweight, simple API |
| **Styling** | TBD | Tailwind + shadcn/ui likely |
| **Backend** | FastAPI | Async Python, matches existing session_db |
| **Database** | PostgreSQL | Existing models in apps/core/session_db |
| **ORM** | SQLModel | Already in place |
| **Real-time** | WebSocket | Future - not MVP |

---

## Constraints

- **No orchestrator** - MVP is read/observe only; sessions managed via CLI
- **No real-time WebSocket** - Can be added post-MVP
- **Leverage existing infrastructure** - session_db models, hook logger

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| No orchestrator for now | MVP focus - sessions managed via CLI, UI is read/observe |
| Leverage existing hook logger | Already capturing events, just need DB bridge |
| Project as first-class entity | Codebases are onboarded, sessions belong to projects |
| Onboarding steps tracked in model | Future automation ready - track path_validated, claude_dir_exists, etc. |
| Swimlane = sessions as lanes | Project view shows sessions progressing through phases |
| React + Next.js + Zustand | User preference, familiar ecosystem |
| Dual-write for hook logger | Keep JSONL + write to DB for MVP stability |
| Tailwind + shadcn/ui | Quick to build, well-documented component library |

---

## Out of Scope (Future)

- Real-time WebSocket streaming
- Full onboarding automation (skills/agents symlinking)
- Documentation foundation interview during onboarding
- Orchestrator integration for creating/managing sessions from UI
- ADW-style workflow execution

---

_Spec finalized - ready for planning_
