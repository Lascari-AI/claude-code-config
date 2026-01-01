---
description: Enter plan mode to design implementation strategy from a finalized spec
argument-hint: [session-id] [continue|finalize]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: opus
---

# Plan Mode

Design HOW to implement a finalized spec using checkpoint-based planning with IDK tasks.

## CRITICAL RULES

1. **NO SUB-AGENTS** - Do NOT use the Task tool. Execute everything directly in this conversation.
2. **ITERATIVE CONFIRMATION** - Get user approval at each stage: outline → each checkpoint's details.
3. **JSON AS SOURCE OF TRUTH** - Write `plan.json` first; `plan.md` is auto-generated.
4. **UPDATE STATE** - Update `state.json` with `plan_state` after each stage.

## Variables

```
$1 = session-id   (required)
$2 = action       (optional: "continue" or "finalize")
SESSIONS_DIR = agents/sessions
SKILL_DIR = .claude/skills/agent-session
```

## Required Reading

Before proceeding, read these files:

| File | Purpose | When to Read |
|------|---------|--------------|
| `SKILL_DIR/plan/OVERVIEW.md` | Workflow, concepts, IDK reference table | Always (first) |
| `SKILL_DIR/plan/templates/plan.json` | JSON structure template | When creating plan.json |
| `SKILL_DIR/plan/idk/*.md` | IDK vocabulary by category | When generating task actions |

## State Detection

Read `state.json` and detect current state:

| State | Condition | Action |
|-------|-----------|--------|
| **Not in plan phase** | `current_phase !== "plan"` | Initialize plan phase |
| **Outline pending** | Plan phase started, no checkpoints | Tier 1: Generate checkpoint outline |
| **Outline needs approval** | Checkpoints exist, `plan_state.status !== "outline_approved"` | Show outline, get confirmation |
| **Task groups pending** | Outline approved, checkpoint N has no task_groups | Tier 2: Generate task groups for checkpoint N |
| **Tasks pending** | Task group N.M has no tasks | Tier 3: Generate tasks for task group N.M |
| **Actions pending** | Task N.M.P has no actions | Tier 4: Generate actions for task N.M.P |
| **Ready to finalize** | All checkpoints fully detailed (task_groups→tasks→actions) | Prompt for finalization |
| **Already finalized** | `phases.plan.status === "finalized"` | Show status, suggest build phase |

Track per-checkpoint progress in `plan_state`:
- `current_checkpoint`: Which checkpoint is being detailed
- `current_task_group`: Which task group is being detailed
- `current_task`: Which task is being detailed

## Execution Flow

### Step 1: Load Session

1. Read `SESSIONS_DIR/$1/state.json`
2. Verify `phases.spec.status === "finalized"` (error if not)
3. Read `SESSIONS_DIR/$1/spec.md`
4. Read `SKILL_DIR/plan/OVERVIEW.md` for workflow guidance
5. Determine current state from table above
6. If `$2 === "finalize"`, jump to Step 5

### Step 2: Generate Checkpoint Outline

If no checkpoints exist:

1. Analyze the spec's goals, requirements, and success criteria
2. Explore the existing codebase for relevant patterns and files
3. Design 3-7 sequential checkpoints that bridge current → desired state
4. Create initial `plan.json` using template from `SKILL_DIR/plan/templates/plan.json`
   - Include checkpoint titles, goals, prerequisites
   - Leave task_groups/tasks empty (to be detailed in Step 3)

Display checkpoint outline to user and use AskUserQuestion:
- Options: "Approve outline", "Adjust checkpoints", "Add more detail"

After approval, update `state.json` with `plan_state`:
```json
{
  "plan_state": {
    "status": "outline_approved",
    "checkpoints_total": [N],
    "checkpoints_detailed": 0,
    "last_updated": "[timestamp]"
  }
}
```

### Step 3: Detail Checkpoint (Tiered Approach)

For each checkpoint that needs detailing, apply tiers 2-4 progressively:

#### 3a. Tier 2: Generate Task Groups

1. Analyze checkpoint goal and scope
2. Generate task groups with titles and objectives
3. Present to user with AskUserQuestion:
   - Options: "Approve task groups", "Adjust grouping", "Merge groups"
4. After approval, update `plan.json` with task_groups (tasks empty)
5. Update `plan_state.current_task_group` to first group

#### 3b. Tier 3: Generate Tasks (per Task Group)

For each task group:

1. Load IDK vocabulary from `SKILL_DIR/plan/idk/`:
   - `crud.md`, `actions.md`, `language.md`, `refactoring.md`, `testing.md`, `documentation.md`
2. Identify file context (beginning/ending states)
3. Generate tasks with titles, descriptions, file_paths
4. Present to user with AskUserQuestion:
   - Options: "Approve tasks", "Split task", "Add task"
5. After approval, update `plan.json` with tasks (actions empty)
6. Update `plan_state.current_task` to first task

#### 3c. Tier 4: Generate Actions (per Task)

For each task:

1. Generate IDK-formatted actions for the task
2. Present actions to user with AskUserQuestion:
   - Options: "Approve actions", "Adjust actions", "Add action"
3. After approval, update `plan.json` with actions
4. Move to next task in task group

#### 3d. Update State

After each tier approval:
```json
{
  "plan_state": {
    "status": "in_progress",
    "current_checkpoint": 1,
    "current_task_group": "1.2",
    "current_task": "1.2.1",
    "last_updated": "[timestamp]"
  }
}
```

### Step 4: Repeat for All Checkpoints

Loop through Step 3 for each checkpoint until all are detailed.

### Step 5: Finalize Plan

When all checkpoints are detailed or `$2 === "finalize"`:

1. Verify all checkpoints have tasks
2. Update `plan.json` status to `"complete"`
3. Update `state.json`:
```json
{
  "phases": {
    "plan": {
      "status": "finalized",
      "finalized_at": "[timestamp]"
    }
  },
  "plan_state": {
    "status": "finalized",
    "checkpoints_total": [N],
    "checkpoints_detailed": [N],
    "checkpoints_completed": []
  }
}
```

Display summary and suggest: `/session:build [session-id]`

## Behavior Notes

- **Progressive detail**: Start with outline, add detail incrementally
- **User control**: Get confirmation before committing each stage
- **Resumable**: State tracking allows stopping and continuing later
- **Direct execution**: No sub-agents - all work happens in this conversation
- **IDK precision**: Use IDK vocabulary for unambiguous task definitions
