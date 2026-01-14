# Implementation Plan

> **Session**: `2026-01-12_agent-session-overhaul_k9m2x7`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-01-14
> **Updated**: 2026-01-14

---

## Overview

- **Checkpoints**: 6 (0 complete)
- **Total Tasks**: 22

## ⬜ Checkpoint 1: Session Directory Structure & Initialization Script

**Goal**: Establish the foundation: update session directory structure and create Python initialization script. This creates the container that all subsequent features will use.

### ⬜ Task Group 1.1: Update Session Directory Templates

**Objective**: Update state.json template to include new fields for commits, research_artifacts, doc_updates, and enhanced plan_state tracking. Simplify context/ to flat structure.

#### ⬜ Task 1.1.1: Update state.json template with commits tracking

**File**: `.claude/skills/agent-session/spec/templates/state.json`

**Description**: Add commits array to state.json template. Each commit entry should link to a checkpoint ID. This enables traceability from commits back to the plan.

**Context to Load**:
- `.claude/skills/agent-session/spec/templates/state.json` (lines all) - Understand current state.json structure
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 119-142) - See commit format specification: checkpoint-{N}: + WHY + Changes

**Actions**:
- ⬜ **1.1.1.1**: ADD VAR commits = [] with schema: [{checkpoint_id, sha, message, created_at}] (`.claude/skills/agent-session/spec/templates/state.json`)

#### ⬜ Task 1.1.2: Enhance plan_state tracking in state.json template

**File**: `.claude/skills/agent-session/spec/templates/state.json`

**Description**: Update plan_state object to include checkpoints_total, checkpoints_detailed, and checkpoints_completed fields for better progress tracking during plan and build phases.

**Context to Load**:
- `.claude/skills/agent-session/spec/templates/state.json` (lines 48-57) - See current plan_state structure
- `.claude/skills/agent-session/plan/OVERVIEW.md` (lines 63-75) - See plan_state tracking requirements

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.2.1**: UPDATE VAR plan_state: ADD checkpoints_total, checkpoints_detailed, current_task_group fields (`.claude/skills/agent-session/spec/templates/state.json`)

#### ⬜ Task 1.1.3: Add detailed goals array to state.json template

**File**: `.claude/skills/agent-session/spec/templates/state.json`

**Description**: Add detailed goals array to goals object to match the three-tier goal structure (high_level, mid_level, detailed) defined in the spec.

