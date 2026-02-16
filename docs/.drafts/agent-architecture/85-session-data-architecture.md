# Session Data Architecture

How session data flows between filesystem and database, what owns what, and how sync works.

> **Implementation Status**: ✅ Implemented in session `2026-02-14_claude-code-agent-sdk-integration`
> - StateManager: `apps/core/backend/state_manager/`
> - MCP Tools: `apps/core/backend/mcp_tools/session_tools.py`
> - Sync Functions: `apps/core/session_db/sync.py`

---

## The Core Tension

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   AGENT WORLD                              UI/QUERY WORLD                   │
│   ───────────                              ───────────────                  │
│                                                                             │
│   Claude Code / Agent SDK                  Frontend / API                   │
│   writes to FILESYSTEM                     reads from DATABASE              │
│                                                                             │
│   ┌─────────────────────┐                  ┌─────────────────────┐          │
│   │ agents/sessions/    │                  │ PostgreSQL          │          │
│   │ ├── state.json      │                  │ ├── sessions        │          │
│   │ ├── spec.md         │      ???         │ ├── agents          │          │
│   │ ├── plan.json       │  ◄───────────►   │ └── agent_logs      │          │
│   │ └── research/       │                  │                     │          │
│   └─────────────────────┘                  └─────────────────────┘          │
│                                                                             │
│   WHY FILESYSTEM:                          WHY DATABASE:                    │
│   • Agents grep/read/walk naturally        • Fast queries (no fs scan)     │
│   • Git version control                    • Project FK relationships       │
│   • Portable (moves with code)             • Aggregations (costs, counts)  │
│   • No network dependency                  • UI reactivity                 │
│   • Works offline                          • Cross-project views           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Ownership Model

### Principle: Single Source of Truth Per Data Type

Each piece of data has ONE authoritative source. The other location is a cache/mirror.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA OWNERSHIP MATRIX                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FILESYSTEM OWNS (Agent-written, content-heavy)                            │
│   ─────────────────────────────────────────────                             │
│   • spec.md           - Unstructured interview output                       │
│   • plan.json         - Checkpoint structure, tasks                         │
│   • plan.md           - Human-readable plan (generated)                     │
│   • research/         - Research artifacts                                  │
│   • debug/            - Debug investigation artifacts                       │
│   • context/          - Diagrams, notes                                     │
│                                                                             │
│   DATABASE OWNS (Execution state, relationships)                            │
│   ───────────────────────────────────────────────                           │
│   • agent runs        - Individual agent invocations                        │
│   • agent_logs        - Hook events, tool calls, timing                     │
│   • costs/tokens      - Aggregated usage                                    │
│   • project_id FK     - Which project this session belongs to               │
│   • sdk_session_id    - Claude SDK session for resumption                   │
│                                                                             │
│   SHARED (Exists in both, needs sync strategy)                              │
│   ────────────────────────────────────────────                              │
│   • session identity  - session_slug, title, description                    │
│   • session status    - current phase (spec, plan, build, complete)         │
│   • checkpoint progress - total/completed counts                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Shared Data Problem

### state.json vs sessions table

Both contain similar fields:

```
state.json                              sessions table
──────────                              ──────────────
session_id                        →     session_slug
current_phase                     →     status
phases.spec.status                →     (derived from status)
phases.plan.status                →     (derived from status)
goals.high_level                  →     metadata.goals (optional)
open_questions                    →     metadata.open_questions (optional)
key_decisions                     →     metadata.key_decisions (optional)
plan_state.checkpoints_total      →     checkpoints_total
plan_state.checkpoints_completed  →     checkpoints_completed
```

### Resolution: Filesystem is Source of Truth for Session State

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   state.json (AUTHORITATIVE)              sessions table (MIRROR)           │
│   ──────────────────────────              ───────────────────────           │
│                                                                             │
│   Agent writes here naturally             Populated by sync process          │
│   No API calls needed                     Enables UI queries                 │
│   Works offline                           Enables project linking            │
│   Git-tracked                             Fast aggregations                  │
│                                                                             │
│   Session skill does:                     Sync process does:                 │
│   1. Write state.json                     1. Read state.json                 │
│   2. (optional) Trigger sync              2. Update sessions table           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Rationale**: Agents should write to filesystem naturally. Forcing API calls for every state update:
- Adds network dependency
- Makes offline work impossible
- Adds latency to agent operations
- Requires error handling for API failures

