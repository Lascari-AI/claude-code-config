---
description: Auto-generate a simple plan for chores and quick fixes (non-interactive)
argument-hint: [session-id]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---

# Quick Plan Mode

Auto-generate a simple plan (~1 checkpoint) for chores, quick fixes, and simple changes.

<purpose>
    - Generate complete implementation plans automatically for small-scope tasks
    - Skip tier-by-tier confirmation to optimize for speed on straightforward changes
    - Produce same plan.json structure as full plan for build compatibility
    - Provide QA gate for user review with escalation path to full plan
</purpose>

<key_knowledge>
    - Plan structure: checkpoints → task_groups → tasks → actions
    - IDK vocabulary for precise, unambiguous task actions
    - Self-contained task design for fault recovery
    - Full plan command workflow (for escalation handling)
</key_knowledge>

<goal>
    - Complete plan.json and plan.md ready for `/session:build` command
    - User confidence that the auto-generated plan is correct
    - Clear escalation path if task is more complex than initially thought
</goal>

<background>
    - Quick plan pairs with light research mode for chore-level tasks
    - Reduces overhead for simple fixes where full interactive planning is overkill
    - Uses Sonnet model for speed; full plan uses Opus for thoroughness
    - Same output structure ensures all build commands work identically
</background>

## Skill Reference

Read the session skill for templates and full documentation:
- Skill: `.claude/skills/session/SKILL.md`
- Plan OVERVIEW: `.claude/skills/session/plan/OVERVIEW.md`
- Plan templates: `.claude/skills/session/plan/templates/`
- IDK vocabulary: `.claude/skills/session/plan/idk/`
- Working directory: `agents/sessions/`

## Variables

```
$1 = session-id   (required)
SESSIONS_DIR = agents/sessions
SKILL_DIR = .claude/skills/session
```

## Instructions

Parse `$1` and follow the linear flow:

1. **`$1` matches existing session ID**: Load that session (check `SESSIONS_DIR/$1/state.json`)
   - Verify spec is finalized
   - Check if plan already exists (if so, show status)
2. **`$1` is empty or invalid**: Error - session ID required for quick plan

Then proceed through: Load → Assess → Auto-Generate → QA → Finalize (or Escalate)

## Core Principles

Quick plan mode is:
- **Non-interactive** - Generates complete plan in one pass, no tier-by-tier approval
- **Speed-optimized** - Uses Sonnet model, minimal back-and-forth
- **Consistent output** - Same plan.json structure as full plan
- **QA-gated** - User reviews before finalization, can escalate if needed

