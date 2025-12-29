---
description: Interactive build - execute checkpoint tasks with user confirmation at each step
argument-hint: [session-id] [checkpoint]
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion
model: opus
---

# Build Mode

Execute a checkpoint interactively, presenting each task for user confirmation before execution.

## Skill Reference

- Skill: `.claude/skills/agent-session/SKILL.md`
- Build docs: `.claude/skills/agent-session/build/OVERVIEW.md`
- Working directory: `agents/sessions/`

## Variables

```
$1 = session-id   (required)
$2 = checkpoint   (optional - auto-discovers next incomplete if not provided)
SESSIONS_DIR = agents/sessions
```

## Workflow

```
1. Load session and validate
     ↓
2. Present checkpoint overview → User confirms start
     ↓
3. For each task:
     ├── Present task details
     ├── User confirms → Execute → Show result
     └── User validates → Continue or adjust
     ↓
4. Run verification → User confirms
     ↓
5. Update state and report
```

<workflow>
    <phase name="1_load_and_validate">
        <steps>
            <step>Validate $1 (session-id) is provided</step>
            <step>Load state.json, plan.json from SESSIONS_DIR/$1</step>
            <step>Verify plan is finalized</step>
            <step>Determine target checkpoint ($2 or auto-discover next incomplete)</step>
            <step>Load checkpoint details and task list</step>
        </steps>
    </phase>

    <phase name="2_present_overview">
        <description>Show checkpoint overview and get user buy-in</description>
        <output>
```markdown
## Build - Checkpoint {{CHECKPOINT_ID}}

**Session**: `{{SESSION_ID}}`
**Checkpoint**: {{CHECKPOINT_TITLE}}

### Goal
{{CHECKPOINT_GOAL}}

### Tasks Preview
{{TASK_LIST_WITH_BRIEF_DESCRIPTIONS}}

### Files That Will Be Modified
{{FILE_LIST}}
```
        </output>
        <action>
            Use AskUserQuestion:
            - Question: "Ready to start this checkpoint?"
            - Options:
              - "Start" - Begin task-by-task execution
              - "Skip to task" - Jump to specific task
              - "Cancel" - Exit build
        </action>
    </phase>

    <phase name="3_task_loop">
        <description>Execute each task with user confirmation</description>

        <for_each_task>
            <step name="present">
                Display task details:
```markdown
---
## Task {{TASK_ID}}: {{TASK_TITLE}}

**Tranche**: {{TRANCHE_ID}}
**Action**: {{TASK_ACTION}}

### Context Files
{{CONTEXT_READ_BEFORE_LIST}}

### Files to Modify
{{FILES_TO_CHANGE}}

### What This Task Does
{{TASK_DESCRIPTION_EXPANDED}}
---
```
            </step>

            <step name="confirm_execution">
                Use AskUserQuestion:
                - Question: "Execute this task?"
                - Options:
                  - "Execute" - Proceed with this task
                  - "Show more" - Read context files first, then ask again
                  - "Skip" - Skip this task, continue to next
                  - "Pause" - Stop here, save progress
            </step>

            <step name="execute_if_confirmed">
                If "Execute" or after "Show more":
                1. Read any context files (task.context.read_before)
                2. Execute the task action using appropriate tools
                3. Display what was changed:
```markdown
### Changes Made

**File**: {{FILE_PATH}}
```diff
{{DIFF_OR_SUMMARY}}
```
```
            </step>

            <step name="validate_result">
                Use AskUserQuestion:
                - Question: "Does this look correct?"
                - Options:
                  - "Looks good" - Continue to next task
                  - "Adjust" - Make modifications before continuing
                  - "Revert" - Undo this change
                  - "Pause" - Stop and review
            </step>

            <step name="handle_response">
                - "Looks good": Update plan_state.current_task, continue
                - "Adjust": Ask what to change, apply, re-validate
                - "Revert": Undo changes, ask if retry or skip
                - "Pause": Save exact position, exit with resume command
            </step>

            <step name="track_devnotes">
                If any deviations, discoveries, or decisions occurred:
                - Create DevNote with appropriate category
                - Show user the DevNote being added
            </step>
        </for_each_task>
    </phase>

    <phase name="4_verification">
        <description>Run verification steps interactively</description>
        <steps>
            <step>Display verification steps from checkpoint's testing_strategy</step>
            <step>Run each verification step, showing output</step>
            <step>
                Use AskUserQuestion:
                - Question: "Verification complete. Does everything look correct?"
                - Options:
                  - "All good" - Mark checkpoint complete
                  - "Issues found" - Document issues, decide next steps
            </step>
        </steps>
    </phase>

    <phase name="5_complete">
        <description>Update state and report</description>
        <steps>
            <step>Mark checkpoint complete in plan_state</step>
            <step>Add checkpoint to checkpoints_completed</step>
            <step>Append any DevNotes to dev-notes.json</step>
            <step>Display completion summary</step>
        </steps>
        <output>
```markdown
## Checkpoint {{CHECKPOINT_ID}} Complete

**Tasks Completed**: {{COMPLETED_COUNT}}/{{TOTAL_COUNT}}
**Tasks Skipped**: {{SKIPPED_COUNT}}

### DevNotes Added
{{DEVNOTES_SUMMARY}}

### Next Steps
- Run `/session:build {{SESSION_ID}}` for next checkpoint
- Or `/session:build-background {{SESSION_ID}}` for autonomous execution
```
        </output>
    </phase>
</workflow>

<user_interaction_patterns>
## Interaction Patterns

### Before Each Task
Always present:
1. Task ID and title
2. What action will be taken
3. Which files will be affected
4. Option to see more context

### After Each Task
Always show:
1. What changed (diff or summary)
2. Validation question
3. Options to adjust, revert, or continue

### On Pause
Save exact position:
- Current checkpoint
- Current tranche
- Current task
- Any partial progress

Provide resume command:
```
/session:build {{SESSION_ID}} {{CHECKPOINT}}
```

### On Skip
- Document skip in DevNote
- Continue to next task
- Track skipped count for summary
</user_interaction_patterns>

<devnotes_in_loop>
## DevNotes During Build

Create DevNotes for:
- **deviation**: User chose to do something differently
- **discovery**: Found something unexpected during execution
- **decision**: User made a choice (skip, adjust, etc.)

Show each DevNote to user as it's created:
```markdown
📝 **DevNote Added**
- Category: {{CATEGORY}}
- Scope: Task {{TASK_ID}}
- Content: {{CONTENT}}
```
</devnotes_in_loop>

<behavior_constraints>
DURING BUILD:
- DO present each task before execution
- DO wait for user confirmation before any writes
- DO show results after each task
- DO ask for validation before continuing
- DO save progress on pause
- DO track all user decisions as DevNotes
- DO allow skipping, adjusting, or reverting

NEVER:
- Execute writes without user confirmation
- Skip the validation step after execution
- Lose progress on pause or error
- Proceed to next task without user acknowledgment
</behavior_constraints>

<error_handling>
On error during task execution:
1. Show the error to user
2. Offer options:
   - "Retry" - Try the task again
   - "Skip" - Move to next task (add DevNote)
   - "Pause" - Stop and investigate
3. Save state regardless of choice
</error_handling>
