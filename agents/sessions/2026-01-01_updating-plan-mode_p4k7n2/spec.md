# Updating Plan Mode

> **Session**: `2026-01-01_updating-plan-mode_p4k7n2`
> **Status**: ✅ Finalized
> **Created**: 2026-01-01
> **Finalized**: 2026-01-01

## Overview

Update the session workflow across all three phases (spec, plan, build) to support:
1. **Structured prior spec referencing** in spec phase
2. **Tiered progressive confirmation** in plan phase
3. **Checkpoint-at-a-time execution with commit boundaries** in build phase

This builds on the hierarchy restructure (Tranche → Task Group, Subtask → Action) to create a coherent end-to-end flow.

## Problem Statement

The current plan structure uses **Tranches** as parallel-executable task groups within checkpoints. In practice, this doesn't work well:

1. **Parallelizability is hard to determine** - Whether tasks can truly run in parallel without conflicts is difficult to predict during planning
2. **Merge conflict risk** - Parallel execution risks file conflicts that are hard to resolve
3. **Conceptual mismatch** - The "parallel execution" framing doesn't match how work actually gets done

The hierarchy needs to be restructured around a clearer mental model that maps to the actual development workflow (commits, objectives, edits).

## Proposed Hierarchy

Restructure the plan hierarchy to map to actual development workflow:

```
Plan (Feature / PR)
└── Checkpoint (Commit-level milestone)
    └── Task Group (Objective/section - e.g., "set up controllers")
        └── Task (Individual deliverable - e.g., "user endpoint")
            └── Action (File-scoped atomic operation)
```

### Level Definitions

| Level | Purpose | Example | Granularity |
|-------|---------|---------|-------------|
| **Plan** | The entire feature/PR being built | "Add user authentication" | 1 per session |
| **Checkpoint** | Commit-level milestone | "Implement API layer" | 3-7 per plan |
| **Task Group** | Logical objective within checkpoint | "Set up endpoints" | 1-5 per checkpoint |
| **Task** | Individual deliverable | "Create /users endpoint" | 1-10 per group |
| **Action** | File-scoped atomic operation | "Add route handler" | 1-5 per task |

### Concrete Example

```
Checkpoint 1: "Implement User API"
├── Task Group 1.1: "Set up data layer"
│   ├── Task 1.1.1: "Create User model"
│   │   ├── Action: CREATE src/models/user.ts
│   │   └── Action: ADD validation schema
│   └── Task 1.1.2: "Create User repository"
│       └── Action: CREATE src/repos/userRepo.ts
│
├── Task Group 1.2: "Set up controllers"
│   └── Task 1.2.1: "Create UserController"
│       ├── Action: CREATE src/controllers/userController.ts
│       └── Action: ADD CRUD methods
│
└── Task Group 1.3: "Set up endpoints"
    ├── Task 1.3.1: "GET /users endpoint"
    │   └── Action: ADD route in src/routes/users.ts
    └── Task 1.3.2: "POST /users endpoint"
        └── Action: ADD route in src/routes/users.ts
```

### Key Changes from Current Structure

| Aspect | Before (Tranche) | After (Task Group) |
|--------|------------------|-------------------|
| **Semantics** | "Parallel-executable group" | "Logical objective" |
| **Purpose** | Execution optimization | Organization & clarity |
| **Naming** | Tranche (obscure) | Task Group (intuitive) |
| **Subtask** | Nested breakdown | → **Action** (file-scoped operation) |

### Action Structure

Actions are structured objects with hierarchical IDs, IDK commands, status tracking, and file scope:

```json
{
  "id": "1.1.1.1",
  "command": "CREATE User type with id, email, name fields",
  "file": "src/models/user.ts",
  "status": "pending"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Hierarchical ID (checkpoint.group.task.action) |
| `command` | Yes | IDK-formatted instruction |
| `file` | Yes | Target file path |
| `status` | Yes | pending / in_progress / complete / blocked |

#### Example Task with Actions

```json
{
  "id": "1.1.1",
  "title": "Create User model",
  "file_path": "src/models/user.ts",
  "description": "Define User type with validation",
  "actions": [
    {
      "id": "1.1.1.1",
      "command": "CREATE User type with id, email, name, createdAt fields",
      "file": "src/models/user.ts",
      "status": "pending"
    },
    {
      "id": "1.1.1.2",
      "command": "ADD zod validation schema UserSchema",
      "file": "src/models/user.ts",
      "status": "pending"
    },
    {
      "id": "1.1.1.3",
      "command": "ADD export statements",
      "file": "src/models/user.ts",
      "status": "pending"
    }
  ],
  "status": "pending"
}

## End-to-End Workflow

### Mental Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CURRENT STATE                              DESIRED STATE                  │
│   (codebase now)                             (spec defines)                 │
│                                                                             │
│        ┌───────┐                                  ┌───────┐                 │
│        │  v1   │ ════════════════════════════▶   │  v2   │                 │
│        └───────┘          THE PLAN               └───────┘                 │
│                          (the bridge)                                       │
│                                                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Checkpoint 1  ──────── commit                         │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 2  ──────── commit                         │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 3  ──────── commit                         │
│                    └─────────────────────┘                                  │
│                                                                             │
│   SPEC = Destination    PLAN = Bridge    BUILD = Walking the bridge        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Spec (Define the Destination)

```
┌─────────────────────────────────────────────────────────────────┐
│  SPEC PHASE                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Start new session OR resume existing                        │
│     │                                                           │
│  2. ─► "Are there prior specs to reference?"                    │
│     │   └── Link relevant prior sessions (structured)           │
│     │                                                           │
│  3. Question-driven exploration                                 │
│     │   └── Ask → Answer → Update spec.md → Repeat              │
│     │                                                           │
│  4. Finalize spec                                               │
│     └── Lock spec, ready for plan phase                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**New: Structured Prior Spec Referencing**
- When starting a new spec, prompt: "Are there prior specs important for context?"
- Store references in `state.json` (like `prior_session` field we added)
- Agent reads prior spec(s) to understand continuity

### Phase 2: Plan (Build the Bridge) - Tiered Progressive Confirmation

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
│  4. For Checkpoint 1:                                           │
│     a. Generate task groups (titles, objectives)                │
│     b. ─► User confirms task groups                             │
│                                                                 │
│  TIER 3: Tasks (per task group)                                 │
│  ──────────────────────────────                                 │
│  5. For Task Group 1.1:                                         │
│     a. Generate tasks (title, description, file_path)           │
│     b. ─► User confirms tasks                                   │
│                                                                 │
│  TIER 4: Actions (per task)                                     │
│  ─────────────────────────────                                  │
│  6. For Task 1.1.1:                                             │
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

### Phase 3: Build (Walk the Bridge) - Checkpoint-at-a-Time

```
┌─────────────────────────────────────────────────────────────────┐
│  BUILD PHASE - One Checkpoint at a Time                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each Checkpoint:                                           │
│  ────────────────────                                           │
│                                                                 │
│  1. Read checkpoint file_context.beginning files                │
│     │                                                           │
│  2. Find first non-complete Task Group                          │
│     │                                                           │
│  3. For each Task in Task Group:                                │
│     │   a. Read task.context.read_before files                  │
│     │   b. Execute actions in order                             │
│     │   c. Update action status → task status → group status    │
│     │                                                           │
│  4. Repeat step 2-3 until all Task Groups complete              │
│     │                                                           │
│  5. Run testing_strategy.verification_steps                     │
│     │                                                           │
│  6. ─► COMMIT (checkpoint = commit boundary)                    │
│     │                                                           │
│  7. Update checkpoint status to complete                        │
│     │                                                           │
│  8. ─► Output command for next checkpoint (DO NOT auto-run)     │
│     └── "Run `/build {session-id}` to continue to Checkpoint 2" │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principles**:
- **Checkpoint = Commit**: Each checkpoint ends with a git commit
- **No auto-continuation**: After commit, output the command to run next checkpoint - let user decide when to continue
- **Resumable**: If interrupted, pick up from first non-complete action