<workflows>
    <workflow name="quick_plan_flow">
        <description>Linear flow from session load through auto-generation and QA</description>

        <phase name="1_load_session">
            <description>Load session and verify preconditions</description>
            <steps>
                <step id="1">Check if SESSIONS_DIR/$1/state.json exists (error if not)</step>
                <step id="2">Load state.json and check phases.spec.status:
                    - If "finalized_complete": Session was completed without plan (exploration determined no changes needed). Inform user and exit gracefully.
                    - If "finalized": Continue to planning
                    - Otherwise: Error - spec not finalized
                </step>
                <step id="3">Read SESSIONS_DIR/$1/spec.md for requirements</step>
                <step id="4">Read SKILL_DIR/plan/OVERVIEW.md for plan structure guidance</step>
                <step id="5">Check if plan.json already exists:
                    - If exists and finalized: Report status, suggest /session:build
                    - If exists and in_progress: Offer to continue or regenerate
                    - If not exists: Proceed to assessment
                </step>
            </steps>
            <on_failure>
                - Session not found: "Session '{$1}' not found. Use /session:spec to create."
                - Spec completed as documentation: "This session was completed as documentation only (no changes needed). No plan required."
                - Spec not finalized: "Spec not finalized. Run /session:spec {$1} finalize first."
            </on_failure>
        </phase>

        <phase name="2_assess_complexity">
            <description>Determine if quick plan is appropriate before generating</description>
            <criteria name="appropriate_for_quick">
                - Task is a chore, bug fix, or small enhancement
                - Changes are localized (typically 1-3 files)
                - Clear, well-defined scope from spec
                - No architectural decisions needed
                - Single logical checkpoint is sufficient
            </criteria>
            <criteria name="suggest_full_plan">
                - Multiple system components affected
                - Architectural decisions required
                - Spec has many goals or complex requirements
                - Changes span more than 5 files
                - Multiple distinct phases of work needed
            </criteria>
            <action_if_complex>
                Use AskUserQuestion:
                - "This task seems complex for quick plan. Would you prefer full plan mode?"
                - Options: "Continue with quick plan", "Switch to full plan"
                - If switch: Exit with "Use /session:plan {session_id} for interactive planning."
            </action_if_complex>
        </phase>

        <phase name="3_iterative_generation">
            <description>Build plan.json iteratively, writing after each step (no user in loop)</description>
            <principle>
                Even though quick plan has no user confirmation at each step, the agent
                still builds the plan ITERATIVELY - creating the structure, then adding
                detail layer by layer. Each substep writes to plan.json before proceeding.
                This matches the multi-turn state-file pattern for restartability.
            </principle>

            <substep name="3a_analyze_spec">
                <description>Extract requirements from spec</description>
                <actions>
                    - Parse spec.md for goals (high_level, mid_level, detailed)
                    - Identify explicit file paths or components mentioned
                    - Note any constraints or dependencies mentioned
                    - Extract success criteria for verification
                </actions>
            </substep>

            <substep name="3b_explore_codebase">
                <description>Understand current state of relevant files</description>
                <actions>
                    - Use Glob to find files matching spec requirements
                    - Read existing files that will be modified
                    - Identify patterns and conventions to follow
                    - Note imports, dependencies, and related files
                </actions>
                <critical>
                    This exploration informs the plan. The agent must understand
                    WHAT exists before defining HOW to change it.
                </critical>
            </substep>

            <substep name="3c_create_plan_skeleton">
                <description>Initialize plan.json with checkpoint outline</description>
                <actions>
                    - Read template from SKILL_DIR/plan/templates/plan.json
                    - Create checkpoint with: id, title, goal, prerequisites
                    - Add file_context.beginning (current state)
                    - Add file_context.ending (expected state)
                    - Add testing_strategy
                    - Leave task_groups as empty array
                </actions>
                <write>
                    Write initial plan.json to SESSIONS_DIR/$1/plan.json
                </write>
                <state_update>
                    Update state.json plan_state:
                    ```json
                    {
                        "status": "generating",
                        "checkpoints_total": 1,
                        "checkpoints_detailed": 0,
                        "current_checkpoint": 1,
                        "last_updated": "{timestamp}"
                    }
                    ```
                </state_update>
            </substep>

            <substep name="3d_add_task_groups">
                <description>Add task groups to checkpoint</description>
                <actions>
                    - Create 1-3 task groups based on objectives
                    - Each group has: id, title, objective, status="pending"
                    - Group by: file type, feature area, or logical sequence
                    - Leave tasks as empty array for each group
                </actions>
                <write>
                    Update plan.json: add task_groups array to checkpoint
                </write>
            </substep>

            <substep name="3e_add_tasks">
                <description>Add tasks to each task group</description>
                <per_task_group>
                    For each task group, add tasks with self-containment:
                    - id: "{group_id}.{task_number}" (e.g., "1.1.1")
                    - title: Action verb + target
                    - file_path: EXACT path to target file
                    - description: WHAT to do + WHY (enough for agent with no context)
                    - status: "pending"
                    - context.read_before: [{file, lines, purpose}]
                    - context.related_files: []
                    - depends_on: [] (or explicit dependencies)
                    - Leave actions as empty array
                </per_task_group>
                <self_containment_test>
                    For each task: Can an agent with ONLY this task object
                    (no session history) execute it correctly?
                    If not, add missing context to read_before or description.
                </self_containment_test>
                <write>
                    Update plan.json: add tasks array to each task_group
                </write>
            </substep>

            <substep name="3f_add_actions">
                <description>Add IDK-formatted actions to each task</description>
                <idk_reference>
                    Read SKILL_DIR/plan/idk/ for vocabulary:
                    - CRUD: CREATE, UPDATE, DELETE
                    - Actions: ADD, REMOVE, MOVE, REPLACE, MIRROR, APPEND
                    - Language: VAR, FUNCTION, CLASS, TYPE, FILE
                    - Refactoring: REFACTOR, RENAME, SPLIT, MERGE, EXTRACT
                </idk_reference>
                <per_task>
                    Add actions:
                    - id: "{task_id}.{action_number}" (e.g., "1.1.1.1")
                    - command: IDK formatted (e.g., "ADD FUNCTION validateInput()")
                    - file: Target file path
                    - status: "pending"
                </per_task>
                <write>
                    Update plan.json: add actions array to each task
                </write>
            </substep>

            <substep name="3g_finalize_generation">
                <description>Mark generation complete, ready for QA</description>
                <state_update>
                    Update state.json:
                    ```json
                    {
                        "current_phase": "plan",
                        "phases": {
                            "plan": {
                                "status": "in_progress",
                                "started_at": "{timestamp}"
                            }
                        },
                        "plan_state": {
                            "status": "pending_qa",
                            "checkpoints_total": 1,
                            "checkpoints_detailed": 1,
                            "last_updated": "{timestamp}"
                        }
                    }
                    ```
                </state_update>
            </substep>
        </phase>

        <phase name="4_present_for_qa">
            <description>Display generated plan and get user decision</description>
            <output_format>