**Context to Load**:
- `.claude/skills/agent-session/spec/templates/state.json` (lines 32-36) - See current goals structure (only high_level, mid_level)
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/state.json` (lines 29-61) - Example of three-tier goals in existing session

**Actions**:
- ⬜ **1.1.3.1**: ADD VAR detailed = [] to goals object (`.claude/skills/agent-session/spec/templates/state.json`)

### ⬜ Task Group 1.2: Create Python Initialization Script

**Objective**: Create a Python script that generates the session directory structure. Agent runs the script instead of manually creating directories. Saves tokens and ensures consistent structure.

#### ⬜ Task 1.2.1: Create session initialization Python script

**File**: `.claude/skills/agent-session/scripts/init-session.py`

**Description**: Create a Python script that initializes a new session directory structure. Takes session_id, topic, and optional description as arguments. Creates directories (research/, context/, debug/) and initializes state.json from template. Output minimal confirmation message for agent consumption.

**Context to Load**:
- `.claude/skills/agent-session/spec/templates/state.json` (lines all) - Template for state.json to be populated by the script
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 227-256) - See session directory structure specification
- `.claude/commands/agent-session/spec.md` (lines 79-106) - Current directory creation steps to be replaced

**Depends On**: Tasks 1.1.1, 1.1.2, 1.1.3

**Actions**:
- ⬜ **1.2.1.1**: CREATE FILE .claude/skills/agent-session/scripts/init-session.py (`.claude/skills/agent-session/scripts/init-session.py`)
- ⬜ **1.2.1.2**: CREATE FUNCTION main() with argparse: session_id (required), topic (required), description (optional) (`.claude/skills/agent-session/scripts/init-session.py`)
- ⬜ **1.2.1.3**: CREATE FUNCTION create_directories(session_path): research/, context/, debug/ (`.claude/skills/agent-session/scripts/init-session.py`)
- ⬜ **1.2.1.4**: CREATE FUNCTION init_state_json(session_path, session_id, topic, description): read template, populate, write (`.claude/skills/agent-session/scripts/init-session.py`)

### ⬜ Task Group 1.3: Update Spec Command for Script Usage

**Objective**: Modify the spec command to use the Python init script instead of mkdir commands. Update directory creation steps in the workflow.

#### ⬜ Task 1.3.1: Update spec command to call Python init script

**File**: `.claude/commands/agent-session/spec.md`

**Description**: Replace mkdir commands in the spec command workflow with a call to the Python init script. Update phase 2_resolve_session steps to run 'python .claude/skills/agent-session/scripts/init-session.py' with appropriate arguments. Remove individual mkdir steps.

**Context to Load**:
- `.claude/commands/agent-session/spec.md` (lines 64-106) - See current directory creation workflow in phase 2_resolve_session
- `.claude/skills/agent-session/scripts/init-session.py` (lines all) - Understand script interface (created in task 1.2.1)

**Depends On**: Tasks 1.2.1

**Actions**:
- ⬜ **1.3.1.1**: REPLACE mkdir commands in step id=3 with: python .claude/skills/agent-session/scripts/init-session.py {session_id} {topic} {description} (`.claude/commands/agent-session/spec.md`)
- ⬜ **1.3.1.2**: UPDATE step id=4: REMOVE Initialize state.json (now handled by script) (`.claude/commands/agent-session/spec.md`)
- ⬜ **1.3.1.3**: UPDATE step id=7: REMOVE Create initial spec.md reference (script creates it) (`.claude/commands/agent-session/spec.md`)

#### ⬜ Task 1.3.2: Update SKILL.md with new directory structure

**File**: `.claude/skills/agent-session/SKILL.md`

**Description**: Update the Session Directory Structure section in SKILL.md to reflect the simplified structure: flat context/ (no subdirectories), debug/ added, and note about using Python init script.

**Context to Load**:
- `.claude/skills/agent-session/SKILL.md` (lines 147-155) - See current directory structure documentation
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 227-256) - See new directory structure specification

**Actions**:
- ⬜ **1.3.2.1**: UPDATE directory structure: ADD debug/ directory (`.claude/skills/agent-session/SKILL.md`)
- ⬜ **1.3.2.2**: UPDATE directory structure: REPLACE context/ subdirectories with flat context/ (`.claude/skills/agent-session/SKILL.md`)

---

## ⬜ Checkpoint 2: Research Integration - Store Research Within Sessions

**Goal**: Modify research system to output within session directories (research/{id}/) with phase metadata tracking. Update research commands to accept session context.

**Prerequisites**: Checkpoints 1

### ⬜ Task Group 2.1: Add Session-Aware Research Command

**Objective**: Create a new research command variant that accepts an agent session ID and outputs research artifacts within that session's research/ directory. Includes phase metadata (spec/plan/debug) and triggered_by tracking.

#### ⬜ Task 2.1.1: Create session-research command

**File**: `.claude/commands/agent-session/research.md`

**Description**: Create a new research command under agent-session namespace. Accepts --session={session-id} --phase={spec|plan|debug} --triggered-by={reason}. Outputs to agents/sessions/{session-id}/research/{research-id}/ instead of research_sessions/. Mirrors existing research.md structure but with session awareness.

**Context to Load**:
- `.claude/commands/development/research.md` (lines all) - Understand existing research orchestrator structure to mirror
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 233-256) - See research directory structure and state.json schema

**Actions**:
- ⬜ **2.1.1.1**: CREATE FILE .claude/commands/agent-session/research.md (`.claude/commands/agent-session/research.md`)
- ⬜ **2.1.1.2**: MIRROR development/research.md structure with session-aware variables (`.claude/commands/agent-session/research.md`)
- ⬜ **2.1.1.3**: ADD argument parsing: --session (required), --phase (required), --triggered-by (required) (`.claude/commands/agent-session/research.md`)
- ⬜ **2.1.1.4**: UPDATE directory_structure to use agents/sessions/{session-id}/research/{research-id}/ (`.claude/commands/agent-session/research.md`)
- ⬜ **2.1.1.5**: UPDATE session_state_schema to include phase, triggered_by, mode fields (`.claude/commands/agent-session/research.md`)

### ⬜ Task Group 2.2: Implement Light Research Mode

**Objective**: Add a --mode=light option that uses a single research agent instead of parallel subagents. Simpler output structure for chores/quick tasks. Still stores within session.

#### ⬜ Task 2.2.1: Add light mode to session-research command

**File**: `.claude/commands/agent-session/research.md`

**Description**: Add --mode={light|full} argument. Light mode spawns a single research agent that investigates directly without subagent decomposition. Output structure is simpler: just state.json and report.md (no subagents/ directory). Default to light mode if not specified.

**Context to Load**:
- `.claude/commands/agent-session/research.md` (lines all) - Understand current session-research structure (created in 2.1.1)
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 73-78) - See light vs full research mode requirements

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.2.1.1**: ADD argument: --mode={light|full} DEFAULT light (`.claude/commands/agent-session/research.md`)
- ⬜ **2.2.1.2**: ADD conditional workflow: if mode=light, spawn single agent; if mode=full, spawn parallel subagents (`.claude/commands/agent-session/research.md`)
- ⬜ **2.2.1.3**: UPDATE directory_structure for light mode: no subagents/ directory (`.claude/commands/agent-session/research.md`)

### ⬜ Task Group 2.3: Update Research Subagent for Session Context

**Objective**: Modify research-subagent.md to accept session path as parameter and output to session/research/{id}/subagents/. Add phase metadata to subagent output.

#### ⬜ Task 2.3.1: Update research-subagent for session context

**File**: `.claude/agents/research/research-subagent.md`

**Description**: Modify research-subagent.md to accept a session_path parameter that can be either research_sessions/{id}/ (legacy) or agents/sessions/{session-id}/research/{research-id}/. Update state file output path accordingly. This allows the same subagent to work with both the old research command and new session-aware command.

**Context to Load**:
- `.claude/agents/research/research-subagent.md` (lines all) - Understand current subagent structure and state file format

**Actions**:
- ⬜ **2.3.1.1**: UPDATE input_format: session_path is now the full path (not just research_sessions/) (`.claude/agents/research/research-subagent.md`)
- ⬜ **2.3.1.2**: UPDATE output_protocol: use session_path for state file location (`.claude/agents/research/research-subagent.md`)

### ⬜ Task Group 2.4: Track Research Artifacts in Session State

**Objective**: Update session state.json with research_artifacts array after research completes. Add back-links to spec.md referencing research reports.

#### ⬜ Task 2.4.1: Update research_artifacts in session state after research

**File**: `.claude/commands/agent-session/research.md`

**Description**: After research completes, update the parent session's state.json to add the research artifact to research_artifacts array. Include path to report.md and research session metadata.

**Context to Load**:
- `.claude/commands/agent-session/research.md` (lines all) - Understand session-research command (created in 2.1.1)
- `.claude/skills/agent-session/spec/templates/state.json` (lines all) - See research_artifacts field in state.json template

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.4.1.1**: ADD phase to update session state.json after research completes (`.claude/commands/agent-session/research.md`)
- ⬜ **2.4.1.2**: ADD action: append {research_id, report_path, phase, triggered_by} to research_artifacts array (`.claude/commands/agent-session/research.md`)

---

## ⬜ Checkpoint 3: Planning Modes - Quick and Full Plans

**Goal**: Implement two planning modes (quick: auto-generate ~1 checkpoint, full: interactive multi-checkpoint) with consistent plan structure. Add mode selection and escalation.

**Prerequisites**: Checkpoints 1

### ⬜ Task Group 3.1: Add Quick Plan Mode Command

**Objective**: Create a quick plan command that auto-generates a simple ~1 checkpoint plan without interactive tiered confirmation. User QAs the result; can escalate if needed.

#### ⬜ Task 3.1.1: Create quick-plan command

**File**: `.claude/commands/agent-session/quick-plan.md`

**Description**: Create a new plan command variant for chores/simple fixes. Auto-generates plan with ~1 checkpoint based on spec. Skips tiered confirmation. Outputs same plan.json structure for consistency. User QAs and can refine if plan is wrong.

**Context to Load**:
- `.claude/commands/agent-session/plan.md` (lines all) - Understand existing full plan command structure
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 82-94) - See quick plan mode requirements

**Actions**:
- ⬜ **3.1.1.1**: CREATE FILE .claude/commands/agent-session/quick-plan.md (`.claude/commands/agent-session/quick-plan.md`)
- ⬜ **3.1.1.2**: ADD workflow: read spec, auto-generate single checkpoint, write plan.json (`.claude/commands/agent-session/quick-plan.md`)
- ⬜ **3.1.1.3**: ADD QA step: present plan to user for review with option to refine (`.claude/commands/agent-session/quick-plan.md`)

### ⬜ Task Group 3.2: Update Plan Command as Full Mode

**Objective**: Rename/clarify existing plan command as 'full plan' mode. Ensure it's the default for complex features. Add mode detection hints.

#### ⬜ Task 3.2.1: Clarify plan command as full mode

**File**: `.claude/commands/agent-session/plan.md`

**Description**: Update existing plan command to clarify it's the 'full' interactive mode. Add guidance on when to use full vs quick plan. Add option to suggest quick plan if task seems simple.

**Context to Load**:
- `.claude/commands/agent-session/plan.md` (lines all) - Current plan command structure

**Actions**:
- ⬜ **3.2.1.1**: UPDATE description to clarify this is 'full' interactive planning mode (`.claude/commands/agent-session/plan.md`)
- ⬜ **3.2.1.2**: ADD guidance section: when to use full vs quick plan (`.claude/commands/agent-session/plan.md`)

### ⬜ Task Group 3.3: Add Escalation Flow

**Objective**: Enable escalating from quick plan to full plan if the auto-generated plan is wrong during QA. Same session, refine the plan interactively.

#### ⬜ Task 3.3.1: Add escalation from quick to full plan

**File**: `.claude/commands/agent-session/quick-plan.md`

**Description**: Add escalation option in quick-plan QA step. If user says plan needs more work, transition to full plan mode for interactive refinement. Keep same session, don't create new plan.json.

**Context to Load**:
- `.claude/commands/agent-session/quick-plan.md` (lines all) - Quick plan command (created in 3.1.1)

**Depends On**: Tasks 3.1.1

**Actions**:
- ⬜ **3.3.1.1**: ADD AskUserQuestion in QA step: options include 'Escalate to full plan' (`.claude/commands/agent-session/quick-plan.md`)
- ⬜ **3.3.1.2**: ADD escalation handler: if escalate, invoke plan.md logic for interactive refinement (`.claude/commands/agent-session/quick-plan.md`)

### ⬜ Task Group 3.4: Update SKILL.md with Planning Modes

**Objective**: Document both planning modes in SKILL.md. Explain when to use each, correlation with research modes.

#### ⬜ Task 3.4.1: Document planning modes in SKILL.md

**File**: `.claude/skills/agent-session/SKILL.md`

**Description**: Add section explaining quick vs full planning modes. Include guidance on mode selection, correlation with research modes (light research → quick plan, full research → full plan), and escalation flow.

**Context to Load**:
- `.claude/skills/agent-session/SKILL.md` (lines 117-131) - Current Phases section to update

**Actions**:
- ⬜ **3.4.1.1**: UPDATE Plan Phase section: add quick vs full mode explanation (`.claude/skills/agent-session/SKILL.md`)
- ⬜ **3.4.1.2**: ADD Commands table entry for /session:quick-plan (`.claude/skills/agent-session/SKILL.md`)

---

## ⬜ Checkpoint 4: Build Phase - Checkpoint Commits with Traceability

**Goal**: Update build phase to create checkpoint commits in specified format, track commits in state.json linked to checkpoints, and update commit message templates.

**Prerequisites**: Checkpoints 1, 3

### ⬜ Task Group 4.1: Update Build Command for Checkpoint Commits

**Objective**: Modify build commands to create git commits in the specified format after each checkpoint completes. Format: checkpoint-{N}: {description} + WHY body + Changes list.

#### ⬜ Task 4.1.1: Add checkpoint commit creation to build command

**File**: `.claude/commands/agent-session/build.md`

**Description**: Update build command to create a git commit after each checkpoint completes verification. Use format: checkpoint-{N}: {brief description} with body containing WHY explanation and Changes bullet list. Follow git skill conventions.

**Context to Load**:
- `.claude/commands/agent-session/build.md` (lines all) - Current build command structure
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 119-147) - See checkpoint commit format specification
- `.claude/skills/agent-session/build/OVERVIEW.md` (lines 115-128) - Current git commit section in build OVERVIEW

**Actions**:
- ⬜ **4.1.1.1**: UPDATE git commit section: use HEREDOC format with checkpoint-{N}: subject (`.claude/commands/agent-session/build.md`)
- ⬜ **4.1.1.2**: ADD commit body format: WHY explanation + Changes bullet list (`.claude/commands/agent-session/build.md`)

#### ⬜ Task 4.1.2: Update build-background command for checkpoint commits

**File**: `.claude/commands/agent-session/build-background.md`

**Description**: Same commit format updates for the autonomous build command.

**Context to Load**:
- `.claude/commands/agent-session/build-background.md` (lines all) - Current build-background command structure

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.1.2.1**: MIRROR commit format from build.md (`.claude/commands/agent-session/build-background.md`)

### ⬜ Task Group 4.2: Track Commits in Session State

**Objective**: After each checkpoint commit, update state.json commits array with commit metadata linked to checkpoint ID.

#### ⬜ Task 4.2.1: Add commit tracking to build commands

**File**: `.claude/commands/agent-session/build.md`

**Description**: After creating git commit, update session state.json commits array. Each entry includes: checkpoint_id, sha (from git log), message, created_at. This enables traceability from commits back to checkpoints.

**Context to Load**:
- `.claude/skills/agent-session/spec/templates/state.json` (lines all) - See commits array structure (added in task 1.1.1)

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.2.1.1**: ADD step after git commit: get SHA with git log -1 --format='%H' (`.claude/commands/agent-session/build.md`)
- ⬜ **4.2.1.2**: ADD step: update state.json commits array with {checkpoint_id, sha, message, created_at} (`.claude/commands/agent-session/build.md`)

### ⬜ Task Group 4.3: Update Build OVERVIEW Documentation

**Objective**: Update build/OVERVIEW.md to reflect new commit format and tracking requirements.

#### ⬜ Task 4.3.1: Update build OVERVIEW with commit format

**File**: `.claude/skills/agent-session/build/OVERVIEW.md`

**Description**: Update the Git Commit section with the new commit format (checkpoint-{N}: + WHY + Changes). Add section on commit tracking in state.json.

**Context to Load**:
- `.claude/skills/agent-session/build/OVERVIEW.md` (lines 115-128) - Current git commit documentation

**Actions**:
- ⬜ **4.3.1.1**: UPDATE Git Commit section with new format: checkpoint-{N}: + WHY body + Changes (`.claude/skills/agent-session/build/OVERVIEW.md`)
- ⬜ **4.3.1.2**: ADD section: Commit Tracking in state.json (`.claude/skills/agent-session/build/OVERVIEW.md`)

---

## ⬜ Checkpoint 5: Debug Integration as Spec Sub-Phase

**Goal**: Integrate debug as a sub-phase within spec. Debug changes are ephemeral (not committed), understanding captured in debug/ artifacts. Add debug flow to spec phase.

**Prerequisites**: Checkpoints 1

### ⬜ Task Group 5.1: Add Debug Sub-Phase to Spec Command

**Objective**: Modify spec command to support entering debug sub-phase. Debug is for understanding (ephemeral changes), findings go to debug/ artifacts.

#### ⬜ Task 5.1.1: Add debug sub-phase workflow to spec command

**File**: `.claude/commands/agent-session/spec.md`

**Description**: Add a debug sub-phase that can be entered during spec. Flow: SPEC → DEBUG → SPEC (informed). Debug phase allows ephemeral code changes (for understanding), captures findings in debug/{issue}.md. Changes are NOT committed. After debug, return to spec with new understanding.

**Context to Load**:
- `.claude/commands/agent-session/spec.md` (lines all) - Current spec command structure
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 48-68) - Debug integration requirements and flow diagram

**Actions**:
- ⬜ **5.1.1.1**: ADD phase: debug_sub_phase between question_driven_exploration and finalize (`.claude/commands/agent-session/spec.md`)
- ⬜ **5.1.1.2**: ADD trigger: when user wants to investigate a bug during spec (`.claude/commands/agent-session/spec.md`)
- ⬜ **5.1.1.3**: ADD debug artifact creation: debug/{issue}.md with findings (`.claude/commands/agent-session/spec.md`)
- ⬜ **5.1.1.4**: ADD principle: debug changes are ephemeral, not committed (`.claude/commands/agent-session/spec.md`)

### ⬜ Task Group 5.2: Update SKILL.md with Debug Integration

**Objective**: Document the debug sub-phase in SKILL.md and spec/OVERVIEW.md.

#### ⬜ Task 5.2.1: Document debug sub-phase in skill docs

**File**: `.claude/skills/agent-session/SKILL.md`

**Description**: Add section explaining debug as sub-phase of spec. Include flow diagram, explain ephemeral changes concept, and how debug findings inform the spec.

**Context to Load**:
- `.claude/skills/agent-session/SKILL.md` (lines 117-131) - Current Phases section

**Actions**:
- ⬜ **5.2.1.1**: UPDATE Spec Phase section: add debug sub-phase explanation (`.claude/skills/agent-session/SKILL.md`)
- ⬜ **5.2.1.2**: ADD flow diagram: SPEC → DEBUG → SPEC (informed) → PLAN → BUILD (`.claude/skills/agent-session/SKILL.md`)

---

## ⬜ Checkpoint 6: Documentation Cleanup Phase

**Goal**: Add doc cleanup phase at end of session. Agent determines what needs updating using docs-framework skill. Updates happen after build + tests pass, not per-checkpoint.

**Prerequisites**: Checkpoints 1, 4

### ⬜ Task Group 6.1: Create Doc Cleanup Command

**Objective**: Create a new command for the documentation cleanup phase. Agent reviews changes + spec, determines what docs need updating using docs-framework skill knowledge.

#### ⬜ Task 6.1.1: Create doc-cleanup command

**File**: `.claude/commands/agent-session/doc-cleanup.md`

**Description**: Create a new command for documentation cleanup phase at end of session. Agent: 1) Reviews commits made during build, 2) Reads spec for context, 3) Uses docs-framework skill to determine what needs updating, 4) Updates relevant docs (L2/L3 codebase docs, L4 headers, L5 docstrings as needed), 5) Updates state.json doc_updates array.

**Context to Load**:
- `agents/sessions/2026-01-12_agent-session-overhaul_k9m2x7/spec.md` (lines 97-108) - Doc integration requirements
- `.claude/skills/docs-framework/SKILL.md` (lines all) - Understand docs-framework skill for intelligent doc decisions

**Actions**:
- ⬜ **6.1.1.1**: CREATE FILE .claude/commands/agent-session/doc-cleanup.md (`.claude/commands/agent-session/doc-cleanup.md`)
- ⬜ **6.1.1.2**: ADD workflow: read commits, read spec, analyze changes significance (`.claude/commands/agent-session/doc-cleanup.md`)
- ⬜ **6.1.1.3**: ADD decision logic: USE docs-framework skill to determine what needs updating (`.claude/commands/agent-session/doc-cleanup.md`)
- ⬜ **6.1.1.4**: ADD action: update relevant docs using docs/write and docs/annotate patterns (`.claude/commands/agent-session/doc-cleanup.md`)
- ⬜ **6.1.1.5**: ADD state update: append to doc_updates array in state.json (`.claude/commands/agent-session/doc-cleanup.md`)

### ⬜ Task Group 6.2: Update Session Lifecycle Documentation

**Objective**: Update SKILL.md to include the doc cleanup phase in the session lifecycle. Add command to commands table.

#### ⬜ Task 6.2.1: Update SKILL.md with doc cleanup phase

**File**: `.claude/skills/agent-session/SKILL.md`

**Description**: Add doc cleanup as final phase before session completion. Update lifecycle diagram. Explain that not every session needs doc updates - agent determines significance.

**Context to Load**:
- `.claude/skills/agent-session/SKILL.md` (lines 27-32) - Current session lifecycle diagram

**Actions**:
- ⬜ **6.2.1.1**: UPDATE Session Lifecycle diagram: add DOC CLEANUP between BUILD and COMPLETE (`.claude/skills/agent-session/SKILL.md`)
- ⬜ **6.2.1.2**: ADD Commands table entry for /session:doc-cleanup (`.claude/skills/agent-session/SKILL.md`)
- ⬜ **6.2.1.3**: ADD note: not every session needs doc updates - agent determines (`.claude/skills/agent-session/SKILL.md`)

---

---
*Auto-generated from plan.json on 2026-01-14 14:47*