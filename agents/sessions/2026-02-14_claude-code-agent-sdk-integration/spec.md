# Spec: Session Data Architecture

**Session ID**: `2026-02-14_claude-code-agent-sdk-integration`
**Created**: 2026-02-14
**Status**: Finalized - Ready for Plan

---

## Overview

This spec focuses on **how to represent session data** across the system's two storage paradigms:

1. **Filesystem** - What Claude Code/Agent SDK naturally writes to (spec.md, plan.json, state.json)
2. **Database** - Structured data for UI queries, project linking, cost tracking

The core tension: Agent SDK writes to codebases. Forcing structured function calls for unstructured things like specs is not optimal. Yet we need database sync for UI visibility.

## Problem Space

### The Fundamental Tension

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  AGENT SDK / CLAUDE CODE                      UI / QUERIES                  │
│  ───────────────────────                      ────────────                  │
│                                                                             │
│  Writes to FILESYSTEM:                        Reads from DATABASE:          │
│  - spec.md (unstructured)                     - Session list by project     │
│  - plan.json (structured)                     - Status, progress            │
│  - state.json (structured)                    - Cost tracking               │
│  - research/ (artifacts)                      - Agent execution logs        │
│                                                                             │
│  WHY FILESYSTEM:                              WHY DATABASE:                 │
│  - Agents grep, read, walk                    - Fast queries (no fs scan)  │
│  - Natural for code writing                   - Project linking (FK)        │
│  - Version control (git)                      - UI reactivity              │
│  - Portable (move with codebase)              - Cross-project aggregation  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      THE GAP: NO SYNC                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What Exists Today

**Filesystem (source of truth for artifacts):**
```
agents/sessions/{session_slug}/
├── state.json     # Session state (phase, status, goals, decisions)
├── spec.md        # What we're building (unstructured, agent-written)
├── plan.json      # How we're building it (checkpoints, tasks)
├── plan.md        # Human-readable plan (generated from plan.json)
├── research/      # Research artifacts
└── debug/         # Debug investigation artifacts
```

**Database (draft models in docs/.drafts/agent-architecture/90-database-models.md):**
- `sessions` table - workflow tracking, project FK, costs, status
- `agents` table - individual agent instances, SDK session IDs
- `agent_logs` table - hook events, tool calls, observability

### The Insight: state.json IS essentially a database record

```
state.json fields                    Database Session fields
──────────────────                   ──────────────────────
session_id                    →      session_slug
current_phase                 →      status
phases.spec.status            →      (derived)
phases.plan.status            →      (derived)
goals.high_level              →      metadata.goals
open_questions                →      metadata.open_questions
key_decisions                 →      metadata.key_decisions
```

The question: **What's the relationship?** Duplicate? Sync? Reference?

## High-Level Goals

1. **Define Clear Data Ownership**: What lives where and why
2. **Design Sync Strategy**: How filesystem and database stay in sync
3. **Enable UI Visibility**: Without breaking agent workflows
4. **Support Multi-Project**: Sessions linked to projects across codebases

## Existing Documentation

Significant work already exists in `docs/.drafts/agent-architecture/`:
- `00-overview.md` - System overview
- `core-session-phases/` - Spec, Plan, Build, Docs-update phases
- `90-database-models.md` - Pydantic models for Session, Agent, AgentLog

The database models doc already establishes the **Hybrid Storage** pattern:
- **Codebase (Files)**: Source of truth for work artifacts agents read/write
- **Database**: Source of truth for execution events, timing, costs, agent state

## Core Design Questions

### 1. What's the relationship between state.json and database Session?

**Option A: state.json is primary, database is cache**
- Agent writes to state.json (natural workflow)
- Sync process reads state.json → updates database
- Database is derived, can be rebuilt from filesystem

**Option B: Database is primary, state.json is convenience**
- Agent writes to database via API
- state.json generated from database for agent convenience
- Source of truth in database

**Option C: Split ownership**
- state.json owns: session metadata, goals, decisions, open questions
- Database owns: execution events, costs, agent SDK session IDs, project FK
- Some fields duplicated for convenience

### 2. When does sync happen?

