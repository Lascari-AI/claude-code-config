# Spec: Refactor Frontend Direct Database Access

**Session ID**: `refactor-frontend-db-access`
**Created**: 2026-02-13
**Status**: Finalized
**Finalized**: 2026-02-13

---

> **Ready for Planning** - This spec has been reviewed and approved. Use `/plan` to begin implementation planning.

---

## Overview

Refactor the core system architecture to allow the frontend to connect directly to the database using Drizzle ORM, while the backend becomes focused on agent orchestration.

### Current Architecture
```
Frontend (Next.js) → Backend (FastAPI) → PostgreSQL (SQLModel/asyncpg)
                     ├── /projects/*  (CRUD, onboarding, directory browsing)
                     ├── /sessions/*  (CRUD, artifacts: spec.md, plan.json, state.json)
                     └── /agents/*    (list agents, logs for sessions)
```

### Proposed Architecture
```
Frontend (Next.js) → PostgreSQL (via Drizzle - reads, event viewing)
Frontend           → Backend (signaling to create sessions)
Backend (FastAPI)  → PostgreSQL (agent execution writes)
Backend            → Claude SDK (running agents: spec, plan, build, docs, debug)
```

---

## Current System Understanding

### Database: PostgreSQL (SQLModel)
- **Project**: Codebases registered in the system (name, slug, path, onboarding status)
- **Session**: Workflow containers (spec → plan → build → docs lifecycle)
- **Agent**: Individual Claude SDK invocations with resumption support
- **AgentLog**: Execution events for observability (tool calls, responses, phases)

### Backend After Refactor (Minimal)
**REMOVE** - all of these move to frontend:
- All `/projects/*` routes (CRUD, browse, onboard)
- All `/sessions/*` routes (list, get, artifacts)
- All `/agents/*` routes (list, get, logs)

**KEEP** - only essentials:
- `GET /health` - health check
- Future: Agent execution endpoints (trigger, status, cancel)

---

## Initial Understanding

User's vision:
1. **Frontend becomes the primary interface for viewing data**
   - Direct PostgreSQL queries via Drizzle ORM
   - Use `drizzle-kit pull` to sync existing schema to TypeScript types

2. **Frontend responsibilities**:
   - View events (agent logs, session progress)
   - Signal backend to create/start new sessions

3. **Backend responsibilities**:
   - "largely just for running the various agents"
   - Handle session creation when signaled by frontend
   - Orchestrate Claude SDK invocations (spec, plan, build, etc.)

---

## High-Level Goals

1. **Frontend reads directly from PostgreSQL** via Drizzle ORM
2. **Simplify backend** to focus on agent execution (writes, orchestration)
3. **Establish event pipeline architecture** that supports both polling and future WebSocket

---

## Mid-Level Goals

### Frontend (Drizzle)
- Read all database tables: projects, sessions, agents, agent_logs
- Project CRUD (create, update, delete) - frontend has filesystem access
- Directory browsing for onboarding (frontend has fs access)

### Backend (FastAPI/SQLModel)
- Agent execution (creates sessions, agents, logs during runs)
- Writes during agent lifecycle

### Session Storage Architecture

**Filesystem** (stays - agents need to walk the filesystem):
- `spec.md` - Agents read during plan/build phases
- `plan.json` - Agents read during build phase
- `context/`, `debug/`, `research/` - Agent working directories

**Database** (queryable by UI):
- Session metadata, status, stats, timestamps
- Agent execution records, logs
- Possibly: synced/cached artifact content for fast UI access

**Frontend access pattern**:
- Query database via Drizzle for lists, summaries, metadata
- Read filesystem via Next.js API Routes (existing pattern):
  - `/api/browse` - directory browsing (already exists)
  - `/api/validate-path` - path validation (already exists)
  - New: `/api/sessions/[slug]/spec` - read spec.md
  - New: `/api/sessions/[slug]/plan` - read plan.json
  - New: `/api/sessions/[slug]/state` - read state.json

**`state.json`**: Filesystem only for this refactor
- Agent writes via Write tool (simple)
- Frontend reads from filesystem
- Future direction: shift toward DB-centric approach

---

## Constraints

- **Agent SDK understanding needed**: The exact mechanism for running Claude Code headless and managing actions/commands needs investigation. Current understanding:
  - Agent SDK allows running Claude Code without the terminal UI
  - Commands like `/spec`, `/plan`, `/build` would be invoked programmatically
  - Open question: How does action management work? How do we trigger, monitor, and control agent execution?

- **Dependency**: Clarifying Agent SDK capabilities is a prerequisite for finalizing how "frontend signals backend" actually works

---

## Out of Scope

- **Remote deployment**: The agent SDK requires setting `cwd` to run, so this is local-only for now
- Authentication/authorization complexity (local tool, trusted environment)
- **Agent SDK orchestration**: How to trigger/manage agents programmatically is a separate effort
- **Frontend-triggered agent execution**: Will be addressed after this refactor establishes the architecture

---

## Resolved Questions

- ~~Auth for direct DB access?~~ → Local-only, no auth needed
- ~~Which writes stay in backend?~~ → All CRUD moves to frontend, backend only for agent execution
- ~~Real-time updates?~~ → Polling baseline, WebSocket for live viewing, design for both
- ~~Trigger mechanism for sessions?~~ → Out of scope for this refactor (Agent SDK investigation separate)

---

## Decisions Log

1. **Local-only deployment** - Remote deployment is out of scope because the Claude Agent SDK requires setting `cwd` to run agents. This means:
   - No need for connection security/auth between frontend and database
   - Drizzle can connect directly from Next.js server components
   - Simplified architecture

2. **Filesystem artifacts stay in filesystem** - Agents need to walk the codebase and read spec.md, plan.json, etc. These can't move to DB-only. Frontend reads filesystem directly for artifact content.

3. **state.json stays filesystem-only** (for now) - Agent writes it easily, frontend reads from filesystem. Future refactors may shift to DB-centric.

4. **Schema ownership**: SQLModel (Python) is source of truth
   - Schema changes happen in Python → alembic migrations → PostgreSQL
   - `drizzle-kit pull` generates TypeScript types from live DB
   - Frontend uses generated Drizzle schema to query

5. **Minimal backend** - Backend exists purely for agent execution
   - All reads: Frontend (Drizzle + filesystem)
   - All project CRUD: Frontend (Drizzle + filesystem)
   - Directory browsing: Frontend (has fs access)
   - Backend keeps: Health check, agent execution endpoints (future)
   - Philosophy: If we hit issues, can move things back, but start minimal

6. **Real-time updates approach**:
   - **Polling as baseline** - Simple, no rate limit concerns for local use
   - **WebSocket for live viewing** - Debugging, watching interesting executions
   - **Usage pattern**: Mix of both
     - *Live*: Debugging sessions, watching complex builds unfold
     - *Background*: Long-running sessions (hours), come back to review
   - **Architecture**: Event pipeline that writes to DB (source of truth) and optionally broadcasts to WebSocket
   - **Implementation order**: Design for WebSocket from start, can implement polling first
