# Build Phase

Execute the plan one checkpoint at a time with verification.

## Build Modes

Two commands for different workflows:

| Command | Mode | Best For |
|---------|------|----------|
| `/session:build` | Interactive | Learning, validation, complex/risky changes (default) |
| `/session:build-background` | Autonomous | Trusted plans, speed, straightforward changes |

### `/session:build` - Interactive Mode (Default)

Task-by-task execution with confirmation at each step.

```
For each task:
  Present task → User confirms → Execute → Show result → User validates → Next
```

User controls:
- Confirm before each write
- Validate each change in real-time
- Skip, adjust, or revert individual tasks
- Pause at any point

### `/session:build-background` - Autonomous Mode

Executes all tasks in a checkpoint directly, reports results at end.

```
User invokes → Checkpoint executes → Results reported → User re-invokes for next
```

## Purpose

The build phase executes the planned transformation:
- Executes checkpoint tasks directly (no sub-agents)
- One checkpoint per invocation, user re-invokes for next
- Tracks progress in state.json for pause/resume capability
- Captures implementation learnings in DevNotes
- User-in-loop control (between checkpoints or per-task)

## Prerequisites

- Finalized plan (`phases.plan.status: "finalized"` in state.json)
- Session in build phase (`current_phase: "build"`)

## Workflow

```
1. Parse arguments ($1=session, $2=checkpoint, $3=task_group)
     ↓
2. Load session (state.json, plan.json, dev-notes.json)
     ↓
3. Determine target
     ├── Auto-discover from plan_state
     ├── Explicit checkpoint ($2)
     └── Explicit task_group ($2.$3)
     ↓
4. Execute checkpoint directly
     ├── Load context (checkpoint, spec goals, prior DevNotes)
     ├── Execute tasks in task_groups using tools
     └── Track progress + DevNotes
     ↓
5. Run verification steps
     ├── Pass → Continue to commit
     └── Fail → User decides: override or pause
     ↓
6. Create git commit (checkpoint = commit boundary)
     ├── git add changed files
     └── git commit -m "checkpoint-N: description"
     ↓
7. Update state (plan_state, dev-notes.json)
     ↓
8. Report to user with next checkpoint command
```

Note: User re-invokes the build command to continue to next checkpoint.

## Execution Model

### Direct Execution

Checkpoint tasks execute directly within the build command context:
- **Same context**: Tasks run in current conversation context
- **User control**: One checkpoint per invocation
- **Focused**: Only executes tasks for the target checkpoint

Build command loads:
- Checkpoint goal and tasks from plan.json
- Relevant spec goals
- Prior DevNotes that might affect this work
- File context (beginning/ending state)

### Task Execution

For each task within the checkpoint:
1. Load pre-read context from `task.context.read_before`
2. Execute action using available tools (Read, Write, Edit, Glob, Grep, Bash)
3. Verify file changes match expectations
4. Track any deviations as DevNotes

### Checkpoint Verification

After all tasks complete:
1. Run `testing_strategy.verification_steps`
2. Compare actual files to `file_context.ending`
3. If verification fails:
   - User can **override** (continues with DevNote documenting decision)
   - User can **pause** (partial completion, exact position saved)

### Git Commit (Checkpoint = Commit Boundary)

After verification passes (or override), create a commit:

```bash
git add <changed-files>
git commit -m "checkpoint-N: <checkpoint-title>"
```

**Commit Message Format**: `checkpoint-N: <short description>`
- Example: `checkpoint-1: Update plan templates and data models`
- Example: `checkpoint-2: Add tiered confirmation workflow`

This creates a clear commit history aligned with the plan structure.

## State Tracking

The `plan_state` in state.json tracks progress:

```json
{
  "plan_state": {
    "status": "in_progress",
    "current_checkpoint": 2,
    "current_task_group": "2.1",
    "current_task": "2.1.3",
    "checkpoints_completed": [1],
    "last_updated": "2025-12-24T12:00:00Z",
    "summary": "Completed checkpoint 1. Working on checkpoint 2, task 2.1.3."
  }
}
```

## DevNotes

DevNotes capture implementation learnings in `dev-notes.json`:

```json
{
  "notes": [
    {
      "id": "dn-001",
      "timestamp": "2025-12-28T12:00:00Z",
      "scope": { "type": "task", "ref": "1.2.3" },
      "category": "deviation",
      "content": "Used async/await instead of callbacks as planned"
    }
  ]
}
```

### Categories

| Category | When to Use |
|----------|-------------|
| `deviation` | Did something different than planned |
| `discovery` | Found something affecting current/future work |
| `decision` | Made a choice during implementation |
| `blocker` | Encountered something preventing progress |
| `resolution` | How a blocker was resolved |

### Scope Types

- `task` - Note about a specific task (ref: task ID like "1.2.3")
- `checkpoint` - Note about entire checkpoint (ref: checkpoint ID like "1")
- `session` - Session-wide note (ref: null)

## Commands

### Interactive Build (Default)

```
/session:build [session-id] [checkpoint]

Arguments:
  $1 = session-id   (required)
  $2 = checkpoint   (optional - auto-discovers if not provided)
```

| Command | Description |
|---------|-------------|
| `/session:build my-session` | Interactive execution of next checkpoint |
| `/session:build my-session 2` | Interactive execution of checkpoint 2 |

### Autonomous Build

```
/session:build-background [session-id] [checkpoint] [task_group]

Arguments:
  $1 = session-id   (required)
  $2 = checkpoint   (optional - specific checkpoint number)
  $3 = task_group   (optional - specific task_group id)
```

| Command | Description |
|---------|-------------|
| `/session:build-background my-session` | Auto-discover next checkpoint |
| `/session:build-background my-session 2` | Execute checkpoint 2 |
| `/session:build-background my-session 2 2.1` | Execute only task_group 2.1 |

## Error Handling

### Partial Completion

Errors are treated like a pause:
- Track exact position (checkpoint, task_group, task)
- Update plan_state with current progress
- Add DevNote capturing what went wrong
- Resume picks up exactly where stopped

### Verification Failure

When verification fails:
1. Present failure details to user
2. Offer options:
   - **Override**: Continue anyway (adds DevNote documenting override)
   - **Pause**: Stop to fix issue manually

## Completion

Session is complete when:
- [x] All checkpoints executed
- [x] All verification steps pass (or overridden)
- [x] `phases.build.status` set to "completed"
- [x] `current_phase` set to "complete"

## Outputs

- Working code (per plan)
- Updated `state.json` with completion status
- `dev-notes.json` with implementation learnings

## Templates

- [dev-notes.json](templates/dev-notes.json) - DevNotes template with schema