## Design Principles

### Async-First / Resumable Execution

The plan structure is designed to support **asynchronous, resumable execution**:

- **Self-contained state**: A new agent can pick up execution from the plan alone, without needing prior conversation context
- **Fail-safe resumption**: If execution fails or is interrupted, easy to resume from exactly where we left off
- **Status at every level**: Explicit status tracking enables quick assessment of progress without parsing children

This is a **core design principle** - the plan is the source of truth for execution state.

```
New Agent Picks Up Plan:
┌─────────────────────────────────────────────────────────────┐
│  1. Read plan.json                                          │
│  2. Find first non-complete Checkpoint                      │
│  3. Find first non-complete Task Group within it            │
│  4. Find first non-complete Task within it                  │
│  5. Find first pending Action → Execute                     │
│  6. Update status, continue                                 │
└─────────────────────────────────────────────────────────────┘
```

## Goals

### High-Level Goals

Restructure the plan hierarchy to be clearer, more intuitive, mapped to git workflow, and **fully resumable by any agent**.

### Mid-Level Goals

**Hierarchy Restructure:**
1. **Replace Tranche with Task Group** - Shift from parallel-execution semantics to objective-based grouping
2. **Rename Subtask to Action** - Clarify that these are file-scoped atomic operations
3. **Maintain 4-level depth** - Checkpoint → Task Group → Task → Action provides right granularity
4. **Status at every level** - Enable async pickup and progress tracking
5. **Update plan.json schema** - Reflect new hierarchy structure

**Spec Phase Updates:**
6. **Structured prior spec referencing** - Prompt for and store links to relevant prior sessions

**Plan Phase Updates:**
7. **Tiered progressive confirmation** - Generate and confirm at each level (checkpoints → task groups → tasks → actions)
8. **State-aware single command** - `/session:plan [id]` detects current tier and continues

**Build Phase Updates:**
9. **Checkpoint-at-a-time execution** - Complete one checkpoint fully before moving to next
10. **Checkpoint = Commit boundary** - Each completed checkpoint results in a git commit
11. **No auto-continuation** - Output command for next checkpoint, don't auto-run

### Detailed Goals

*Granular requirements (to be added as understanding develops)*

## Proposed Plan Structure (Full Schema)

### Current vs Proposed Comparison

| Current | Proposed | Change |
|---------|----------|--------|
| `tranches[]` | `task_groups[]` | Renamed, semantic shift |
| `tranche.goal` | `task_group.objective` | Renamed for clarity |
| `task.action` (single IDK string) | `task.actions[]` (array of Action objects) | Restructured |
| `task.subtasks[]` | Removed | Replaced by `actions[]` |
| `task.context` | Keep | Unchanged |
| `task.depends_on` | Keep | Unchanged |

### Proposed plan.json Template

