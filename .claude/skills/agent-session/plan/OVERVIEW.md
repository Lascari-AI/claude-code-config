# Plan Phase

Design HOW to implement the finalized spec using checkpoint-based planning.

## Purpose

The plan phase builds the **bridge** from current state to desired state:
- Analyzes existing codebase
- Designs checkpoint sequence
- Creates detailed tasks with IDK definitions
- Establishes testing strategy per checkpoint

## Prerequisites

- Finalized spec (`phases.spec.status: "finalized"` in state.json)
- Session in plan phase (`current_phase: "plan"`)

## Workflow

### Tiered Progressive Confirmation

```
┌─────────────────────────────────────────────────────────────────┐
│  PLAN PHASE - Tiered Approach                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TIER 1: Checkpoint Outline                                     │
│  ─────────────────────────────                                  │
│  1. Read finalized spec                                         │
│  2. Generate checkpoint outline (titles, goals, order)          │
│  3. ─► User confirms outline                                    │
│                                                                 │
│  TIER 2: Task Groups (per checkpoint)                           │
│  ─────────────────────────────────────                          │
│  4. For Checkpoint N:                                           │
│     a. Generate task groups (titles, objectives)                │
│     b. ─► User confirms task groups                             │
│                                                                 │
│  TIER 3: Tasks (per task group)                                 │
│  ──────────────────────────────                                 │
│  5. For Task Group N.M:                                         │
│     a. Generate tasks (title, description, file_path)           │
│     b. ─► User confirms tasks                                   │
│                                                                 │
│  TIER 4: Actions (per task)                                     │
│  ─────────────────────────────                                  │
│  6. For Task N.M.P:                                             │
│     a. Generate actions (IDK commands)                          │
│     b. ─► User confirms actions                                 │
│                                                                 │
│  7. Repeat Tiers 2-4 for remaining checkpoints                  │
│                                                                 │
│  8. Finalize plan                                               │
│     └── All checkpoints detailed, ready for build               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Progressive disclosure with confirmation gates at each tier. Don't generate everything upfront - build detail incrementally with user validation.

### State Tracking

The `plan_state` in state.json tracks progress for resumability:

```json
{
  "plan_state": {
    "status": "in_progress",
    "current_checkpoint": 2,
    "current_task_group": "2.1",
    "current_task": "2.1.1",
    "last_updated": "2026-01-01T12:00:00Z"
  }
}
```

## Key Concepts

### Checkpoints

Sequential milestones that incrementally move from current state to target state.

```json
{
  "id": 1,
  "title": "Implement Core Types",
  "goal": "Create foundational data types",
  "prerequisites": [],
  "status": "pending"
}
```

### Task Groups

Objective-based grouping of tasks within a checkpoint.

```json
{
  "id": "1.1",
  "title": "Set up data layer",
  "objective": "Create foundational data models and repository",
  "status": "pending",
  "tasks": [...]
}
```

### Actions

File-scoped atomic operations within a task. Each action uses IDK format.

```json
{
  "id": "1.1.1.1",
  "command": "CREATE TYPE User with fields: id, name, email",
  "file": "src/types/user.ts",
  "status": "pending"
}
```

### Tasks

Units of work containing one or more actions. Uses IDK format for precise commands.

```json
{
  "id": "1.1.1",
  "title": "Define User type",
  "file_path": "src/types/user.ts",
  "context": { "read_before": [...] },
  "actions": [
    { "id": "1.1.1.1", "command": "CREATE TYPE User...", "file": "src/types/user.ts", "status": "pending" }
  ]
}
```

## IDK Reference

Information-Dense Keywords for precise task definitions:

| Category | Keywords | File |
|----------|----------|------|
| **CRUD** | CREATE, UPDATE, DELETE | [idk/crud.md](idk/crud.md) |
| **Actions** | ADD, REMOVE, MOVE, REPLACE, MIRROR, MAKE, USE, APPEND | [idk/actions.md](idk/actions.md) |
| **Language** | VAR, FUNCTION, CLASS, TYPE, FILE, DEFAULT | [idk/language.md](idk/language.md) |
| **Location** | BEFORE, AFTER | [idk/location.md](idk/location.md) |
| **Refactoring** | REFACTOR, RENAME, SPLIT, MERGE, EXTRACT, INLINE, INSERT, WRAP | [idk/refactoring.md](idk/refactoring.md) |
| **Testing** | TEST, ASSERT, MOCK, VERIFY, CHECK | [idk/testing.md](idk/testing.md) |
| **Documentation** | COMMENT, DOCSTRING, ANNOTATE | [idk/documentation.md](idk/documentation.md) |

## File Context Tracking

Each checkpoint tracks beginning and ending file states:

```json
{
  "file_context": {
    "beginning": {
      "files": [{ "path": "...", "status": "exists" }],
      "tree": "ASCII tree visualization"
    },
    "ending": {
      "files": [{ "path": "...", "status": "new" }],
      "tree": "ASCII tree visualization"
    }
  }
}
```

## Testing Strategy

Each checkpoint includes verification approach:

```json
{
  "testing_strategy": {
    "approach": "Type checking and unit tests",
    "verification_steps": [
      "Run tsc --noEmit",
      "Run jest src/types/__tests__"
    ]
  }
}
```

## Commands

| Command | Description |
|---------|-------------|
| `/session:plan [session-id]` | Start/resume planning |
| `/session:plan [session-id] finalize` | Finalize plan for build |

## Outputs

- `plan.json` - Structured plan (source of truth)
- `plan.md` - Human-readable plan (generated)
- `state.json` - Updated with `plan_state`

## Templates

- [plan.json](templates/plan.json) - Plan structure template

## Reference

- [models.py](reference/models.py) - Pydantic models for type-safe plan structure

## Scripts

- [sync-plan-md.py](scripts/sync-plan-md.py) - Auto-generates plan.md from plan.json (triggered via PostToolUse hook)