---

## Sync Strategies

### Option A: Event-Triggered Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT-TRIGGERED SYNC                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Session skill writes state.json                                           │
│         │                                                                   │
│         ▼                                                                   │
│   Post-write hook (optional)                                                │
│         │                                                                   │
│         ▼                                                                   │
│   POST /api/sessions/sync                                                   │
│   {                                                                         │
│     "session_slug": "2026-02-14_my-feature",                                │
│     "working_dir": "/path/to/project",                                      │
│     "event": "state_updated"                                                │
│   }                                                                         │
│         │                                                                   │
│         ▼                                                                   │
│   Backend reads state.json from working_dir                                 │
│         │                                                                   │
│         ▼                                                                   │
│   Upserts sessions table                                                    │
│                                                                             │
│   PROS:                           CONS:                                     │
│   • Near real-time UI updates     • Requires API call from skill            │
│   • Clear trigger points          • Network dependency                      │
│   • Can batch updates             • Skill complexity increases              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Option B: Phase-Transition Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE-TRANSITION SYNC                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Sync only at major transitions:                                           │
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  CREATE  │───►│   SPEC   │───►│   PLAN   │───►│  BUILD   │───► ...     │
│   │          │    │ FINALIZE │    │ FINALIZE │    │ COMPLETE │             │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│        │               │               │               │                    │
│        ▼               ▼               ▼               ▼                    │
│      SYNC            SYNC            SYNC            SYNC                   │
│                                                                             │
│   PROS:                           CONS:                                     │
│   • Fewer sync points             • UI stale during phases                  │
│   • Natural integration points    • Progress not visible until complete     │
│   • Less API chatter              • Checkpoint progress delayed             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Option C: Pull-Based / On-Demand Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PULL-BASED SYNC                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   UI requests sync when needed:                                             │
│                                                                             │
│   User opens project                                                        │
│         │                                                                   │
│         ▼                                                                   │
│   GET /api/projects/{id}/sessions?sync=true                                 │
│         │                                                                   │
│         ▼                                                                   │
│   Backend scans {working_dir}/agents/sessions/                              │
│         │                                                                   │
│         ▼                                                                   │
│   For each session_slug:                                                    │
│     - Read state.json                                                       │
│     - Upsert sessions table                                                 │
│         │                                                                   │
│         ▼                                                                   │
│   Return synced session list                                                │
│                                                                             │
│   PROS:                           CONS:                                     │
│   • No agent changes needed       • Eventual consistency                    │
│   • Works with existing skills    • Scan can be slow for many sessions      │
│   • Simple to implement           • Not real-time                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Option D: Hybrid (Recommended)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID SYNC                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Combine approaches:                                                       │
│                                                                             │
│   1. PULL-BASED as baseline                                                 │
│      - Scan on project open                                                 │
│      - "Refresh" button in UI                                               │
│      - Periodic background job (optional)                                   │
│                                                                             │
│   2. EVENT-TRIGGERED for key moments                                        │
│      - Session create (new session appears immediately)                     │
│      - Phase complete (status updates in UI)                                │
│      - Session complete (final state captured)                              │
│                                                                             │
│   3. PHASE-TRANSITION as optimization                                       │
│      - Skip intermediate state updates                                      │
│      - Reduce API chatter during spec interview                             │
│                                                                             │
│   Result:                                                                   │
│   • Sessions appear immediately on create                                   │
│   • Major status changes reflected quickly                                  │
│   • Full resync available on demand                                         │
│   • Works offline (sync when reconnected)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sync Implementation

### The Sync Function