**Option A: On every write (real-time)**
- Session skill calls API after each state.json update
- Pro: UI always current
- Con: More complex skill, network dependency

**Option B: On phase transitions**
- Sync on: session create, spec finalize, plan finalize, build complete
- Pro: Simpler, fewer sync points
- Con: UI may be stale during phases

**Option C: On demand / pull-based**
- UI requests sync when viewing a project
- Background job scans filesystem periodically
- Pro: No agent changes needed
- Con: Eventual consistency

### 3. What's source of truth for what?

| Data Type | Filesystem | Database | Notes |
|-----------|------------|----------|-------|
| Spec content | ✓ | | Unstructured, agent writes directly |
| Plan structure | ✓ | | Checkpoints, tasks - agent writes |
| Session status | ? | ? | **UNCLEAR** - both have it |
| Goals/decisions | ✓ | mirror? | In state.json, useful for queries? |
| Execution events | | ✓ | Hook events, tool calls |
| Costs/tokens | | ✓ | Aggregated from agent runs |
| Project link | | ✓ | FK relationship |
| Agent SDK session ID | | ✓ | For resumption |

### 4. Project ↔ Session relationship

```
Current structure:
  project (database) → working_dir (filesystem path)
  session (filesystem) → agents/sessions/{slug}/

Question: How does project know about sessions?

Option A: Scan on demand
  - Project has working_dir
  - Scan {working_dir}/agents/sessions/ when needed
  - No FK, dynamic discovery

Option B: Session has project_id FK
  - When session created, link to project
  - Query: SELECT * FROM sessions WHERE project_id = ?
  - Requires session to exist in database
```

## Key Decisions

1. **Artifacts stay on filesystem, metadata syncs to DB**
   - Rationale: Agents need direct file access to spec.md, plan.json. Database handles visibility and tracking.
   - Source: SESSION_SYNC_ISSUE.md, database-models.md

2. **state.json is essentially structured data that could live in DB**
   - But keeping it in filesystem allows grep, portability, git tracking
   - Needs clearer definition of ownership

## Documentation Draft

Started comprehensive draft at:
**`docs/.drafts/agent-architecture/85-session-data-architecture.md`**

Covers:
- Data ownership model (filesystem vs database)
- Sync strategies (event-triggered, phase-transition, pull-based, hybrid)
- Project ↔ Session relationship
- Agent execution tracking (CLI mode vs backend mode)

## Resolved Decisions

### 1. Filesystem is Source of Truth (Portable Sessions)

**Decision**: Filesystem owns session state. Database is a reconstructable index.

**Rationale**:
- Sessions should be portable - clone a repo, onboard sessions into any system
- No dependency on original database to understand or resume work
- Database can be blown away and reconstructed from filesystem anytime

### 2. state.json Becomes Minimal Manifest (Programmatic Updates Only)

**Decision**: Simplify state.json to machine-readable manifest. No AI direct editing.

**Rationale**:
- Goals, open_questions, key_decisions move to spec.md (human-readable, AI-editable)
- state.json becomes tracking-only: phase, progress, commits, timestamps
- Updates via hooks (automatic) and MCP tools (explicit)
- Enables structured, validated state transitions

### 3. Database is Query Layer + Execution Tracking

**Decision**: Database stores:
- Session index (mirrored from state.json via onboarding)
- Agent runs (database-only, SDK invocations)
- Agent logs (database-only, execution events)

**Rationale**:
- No bidirectional sync needed
- Onboarding = scan filesystem → populate database
- Agents/logs are ephemeral execution data, not needed for portability

### 4. Update Mechanisms

**Decision**:
- Hooks for automatic updates (updated_at on file changes)
- MCP tools for explicit state changes (phase transitions, checkpoint completion, commits)

**Rationale**:
- Semantic transitions (plan→build) can't be detected by hooks
- AI calls MCP tool when it knows it's transitioning
- Python StateManager class handles the actual state.json updates

---

## state.json v2 Specification

### Design Principles