```markdown
## Quick Plan Generated

**Checkpoint 1**: {title}
**Goal**: {goal}

**Task Groups**:
1. **{group_1.id}**: {group_1.title}
   - Task {task_1.id}: {task_1.title} → `{task_1.file_path}`
   - Task {task_2.id}: {task_2.title} → `{task_2.file_path}`

2. **{group_2.id}**: {group_2.title} (if applicable)
   ...

**Estimated scope**: {N} files, {M} tasks
```
            </output_format>
            <user_decision>
                Use AskUserQuestion:
                - question: "How would you like to proceed with this plan?"
                - header: "Plan QA"
                - options:
                    - label: "Approve and finalize"
                      description: "Accept plan as-is, ready for build phase"
                    - label: "Adjust plan"
                      description: "Make specific changes while staying in quick mode"
                    - label: "Escalate to full plan"
                      description: "Switch to interactive tier-by-tier planning"
            </user_decision>
        </phase>

        <phase name="5a_finalize" condition="user approved">
            <description>Lock plan for build phase</description>
            <steps>
                <step id="1">Update plan.json status to "complete"</step>
                <step id="2">plan.md auto-generated by PostToolUse hook when plan.json is written</step>
                <step id="3">Update state.json:
                    ```json
                    {
                        "current_phase": "plan",
                        "phases": {
                            "plan": {
                                "status": "finalized",
                                "started_at": "{timestamp}",
                                "finalized_at": "{timestamp}"
                            }
                        },
                        "plan_state": {
                            "status": "finalized",
                            "checkpoints_total": 1,
                            "checkpoints_detailed": 1,
                            "checkpoints_completed": [],
                            "current_checkpoint": 1,
                            "last_updated": "{timestamp}"
                        }
                    }
                    ```
                </step>
            </steps>
            <output>
```markdown
## Plan Finalized

**Session**: `{session_id}`
**Checkpoints**: 1
**Tasks**: {N}

Ready for build. Run `/session:build {session_id}` to begin implementation.
```
            </output>
        </phase>

        <phase name="5b_adjust" condition="user requested adjustments">
            <description>Refine plan while staying in quick mode</description>
            <steps>
                <step id="1">Ask what specific adjustments are needed</step>
                <step id="2">Make changes to plan.json</step>
                <step id="3">Return to phase 4 (QA) to re-present</step>
            </steps>
        </phase>

        <phase name="5c_escalate" condition="user requested full plan">
            <description>Transition to interactive planning mode</description>
            <steps>
                <step id="1">Preserve existing plan.json as starting point</step>
                <step id="2">Update state.json to indicate escalation:
                    ```json
                    {
                        "plan_state": {
                            "status": "escalated_to_full",
                            "escalated_at": "{timestamp}",
                            "escalated_from": "quick_plan"
                        }
                    }
                    ```
                </step>
                <step id="3">Report escalation and guidance</step>
            </steps>
            <output>
```markdown
## Escalating to Full Plan Mode

The quick plan has been preserved as a starting point. Full plan mode will allow
tier-by-tier confirmation and interactive refinement.

**Next**: Continue with interactive planning using the existing plan as baseline.

The plan command will detect the escalation and continue from the current state.
```
            </output>
            <continuation>
                Continue execution as if /session:plan {session_id} was invoked,
                starting from the current plan state (checkpoint outline exists).
            </continuation>
        </phase>
    </workflow>
</workflows>