```python
def sync_session_from_filesystem(
    working_dir: str,
    session_slug: str,
    project_id: UUID | None = None
) -> Session:
    """
    Read state.json and upsert to database.

    Filesystem is source of truth - database is updated to match.
    """
    session_dir = Path(working_dir) / "agents/sessions" / session_slug
    state_path = session_dir / "state.json"

    if not state_path.exists():
        raise SessionNotFound(session_slug)

    state = json.loads(state_path.read_text())

    # Map state.json to database fields
    session_data = SessionCreate(
        session_slug=session_slug,
        title=state.get("topic"),
        description=state.get("description"),
        status=map_phase_to_status(state.get("current_phase")),
        session_type=state.get("granularity", "full"),
        working_dir=working_dir,
        session_dir=str(session_dir),

        # Artifact existence checks
        spec_exists=(session_dir / "spec.md").exists(),
        plan_exists=(session_dir / "plan.json").exists(),

        # Checkpoint progress
        checkpoints_total=state.get("plan_state", {}).get("checkpoints_total", 0),
        checkpoints_completed=len(state.get("plan_state", {}).get("checkpoints_completed", [])),

        # Metadata (goals, decisions, etc.)
        metadata={
            "goals": state.get("goals"),
            "key_decisions": state.get("key_decisions"),
            "open_questions": state.get("open_questions"),
        }
    )

    # Upsert to database
    return db.upsert_session(session_data, project_id=project_id)
```

### Status Mapping

```python
def map_phase_to_status(current_phase: str) -> SessionStatus:
    """Map state.json current_phase to database status."""
    mapping = {
        "spec": "spec",
        "plan": "plan",
        "build": "build",
        "docs": "docs",
        "complete": "complete",
    }
    return mapping.get(current_phase, "created")
```

---

## Project ↔ Session Relationship