1. **Programmatic updates only** - No direct AI editing of state.json
2. **Minimal schema** - Only what's needed for tracking and onboarding
3. **Content in artifacts** - Goals, questions, decisions live in spec.md
4. **Portable** - Filesystem is source of truth, database reconstructable
5. **Explicit artifact references** - For UI rendering

### Schema

```json
{
  "$schema": "Session state manifest v2 - programmatic updates only",

  // ─── Identity ─────────────────────────────────────────────────────────────
  "session_id": "2026-02-14_feature-dark-mode_a1b2c3",
  "topic": "Implement dark mode",
  "description": "Add dark mode toggle with system preference detection",
  "session_type": "full",

  // ─── Timestamps (auto-updated by hooks) ───────────────────────────────────
  "created_at": "2026-02-14T10:00:00Z",
  "updated_at": "2026-02-14T14:30:00Z",

  // ─── Current State (updated by MCP tools / state manager) ─────────────────
  "current_phase": "build",
  "status": "active",

  // ─── Phase History (updated by state manager on transitions) ──────────────
  "phase_history": {
    "spec_started_at": "2026-02-14T10:00:00Z",
    "spec_completed_at": "2026-02-14T11:30:00Z",
    "plan_started_at": "2026-02-14T11:30:00Z",
    "plan_completed_at": "2026-02-14T12:00:00Z",
    "build_started_at": "2026-02-14T12:00:00Z",
    "build_completed_at": null,
    "docs_started_at": null,
    "docs_completed_at": null
  },

  // ─── Build Progress (updated by state manager as checkpoints complete) ────
  "build_progress": {
    "checkpoints_total": 5,
    "checkpoints_completed": [1, 2],
    "current_checkpoint": 3
  },

  // ─── Git Context (set at session create, updated if worktree changes) ─────
  "git": {
    "branch": "feature/dark-mode",
    "worktree": null,
    "base_branch": "main"
  },

  // ─── Commits (updated by state manager when commits are made) ─────────────
  "commits": [
    {
      "sha": "abc1234",
      "message": "feat: add theme provider component",
      "checkpoint": 1,
      "created_at": "2026-02-14T13:00:00Z"
    }
  ],

  // ─── Artifact References (explicit for UI rendering) ──────────────────────
  "artifacts": {
    "spec": "spec.md",
    "plan": "plan.json",
    "plan_readable": "plan.md"
  }
}
```

### Field Reference

| Field | Type | Updated By | Purpose |
|-------|------|------------|---------|
| `session_id` | string | Create only | Unique identifier (folder name) |
| `topic` | string | Create only | Human-readable title |
| `description` | string | Create only | Brief description |
| `session_type` | enum | Create only | `full` \| `quick` \| `research` |
| `created_at` | datetime | Create only | Session creation timestamp |
| `updated_at` | datetime | Hook (auto) | Last modification timestamp |
| `current_phase` | enum | MCP/StateManager | `spec` \| `plan` \| `build` \| `docs` \| `complete` |
| `status` | enum | MCP/StateManager | `active` \| `paused` \| `complete` \| `failed` |
| `phase_history` | object | MCP/StateManager | Timestamps for each phase transition |
| `build_progress` | object | MCP/StateManager | Checkpoint tracking during build |
| `git` | object | MCP/StateManager | Branch and worktree info |
| `commits` | array | MCP/StateManager | Commits made during session |
| `artifacts` | object | Create only | Paths to session artifacts |

### What Moves to spec.md

These fields are **removed from state.json** and now live in spec.md:

**Goals** → Markdown sections (High-Level, Mid-Level, Implementation)
**Open Questions** → Checkbox list in spec.md
**Key Decisions** → Structured markdown with rationale

Example spec.md sections:
```markdown
## Goals

### High-Level Goals
- User can toggle between light and dark mode

### Mid-Level Goals
- Theme provider wraps application
- Toggle persists to localStorage

## Open Questions

- [ ] Should we support custom accent colors?
- [x] Per-device or sync across devices? → Per-device

## Key Decisions

### Use CSS variables over Tailwind dark: prefix
**Rationale**: More flexible for runtime switching
**Made**: 2026-02-14
```

---