<behavior_constraints>
    DURING QUICK PLAN MODE:
    - DO NOT spawn sub-agents - execute everything directly
    - DO NOT require tier-by-tier confirmation (that's full plan)
    - DO use same plan.json structure as full plan for compatibility
    - DO assess complexity before committing to quick plan
    - DO provide clear escalation path to full plan
    - DO generate self-contained tasks (testable in isolation)

    ALLOWED WRITES:
    - agents/sessions/{session_id}/plan.json
    - agents/sessions/{session_id}/state.json

    NOTE: plan.md is auto-generated by PostToolUse hook when plan.json is written
</behavior_constraints>

<user_output>
    <scenario name="plan_generated" trigger="After auto-generation completes">
```markdown
## Quick Plan Generated

**Checkpoint 1**: {title}
**Goal**: {goal}

**Task Groups**:
{foreach task_group}
{group_number}. **{group.id}**: {group.title}
{foreach task in group}
   - Task {task.id}: {task.title} → `{task.file_path}`
{/foreach}
{/foreach}

**Estimated scope**: {file_count} files, {task_count} tasks

---

Review the plan above. You can:
- **Approve** to finalize and proceed to build
- **Adjust** to refine while staying in quick mode
- **Escalate** to switch to interactive full plan mode
```
    </scenario>

    <scenario name="complexity_warning" trigger="Task seems too complex for quick plan">
        Use AskUserQuestion:
        ```
        question: "This task seems more complex than typical quick plan scope. How would you like to proceed?"
        header: "Complexity"
        options:
          - label: "Continue with quick plan"
            description: "Generate a quick plan anyway - I'll escalate if needed"
          - label: "Switch to full plan"
            description: "Use interactive tier-by-tier planning for better control"
        ```
    </scenario>
</user_output>

<error_handling>
    <scenario name="No Session ID">
        Error: "Session ID required. Usage: /session:quick-plan {session_id}"
    </scenario>
    <scenario name="Session Not Found">
        Error: "Session '{$1}' not found. Use /session:spec to create a new session."
    </scenario>
    <scenario name="Spec Not Finalized">
        Error: "Spec not finalized. Run /session:spec {$1} finalize first."
    </scenario>
    <scenario name="Plan Already Finalized">
        Info: "Plan already finalized for this session. Run /session:build {$1} to begin."
    </scenario>
</error_handling>

## Example: Complete Quick Plan

For a spec with goal: "Fix typo in README and update copyright year"

### Generated plan.json

```json
{
  "$schema": "Plan schema for session checkpoint-based planning (v2)",
  "session_id": "2026-01-14_fix-readme-typo_a1b2c3",
  "spec_reference": "./spec.md",
  "created_at": "2026-01-14T10:00:00Z",
  "updated_at": "2026-01-14T10:00:00Z",
  "status": "complete",

  "checkpoints": [
    {
      "id": 1,
      "title": "Fix README and Update Copyright",
      "goal": "Correct spelling mistake and update copyright year to 2026",
      "prerequisites": [],
      "status": "pending",

      "file_context": {
        "beginning": {
          "files": [
            {"path": "README.md", "status": "exists", "description": "Project README with typo on line 15"}
          ],
          "tree": "README.md"
        },
        "ending": {
          "files": [
            {"path": "README.md", "status": "modified", "description": "Fixed typo and updated copyright"}
          ],
          "tree": "README.md"
        }
      },

      "testing_strategy": {
        "approach": "Manual review of changes",
        "verification_steps": [
          "git diff README.md",
          "Verify 'recieve' changed to 'receive'",
          "Verify copyright shows 2026"
        ]
      },

      "task_groups": [
        {
          "id": "1.1",
          "title": "Documentation Fixes",
          "objective": "Correct typo and update copyright in README",
          "status": "pending",
          "tasks": [
            {
              "id": "1.1.1",
              "title": "Fix typo in README",
              "file_path": "README.md",
              "description": "Change 'recieve' to 'receive' on line 15. This is a simple spelling correction identified during code review.",
              "status": "pending",
              "context": {
                "read_before": [
                  {"file": "README.md", "lines": "10-20", "purpose": "See typo in context"}
                ],
                "related_files": []
              },
              "depends_on": [],
              "actions": [
                {
                  "id": "1.1.1.1",
                  "command": "REPLACE 'recieve' WITH 'receive'",
                  "file": "README.md",
                  "status": "pending"
                }
              ]
            },
            {
              "id": "1.1.2",
              "title": "Update copyright year",
              "file_path": "README.md",
              "description": "Update copyright from 2025 to 2026 in the footer section. Annual update for new year.",
              "status": "pending",
              "context": {
                "read_before": [
                  {"file": "README.md", "lines": "last 10", "purpose": "Find copyright line"}
                ],
                "related_files": []
              },
              "depends_on": [],
              "actions": [
                {
                  "id": "1.1.2.1",
                  "command": "REPLACE '2025' WITH '2026' IN copyright line",
                  "file": "README.md",
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

### Key characteristics of quick plan:
- **Single checkpoint** - one logical unit of work
- **1-3 task groups** - minimal grouping
- **Self-contained tasks** - each task has full context
- **Simple verification** - straightforward testing strategy