### The Linking Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   PROJECT (database)                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ id: uuid                                                            │   │
│   │ name: "My App"                                                      │   │
│   │ working_dir: "/Users/ford/projects/my-app"  ◄── Path to codebase    │   │
│   │ ...                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   SESSIONS (filesystem)                                                     │
│   /Users/ford/projects/my-app/agents/sessions/                              │
│   ├── 2026-02-14_auth-feature/                                              │
│   │   └── state.json                                                        │
│   ├── 2026-02-10_api-refactor/                                              │
│   │   └── state.json                                                        │
│   └── 2026-02-08_bugfix-login/                                              │
│       └── state.json                                                        │
│                                                                             │
│   QUESTION: How does database know about these sessions?                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Solution: Project Owns Working Dir, Sessions Discovered/Synced

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   projects table                          sessions table                    │
│   ──────────────                          ──────────────                    │
│   id (PK)                                 id (PK)                           │
│   name                                    project_id (FK) ◄─── LINK         │
│   working_dir ───────────┐                session_slug                      │
│   ...                    │                working_dir ◄─── REDUNDANT        │
│                          │                session_dir     (for convenience) │
│                          │                ...                               │
│                          │                                                  │
│                          │                                                  │
│   Discovery/Sync:        │                                                  │
│   ──────────────         │                                                  │
│   1. Project has         │                                                  │
│      working_dir ────────┘                                                  │
│                                                                             │
│   2. Scan: {working_dir}/agents/sessions/*/state.json                       │
│                                                                             │
│   3. For each session found:                                                │
│      - Read state.json                                                      │
│      - Upsert to sessions table with project_id FK                          │
│                                                                             │
│   4. Sessions now queryable:                                                │
│      SELECT * FROM sessions WHERE project_id = ?                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Execution Tracking

### Where Agent Runs Live

Agent execution data is **database-owned** because:
- Agents may run from backend (Agent SDK)
- Multiple agents per session
- Need SDK session IDs for resumption
- Hook events are high-volume (not suitable for filesystem)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   SESSION (filesystem state.json + database record)                         │
│         │                                                                   │
│         │ 1:N                                                               │
│         ▼                                                                   │
│   AGENT RUNS (database only)                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ id: uuid                                                            │   │
│   │ session_id: FK → sessions                                           │   │
│   │ agent_type: "spec" | "plan" | "build" | "research" | "docs"         │   │
│   │ sdk_session_id: "sess_abc123..."  ◄── For Claude SDK resume         │   │
│   │ model: "claude-sonnet-4-5"                                          │   │
│   │ status: "executing" | "complete" | "failed"                         │   │
│   │ input_tokens: 15000                                                 │   │
│   │ output_tokens: 3000                                                 │   │
│   │ cost: 0.42                                                          │   │
│   │ checkpoint_id: 2  ◄── For build agents                              │   │
│   │ ...                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         │ 1:N                                                               │
│         ▼                                                                   │
│   AGENT LOGS (database only)                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ id: uuid                                                            │   │
│   │ agent_id: FK → agents                                               │   │
│   │ event_type: "PreToolUse" | "PostToolUse" | "TextBlock" | ...        │   │
│   │ tool_name: "Edit"                                                   │   │
│   │ payload: { ... }                                                    │   │
│   │ timestamp: "2026-02-14T10:30:00Z"                                   │   │
│   │ ...                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When Agents Run from CLI vs Backend

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CLI MODE (current)                      BACKEND MODE (future)             │
│   ──────────────────                      ─────────────────────             │
│                                                                             │
│   User runs /session:spec                 User clicks "Start Spec" in UI    │
│         │                                       │                           │
│         ▼                                       ▼                           │
│   Claude Code CLI                         Backend API                       │
│         │                                       │                           │
│         ▼                                       ▼                           │
│   Session skill executes                  Agent SDK spawns agent            │
│         │                                       │                           │
│         ▼                                       ▼                           │
│   Writes state.json                       Creates agent record in DB        │
│   Writes spec.md                          Hooks log to agent_logs           │
│         │                                 Writes state.json + spec.md       │
│         ▼                                       │                           │
│   (No agent record in DB)                       ▼                           │
│   (No hook logging)                       Agent record tracks execution     │
│         │                                       │                           │
│         ▼                                       ▼                           │
│   Manual sync needed                      Automatic - already in DB         │
│                                                                             │
│   QUESTION: Should CLI mode also create agent records?                      │
│   ANSWER: Optional. Core workflow works without it.                         │
│           Add later for unified observability.                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: What Lives Where

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINAL OWNERSHIP MODEL                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FILESYSTEM (Source of Truth)                                              │
│   ────────────────────────────                                              │
│   agents/sessions/{slug}/                                                   │
│   ├── state.json      ◄── Session state, phases, goals, decisions          │
│   ├── spec.md         ◄── Spec content (unstructured)                       │
│   ├── plan.json       ◄── Plan structure (checkpoints, tasks)               │
│   ├── plan.md         ◄── Human-readable plan                               │
│   ├── research/       ◄── Research artifacts                                │
│   └── debug/          ◄── Debug artifacts                                   │
│                                                                             │
│   DATABASE (Mirror + Extensions)                                            │
│   ──────────────────────────────                                            │
│   sessions                                                                  │
│   ├── Core fields     ◄── MIRRORED from state.json via sync                 │
│   ├── project_id FK   ◄── EXTENSION: links to project                       │
│   ├── total_cost      ◄── EXTENSION: aggregated from agents                 │
│   └── total_tokens    ◄── EXTENSION: aggregated from agents                 │
│                                                                             │
│   agents                                                                    │
│   └── (all fields)    ◄── DATABASE ONLY: execution tracking                 │
│                                                                             │
│   agent_logs                                                                │
│   └── (all fields)    ◄── DATABASE ONLY: hook events, observability         │
│                                                                             │
│   SYNC STRATEGY: Hybrid                                                     │
│   ─────────────────────                                                     │
│   • Pull-based on project open (scan filesystem)                            │
│   • Event-triggered on session create and phase complete                    │
│   • Refresh button in UI for manual sync                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### StateManager (Python Class)

The `SessionStateManager` class is the **only interface** for modifying `state.json`. Located at `apps/core/backend/state_manager/state_manager.py`.

```python
from state_manager import SessionStateManager, Phase, Status

manager = SessionStateManager(Path("/path/to/session"))
state = manager.load()

# Phase transitions (validated)
manager.transition_to_phase(Phase.plan)  # spec → plan

# Build progress tracking
manager.init_build_progress(checkpoints_total=5)
manager.start_checkpoint(1)
manager.complete_checkpoint(1)

# Commit tracking
manager.add_commit(sha="abc1234", message="feat: add X", checkpoint=1)

# Status and git context
manager.set_status(Status.paused)
manager.set_git_branch("feature/my-feature")
```

**Valid Phase Transitions:**
```
spec → plan → build → docs → complete
                  └──→ complete (skip docs)
```

### MCP Tools for SDK Agents

Located at `apps/core/backend/mcp_tools/session_tools.py`. These tools wrap StateManager for use via Claude Agent SDK:

| Tool | Purpose |
|------|---------|
| `session_transition_phase` | Transition session to new phase |
| `session_init_build` | Initialize build progress (set checkpoint count) |
| `session_start_checkpoint` | Set current active checkpoint |
| `session_complete_checkpoint` | Mark checkpoint complete, auto-advance |
| `session_add_commit` | Record git commit with optional checkpoint link |
| `session_set_status` | Set execution status (active/paused/complete/failed) |
| `session_set_git` | Set branch and/or worktree |

**Example MCP tool call:**
```json
{
  "tool": "session_transition_phase",
  "args": {
    "session_dir": "/path/to/agents/sessions/2026-02-14_my-feature",
    "new_phase": "build"
  }
}
```

### Filesystem → Database Sync

Located at `apps/core/session_db/sync.py`. Provides three levels of sync:

| Function | Use Case |
|----------|----------|
| `sync_session_from_filesystem()` | Sync a single session |
| `onboard_project_sessions()` | Scan and sync all sessions in a project |
| `sync_all_sessions_in_project()` | Full sync with error reporting |

**Sync is upsert-based**: Creates new sessions or updates existing ones.

**V1 → V2 Compatibility**: Sync functions handle both state.json schema versions:
- V1: Uses `phases.*.status` and `plan_state`
- V2: Uses `phase_history` and `build_progress`

```python
from session_db.sync import sync_session_from_filesystem

async with get_async_session() as db:
    session = await sync_session_from_filesystem(
        db=db,
        working_dir="/path/to/project",
        session_slug="2026-02-14_my-feature",
        project_id=project_uuid,  # Optional
    )
```

---

## state.json v2 Schema

The v2 schema is minimal and programmatically-managed:

```json
{
  "$schema": "Session state manifest v2",
  "session_id": "2026-02-14_my-feature",
  "topic": "Add feature X",
  "description": "Brief description",
  "session_type": "full",
  "created_at": "2026-02-14T10:00:00Z",
  "updated_at": "2026-02-14T14:30:00Z",
  "current_phase": "build",
  "status": "active",
  "phase_history": {
    "spec_started_at": "...",
    "spec_completed_at": "...",
    "plan_started_at": "...",
    "plan_completed_at": "...",
    "build_started_at": "...",
    "build_completed_at": null
  },
  "build_progress": {
    "checkpoints_total": 5,
    "checkpoints_completed": [1, 2],
    "current_checkpoint": 3
  },
  "git": {
    "branch": "feature/my-feature",
    "worktree": null,
    "base_branch": "main"
  },
  "commits": [
    {"sha": "abc1234", "message": "feat: X", "checkpoint": 1, "created_at": "..."}
  ],
  "artifacts": {
    "spec": "spec.md",
    "plan": "plan.json",
    "plan_readable": "plan.md"
  }
}
```

**Key Changes from V1:**
- Goals, open_questions, key_decisions → moved to `spec.md`
- `phases` object → replaced by `phase_history` timestamps
- `plan_state` → replaced by `build_progress`
- Updates via StateManager/MCP tools only (no direct AI editing)

---

## Open Questions

- [ ] Should CLI-mode agents also create database agent records for observability?
- [ ] How to handle session deletion - cascade from filesystem or database?
- [ ] Should state.json include a `synced_at` timestamp to detect drift?
- [ ] Do we need a `sync_status` field in sessions table (synced, stale, conflict)?

---

*Updated 2026-02-16 - Added implementation details*
*Draft v1 - 2026-02-14*
