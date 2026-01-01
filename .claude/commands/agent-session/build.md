---
description: Interactive build - walk through checkpoint tasks one by one with user confirmation
argument-hint: [session-id] [checkpoint]
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion
model: opus
---

# Build Mode

Walk through a checkpoint task-by-task, executing each one directly in this conversation with user confirmation.

## CRITICAL RULES

1. **NO SUB-AGENTS** - Do NOT use the Task tool. Execute everything directly in this conversation.
2. **ONE TASK AT A TIME** - Complete each task fully before moving to the next.
3. **USER CONFIRMS EACH EDIT** - Show what you'll change, wait for approval, then edit.
4. **UPDATE STATE AFTER EACH TASK** - Write to state.json after completing each task.

## Variables

```
$1 = session-id   (required)
$2 = checkpoint   (optional - auto-discovers next incomplete if not provided)
SESSIONS_DIR = agents/sessions
```

## Execution Flow

Follow these steps IN ORDER, directly in this conversation:

### Step 1: Load Session

1. Read `SESSIONS_DIR/$1/state.json`
2. Read `SESSIONS_DIR/$1/plan.json`
3. Verify plan is finalized (`phases.plan.status === "finalized"`)
4. If $2 provided, use that checkpoint. Otherwise, find first incomplete checkpoint from `plan_state.checkpoints_completed`

### Step 2: Show Checkpoint Overview

Display to user:
```
## Checkpoint [ID]: [Title]

**Goal**: [checkpoint goal]

**Tasks**:
1. [task 1 summary]
2. [task 2 summary]
...

Ready to begin?
```

Use AskUserQuestion to confirm start.

### Step 3: Execute Each Task (THE MAIN LOOP)

For each task in the checkpoint, do ALL of the following in sequence:

#### 3a. Present the Task
```
---
## Task [ID]: [Title]

**Action**: [what this task does]
**Files to read first**: [list]
**Files to modify**: [list]
---
```

#### 3b. Read Context Files
Actually read the files listed in `task.context.read_before` using the Read tool.
Show relevant snippets to the user.

#### 3c. Confirm Before Editing
Use AskUserQuestion:
- "Ready to execute this task?"
- Options: Execute, Skip, Pause

#### 3d. Make the Edits
If user confirms:
1. Use Edit or Write tool to make the changes
2. Show what was changed (the actual diff or new content)

#### 3e. Confirm the Result
Use AskUserQuestion:
- "Does this look correct?"
- Options: Looks good, Adjust, Revert

#### 3f. Update State
After user confirms, update `state.json`:
```json
{
  "plan_state": {
    "current_task": "[next task id]",
    "last_updated": "[timestamp]"
  }
}
```

#### 3g. Move to Next Task
Repeat from 3a for the next task.

### Step 4: Checkpoint Complete

After all tasks:

#### 4a. Create Git Commit (checkpoint = commit boundary)
```bash
git add <changed-files>
git commit -m "checkpoint-N: <checkpoint-title>"
```

Show commit hash to user.

#### 4b. Update State
Update state.json:
- Add checkpoint to `plan_state.checkpoints_completed`
- Set `plan_state.current_checkpoint` to next (or null if done)

#### 4c. Report Completion
```
## Checkpoint N Complete ✅

**Commit**: <commit-hash>
**Tasks Completed**: X/X

### Next
Run `/session:build <session-id>` to continue to Checkpoint N+1.
```

## Example Execution

Here's exactly how a task execution should look:

```
---
## Task 1.1: Add validation function

**Action**: Create a new validation function in utils.ts
**Files to read first**: src/utils.ts
**Files to modify**: src/utils.ts
---

Let me read the current file first...

[Uses Read tool on src/utils.ts]

Here's the current state of the file:
[shows relevant code]

I'll add the validation function after line 45. Here's what I'll add:
[shows the new code]

Ready to execute this task?
```

[User confirms]

```
[Uses Edit tool to make the change]

Done! Here's what changed:
[shows the edit]

Does this look correct?
```

[User confirms]

```
✓ Task 1.1 complete

Updating state...
[Updates state.json]

Moving to Task 1.2...
```

## Behavior

- Execute ALL tool calls directly - no spawning agents
- Show your work - let user see each read, each edit
- Wait for confirmation before each edit
- Update state.json after EACH completed task
- If user says "Pause", save current position and stop

## State Updates

After each task, edit state.json to update:
```json
{
  "plan_state": {
    "status": "in_progress",
    "current_checkpoint": [current],
    "current_task": [next task or null],
    "last_updated": "[ISO timestamp]"
  }
}
```

After checkpoint complete:
```json
{
  "plan_state": {
    "checkpoints_completed": [..., completed_id],
    "current_checkpoint": [next or null],
    "current_task": null
  }
}
```