## State Manager (Python Class)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATE MANAGER PATTERN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  class SessionStateManager:                                                 │
│      def __init__(self, session_dir: Path)                                  │
│      def load(self) -> SessionState                                         │
│      def save(self) -> None                                                 │
│                                                                             │
│      # Phase transitions                                                    │
│      def transition_to_phase(self, phase: Phase) -> None                    │
│      def complete_phase(self, phase: Phase) -> None                         │
│                                                                             │
│      # Build progress                                                       │
│      def start_checkpoint(self, checkpoint_id: int) -> None                 │
│      def complete_checkpoint(self, checkpoint_id: int) -> None              │
│                                                                             │
│      # Git tracking                                                         │
│      def set_git_branch(self, branch: str) -> None                          │
│      def set_git_worktree(self, worktree: Path) -> None                     │
│                                                                             │
│      # Commits                                                              │
│      def add_commit(self, sha: str, message: str, checkpoint: int) -> None  │
│                                                                             │
│      # Status                                                               │
│      def set_status(self, status: Status) -> None                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MCP Tools Required

| Tool | Params | Action |
|------|--------|--------|
| `session_transition_phase` | session_id, new_phase | Update current_phase, set phase_history timestamps |
| `session_complete_checkpoint` | session_id, checkpoint_id | Add to checkpoints_completed, update current_checkpoint |
| `session_add_commit` | session_id, sha, message, checkpoint | Append to commits array |
| `session_set_status` | session_id, status | Update status field |
| `session_update_git` | session_id, branch?, worktree? | Update git object fields |

---

## Breaking Changes

> **WARNING**: This requires updates to many prompts and flows.

### Affected Components

| Component | Change Required |
|-----------|-----------------|
| `.claude/skills/session/spec/skill.md` | Remove state.json goals/questions/decisions updates |
| `.claude/skills/session/plan/skill.md` | Remove state.json update instructions |
| `.claude/skills/session/build/skill.md` | Replace state updates with MCP tool calls |
| `.claude/skills/session/spec/templates/state.json` | Replace with v2 schema |
| `.claude/skills/session/spec/templates/spec.md` | Add Goals, Open Questions, Key Decisions sections |
| Any prompt mentioning "update state.json" | Replace with MCP tool usage |

### Migration Path

1. Create StateManager Python class
2. Create MCP tools that use StateManager
3. Update state.json template to v2 schema
4. Update spec.md template with new sections
5. Update all skill prompts
6. Test full session flow

---

## Database Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE ↔ FILESYSTEM RELATIONSHIP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FILESYSTEM (Source of Truth)                                               │
│  agents/sessions/{slug}/                                                    │
│  ├── state.json      ◄── Portable session manifest                         │
│  ├── spec.md         ◄── Content: goals, questions, decisions              │
│  ├── plan.json       ◄── Checkpoint structure                              │
│  └── plan.md         ◄── Human-readable plan                               │
│                                                                             │
│  DATABASE (Query Index + Execution Tracking)                                │
│  sessions table:                                                            │
│  ├── Populated by ONBOARDING (reading state.json)                           │
│  ├── Links session to project via working_dir                               │
│  └── Can be reconstructed anytime from filesystem                           │
│                                                                             │
│  agents / agent_logs tables:                                                │
│  ├── Database-only (execution tracking)                                     │
│  ├── Created when SDK agents run                                            │
│  └── Not needed for session portability                                     │
│                                                                             │
│  ONBOARDING FLOW:                                                           │
│  1. Scan {working_dir}/agents/sessions/*/                                   │
│  2. Read each state.json                                                    │
│  3. Upsert to sessions table                                                │
│  4. Link to project via working_dir match                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Resolved Questions

- [x] **Should `updated_at` be updated by hook or by StateManager on every save?**
  → **Hook** for automatic updates when any session file changes. StateManager focuses on explicit state changes.

- [x] **Do we need a `version` field in state.json for schema migrations?**
  → **Not initially**. Can add later if migration complexity arises. Start simple.

- [x] **Should StateManager validate state transitions?**
  → **Yes**. Reducer-style methods with validation prevent invalid states (e.g., can't skip from spec to build).
