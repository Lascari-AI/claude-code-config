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

### Checkpoint Structuring: Tracer Bullet Approach

Structure checkpoints as **vertical slices** (end-to-end), not horizontal layers. This approach—from "The Pragmatic Programmer"—builds a thin, working end-to-end implementation first, then incrementally adds complexity.

**Why Tracer Bullet?**
- Validates the entire pipeline works before investing heavily
- Enables testing and verification from checkpoint 1
- Catches integration issues early, not at the end
- Each checkpoint produces working, testable code

```
❌ AVOID: Layer-by-layer (horizontal slicing)
┌─────────────────────────────────────────────────────┐
│ Checkpoint 1: All data models                       │
│ Checkpoint 2: All API endpoints                     │
│ Checkpoint 3: All UI components                     │
│ Checkpoint 4: Integration testing  ← too late!      │
└─────────────────────────────────────────────────────┘

✅ PREFER: Tracer bullet (vertical slicing)
┌─────────────────────────────────────────────────────┐
│ Checkpoint 1: One complete flow (model→API→UI)      │
│               Minimal but WORKING end-to-end        │
│ Checkpoint 2: Add second flow or enhance first      │
│ Checkpoint 3: Add complexity to working system      │
│ Checkpoint 4: Polish, edge cases, refinement        │
└─────────────────────────────────────────────────────┘
```

**Key Principle**: After checkpoint 1, you should have something that works end-to-end, even if minimal. Each subsequent checkpoint adds to that working foundation rather than building components in isolation.

**Example - Building a User Export Feature:**

```
❌ Horizontal approach:
  1. Create all export format handlers (CSV, JSON, PDF)
  2. Build the export API endpoint
  3. Create the UI export dialog
  4. Test everything together

✅ Tracer bullet approach:
  1. Export ONE user to CSV (model→service→API→UI→download)
  2. Add JSON format to working flow
  3. Add PDF format to working flow
  4. Add batch export, progress tracking, error handling
```

The tracer bullet approach ensures each checkpoint is independently testable and validates assumptions early.

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

### Self-Contained Task Design

> **Core Principle**: Every task and task group must be executable by an agent in a completely new session with zero prior context.

The task object itself should contain everything needed to execute it:
- **File references**: All paths to read, modify, or create
- **Context**: `read_before` specifies what to understand first
- **Actions**: Precise IDK commands that are unambiguous
- **Dependencies**: Explicit `depends_on` if ordering matters

**Why This Matters - Fault Recovery**:

If execution breaks at Checkpoint 2, Task Group 1, Task 4:
```
❌ Without self-contained tasks:
   → Restart entire session
   → Re-read all context
   → Redo completed work

✅ With self-contained tasks:
   → Load task 2.1.4 directly
   → Task has all file refs and context
   → Execute just that task
   → Continue from 2.1.5
```

**Design Test**: Can an agent with only the task object (no session history) execute this task correctly? If yes, the task is properly designed.

```
┌─────────────────────────────────────────────────────────────────┐
│  SELF-CONTAINED TASK CHECKLIST                                  │
├─────────────────────────────────────────────────────────────────┤
│  ✓ file_path specifies exact target file                        │
│  ✓ read_before lists all files needed for context               │
│  ✓ actions use precise IDK commands (no ambiguity)              │
│  ✓ description explains WHAT and WHY                            │
│  ✓ No implicit knowledge required from prior tasks              │
└─────────────────────────────────────────────────────────────────┘
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