```json
{
  "$schema": "Plan schema for session checkpoint-based planning (v2)",

  "session_id": "{{SESSION_ID}}",
  "spec_reference": "./spec.md",
  "created_at": "{{CREATED_AT}}",
  "updated_at": "{{UPDATED_AT}}",
  "status": "draft",

  "checkpoints": [
    {
      "id": 1,
      "title": "{{CHECKPOINT_TITLE}}",
      "goal": "{{CHECKPOINT_GOAL}}",
      "prerequisites": [],
      "status": "pending",

      "file_context": {
        "beginning": {
          "files": [
            {
              "path": "{{FILE_PATH}}",
              "status": "exists",
              "description": "{{FILE_DESCRIPTION}}"
            }
          ],
          "tree": "{{ASCII_TREE}}"
        },
        "ending": {
          "files": [
            {
              "path": "{{FILE_PATH}}",
              "status": "new",
              "description": "{{FILE_DESCRIPTION}}"
            }
          ],
          "tree": "{{ASCII_TREE}}"
        }
      },

      "testing_strategy": {
        "approach": "{{TESTING_APPROACH}}",
        "verification_steps": [
          "{{VERIFICATION_COMMAND}}"
        ]
      },

      "task_groups": [
        {
          "id": "1.1",
          "title": "{{TASK_GROUP_TITLE}}",
          "objective": "{{TASK_GROUP_OBJECTIVE}}",
          "status": "pending",
          "tasks": [
            {
              "id": "1.1.1",
              "title": "{{TASK_TITLE}}",
              "description": "{{TASK_DESCRIPTION}}",
              "file_path": "{{PRIMARY_FILE_PATH}}",
              "status": "pending",
              "context": {
                "read_before": [
                  {
                    "file": "{{CONTEXT_FILE}}",
                    "lines": "{{LINE_RANGE}}",
                    "purpose": "{{WHY_READ_THIS}}"
                  }
                ],
                "related_files": [
                  "{{RELATED_FILE}}"
                ]
              },
              "depends_on": [],
              "actions": [
                {
                  "id": "1.1.1.1",
                  "command": "{{IDK_COMMAND}}",
                  "file": "{{TARGET_FILE}}",
                  "status": "pending"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Concrete Example (Populated)

```json
{
  "$schema": "Plan schema for session checkpoint-based planning (v2)",

  "session_id": "2026-01-01_user-auth-feature_abc123",
  "spec_reference": "./spec.md",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "status": "in_progress",

  "checkpoints": [
    {
      "id": 1,
      "title": "Implement User Data Layer",
      "goal": "Create User model, types, and repository",
      "prerequisites": [],
      "status": "in_progress",

      "file_context": {
        "beginning": {
          "files": [
            { "path": "src/types/index.ts", "status": "exists", "description": "Current type definitions" }
          ],
          "tree": "src/\n├── types/\n│   └── index.ts\n└── services/"
        },
        "ending": {
          "files": [
            { "path": "src/types/index.ts", "status": "modified", "description": "Extended with User exports" },
            { "path": "src/types/user.ts", "status": "new", "description": "User type definitions" },
            { "path": "src/repos/userRepo.ts", "status": "new", "description": "User repository" }
          ],
          "tree": "src/\n├── types/\n│   ├── index.ts\n│   └── user.ts\n├── repos/\n│   └── userRepo.ts\n└── services/"
        }
      },

      "testing_strategy": {
        "approach": "Type checking and unit tests",
        "verification_steps": [
          "tsc --noEmit",
          "npm test -- --grep 'User'"
        ]
      },

      "task_groups": [
        {
          "id": "1.1",
          "title": "User Type Definitions",
          "objective": "Define User type with validation schema",
          "status": "complete",
          "tasks": [
            {
              "id": "1.1.1",
              "title": "Create User type file",
              "description": "Define core User type with all required fields",
              "file_path": "src/types/user.ts",
              "status": "complete",
              "context": {
                "read_before": [
                  {
                    "file": "src/types/index.ts",
                    "lines": "1-20",
                    "purpose": "Understand existing type patterns"
                  }
                ],
                "related_files": ["docs/data-model.md"]
              },
              "depends_on": [],
              "actions": [
                {
                  "id": "1.1.1.1",
                  "command": "CREATE User interface with id, email, name, createdAt, updatedAt fields",
                  "file": "src/types/user.ts",
                  "status": "complete"
                },
                {
                  "id": "1.1.1.2",
                  "command": "ADD UserCreateInput type for creation payload",
                  "file": "src/types/user.ts",
                  "status": "complete"
                },
                {
                  "id": "1.1.1.3",
                  "command": "ADD UserUpdateInput type for update payload",
                  "file": "src/types/user.ts",
                  "status": "complete"
                }
              ]
            },
            {
              "id": "1.1.2",
              "title": "Add Zod validation schemas",
              "description": "Create runtime validation schemas for User types",
              "file_path": "src/types/user.ts",
              "status": "complete",
              "context": {
                "read_before": [
                  {
                    "file": "src/types/user.ts",
                    "purpose": "Reference the types just created"
                  }
                ],
                "related_files": []
              },
              "depends_on": ["1.1.1"],
              "actions": [
                {
                  "id": "1.1.2.1",
                  "command": "ADD UserSchema zod validation matching User interface",
                  "file": "src/types/user.ts",
                  "status": "complete"
                },
                {
                  "id": "1.1.2.2",
                  "command": "ADD UserCreateInputSchema for input validation",
                  "file": "src/types/user.ts",
                  "status": "complete"
                }
              ]
            }
          ]
        },
        {
          "id": "1.2",
          "title": "User Repository",
          "objective": "Create repository for User CRUD operations",
          "status": "in_progress",
          "tasks": [
            {
              "id": "1.2.1",
              "title": "Create UserRepository class",
              "description": "Implement repository with CRUD methods",
              "file_path": "src/repos/userRepo.ts",
              "status": "in_progress",
              "context": {
                "read_before": [
                  {
                    "file": "src/types/user.ts",
                    "purpose": "Import User types"
                  },
                  {
                    "file": "src/repos/baseRepo.ts",
                    "lines": "1-50",
                    "purpose": "Extend base repository pattern"
                  }
                ],
                "related_files": ["src/db/connection.ts"]
              },
              "depends_on": ["1.1.1"],
              "actions": [
                {
                  "id": "1.2.1.1",
                  "command": "CREATE UserRepository class extending BaseRepository",
                  "file": "src/repos/userRepo.ts",
                  "status": "complete"
                },
                {
                  "id": "1.2.1.2",
                  "command": "ADD findById method",
                  "file": "src/repos/userRepo.ts",
                  "status": "complete"
                },
                {
                  "id": "1.2.1.3",
                  "command": "ADD findByEmail method",
                  "file": "src/repos/userRepo.ts",
                  "status": "in_progress"
                },
                {
                  "id": "1.2.1.4",
                  "command": "ADD create method with validation",
                  "file": "src/repos/userRepo.ts",
                  "status": "pending"
                },
                {
                  "id": "1.2.1.5",
                  "command": "ADD update method with partial input",
                  "file": "src/repos/userRepo.ts",
                  "status": "pending"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": 2,
      "title": "Implement User API Endpoints",
      "goal": "Create REST endpoints for user operations",
      "prerequisites": [1],
      "status": "pending",
      "file_context": { "beginning": { "files": [], "tree": "" }, "ending": { "files": [], "tree": "" } },
      "testing_strategy": { "approach": "Integration tests", "verification_steps": [] },
      "task_groups": []
    }
  ]
}
```

### Field Reference by Level

| Level | Field | Type | Required | Description |
|-------|-------|------|----------|-------------|
| **Plan** | session_id | string | Yes | Parent session identifier |
| | spec_reference | string | Yes | Path to finalized spec |
| | created_at | datetime | Yes | Plan creation timestamp |
| | updated_at | datetime | Yes | Last modification timestamp |
| | status | enum | Yes | draft / in_progress / complete |
| | checkpoints | array | Yes | Ordered list of checkpoints |
| **Checkpoint** | id | integer | Yes | Sequential number (1-based) |
| | title | string | Yes | Short descriptive title |
| | goal | string | Yes | What this checkpoint achieves |
| | prerequisites | int[] | No | Checkpoint IDs that must complete first |
| | status | enum | Yes | pending / in_progress / complete / blocked |
| | file_context | object | Yes | Beginning and ending file states |
| | testing_strategy | object | Yes | How to verify completion |
| | task_groups | array | Yes | Logical groupings of tasks |
| **Task Group** | id | string | Yes | Hierarchical ID (e.g., "1.1") |
| | title | string | Yes | Short title |
| | objective | string | Yes | What this group accomplishes |
| | status | enum | Yes | pending / in_progress / complete / blocked |
| | tasks | array | Yes | Tasks within this group |
| **Task** | id | string | Yes | Hierarchical ID (e.g., "1.1.1") |
| | title | string | Yes | Short title |
| | description | string | Yes | Detailed description |
| | file_path | string | Yes | Primary file this task operates on |
| | status | enum | Yes | pending / in_progress / complete / blocked |
| | context | object | No | Files to read before executing |
| | depends_on | string[] | No | Task IDs that must complete first |
| | actions | array | Yes | Atomic operations to perform |
| **Action** | id | string | Yes | Hierarchical ID (e.g., "1.1.1.1") |
| | command | string | Yes | IDK-formatted instruction |
| | file | string | Yes | Target file path |
| | status | enum | Yes | pending / in_progress / complete / blocked |

## Non-Goals

*What we are explicitly NOT building - prevents scope creep*

## Success Criteria

*How do we know we're done? Testable outcomes*

- [ ] (To be defined)

## Context & Background

### Prior Work

This spec is a **continuation/update** of the original plan mode enhancement:
- **Prior Session**: `2025-12-24_enhancing-plan-mode_k7m3x9`
- **Prior Spec**: [`agents/sessions/2025-12-24_enhancing-plan-mode_k7m3x9/spec.md`](../2025-12-24_enhancing-plan-mode_k7m3x9/spec.md)

### Current Plan Mode Implementation

The existing plan mode was implemented in session `2025-12-24_enhancing-plan-mode_k7m3x9` and includes:
- Checkpoint-based planning structure
- IDK (Information-Dense Keywords) for task definitions
- Progressive disclosure workflow
- plan.json as source of truth with plan.md auto-generated
- Task hierarchy: Checkpoint → Tranche → Task → Subtask
- File context tracking (beginning/ending states)
- Testing strategy per checkpoint

### Related Files

- `.claude/commands/session/plan.md` - Plan mode command
- `.claude/skills/session/plan/OVERVIEW.md` - Plan phase documentation
- `agents/sessions/*/plan.json` - Existing plan files

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Replace Tranche → Task Group | Shift from parallel-execution semantics to objective-based grouping; "Task Group" is more intuitive | 2026-01-01 |
| Rename Subtask → Action | Clarifies these are file-scoped atomic operations, not just "smaller tasks" | 2026-01-01 |
| Keep 4-level hierarchy | Checkpoint → Task Group → Task → Action provides right granularity for organization without over-complication | 2026-01-01 |
| Map to git workflow | Plan=PR, Checkpoint=Commit makes the structure intuitive and actionable | 2026-01-01 |
| **IDK format required for all Actions** | Non-negotiable: every action handed off for execution must use IDK vocabulary | 2026-01-01 |
| Actions are structured objects | Each action has: id, command (IDK), file, status - enables precise tracking and file-scoped execution | 2026-01-01 |
| **Status tracking at every level** | Enables async/resumable execution - a new agent can pick up from plan state without prior context | 2026-01-01 |
| Context at Task level only | Task Group doesn't need context; Task-level read_before/related_files is sufficient | 2026-01-01 |
| Task Group has title + objective | Allows viewing at different granularity levels (title for scanning, objective for understanding) | 2026-01-01 |
| Structured prior spec referencing | Prompt for prior specs at session start, store in state.json for context | 2026-01-01 |
| Tiered progressive confirmation in plan | Generate checkpoints → confirm → task groups → confirm → tasks → confirm → actions | 2026-01-01 |
| Checkpoint = Commit boundary | Each completed checkpoint results in a git commit in build phase | 2026-01-01 |
| No auto-continuation in build | After checkpoint commit, output command for next - don't auto-run | 2026-01-01 |

## Open Questions

*None currently - spec covers hierarchy, workflow, and all three phases*

## Diagrams

*Visual aids to clarify understanding (to be added as needed)*

## Notes

*Additional context and observations*

---
*This spec was finalized on 2026-01-01. Ready for plan phase.*
