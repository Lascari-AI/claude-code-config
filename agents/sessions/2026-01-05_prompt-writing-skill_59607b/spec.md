# Spec: Update Prompt Writing Skill

**Session ID**: `2026-01-05_prompt-writing-skill_59607b`
**Status**: ✅ Finalized
**Created**: 2026-01-05
**Finalized**: 2026-01-05

---

> **This spec is finalized.** Ready for `/plan` phase.

---

## Overview

Restructure the `system_prompt` section of the prompt-writing skill to center on **workflow design** as the core discipline.

---

## Problem Statement

The current structure mixes concerns:
- Overview contains both routing AND the canonical template
- The distinction between single-completion and multi-turn isn't clearly framed around workflows
- The skill doesn't emphasize that **the system prompt IS the workflow**

**Why this matters**: When writing prompts, the workflow is the thing. Purpose, knowledge, goal, background—these are context. The workflow is what actually directs the model's behavior.

---

## Core Insight

From user input:

> "The core thing here is the **workflow**. This is a designated section for workflow design."

> "Single-completion: we're trying to get a lot of the workflow steps all done within the thinking window... It's for one-off tasks like processing."

> "Multi-turn: we are maintaining an external state... it's going through a much longer workflow with a lot of completions."

**Key distinction discovered from reference patterns:**

| Aspect | Single-Completion | Multi-Turn |
|--------|-------------------|------------|
| Workflow structure | `<steps>` | `<phases>` |
| Execution | Internal reasoning (thinking window) | External actions (tool calls, state) |
| State | None | External (JSON files, schemas) |
| Output | Single response | Incremental updates |
| Examples | Classification, extraction, generation | Research agents, session management |

---

## Goals

### High-Level

- **Reframe the skill around workflow design** as the central discipline
- Make the learning path clear: overview → base template → workflow design → pattern-specific guidance

### Mid-Level

1. **Overview**: Explains what this section covers + routing to appropriate file
2. **Base Template**: Canonical structure (purpose, knowledge, goal, background, workflow, rules)
3. **Workflow Design**: Core focus—how to design effective workflows
4. **Single-Completion Pattern**: Workflows for thinking-window execution
5. **Multi-Turn Pattern**: Workflows for external state and phased execution
6. **Special Cases**: Iterative loops, user-in-the-loop variants

---

## Proposed File Structure

```
system_prompt/
├── 00-overview.md              # What this section covers, routing
├── 10-base-template.md         # Canonical XML structure (purpose, knowledge, goal, etc.)
└── 20-workflow-design/         # FOLDER: Everything about workflow design
    ├── 00-overview.md          # Introduces workflow design, explains patterns
    ├── 10-base.md              # Core workflow principles (all patterns)
    ├── 20-single-completion.md # Pattern: thinking-window execution
    └── 30-multi-turn/          # Pattern: external state execution
        ├── 00-base.md          # Core: state schema, phases, autonomous execution
        ├── 10-iterative-loop.md    # Technique: user input each cycle
        └── 20-parallel-agents.md   # Technique: spawn subagents with own state
```

**Taxonomy:**
- **Single-completion** vs **Multi-turn** = The fundamental split (thinking window vs external state)
- **Techniques** (within multi-turn) = Ways to structure multi-turn workflows
  - Base/autonomous: Just phases, runs to completion
  - Iterative loop: User provides input each cycle
  - Parallel agents: Spawn subagents with own state

**Flow**:
1. Read `system_prompt/00-overview.md` → Routes to base-template or workflow-design
2. Read `10-base-template.md` → Canonical XML structure
3. Read `20-workflow-design/00-overview.md` → Understand workflow patterns
4. Read `20-workflow-design/10-base.md` → Core principles for all workflows
5. Read appropriate pattern:
   - `20-single-completion.md` for thinking-window execution
   - `30-multi-turn/00-base.md` for external state execution
   - Then technique files as needed (iterative-loop, parallel-agents)

---

## Key Distinctions to Emphasize

### Steps vs Phases

**Steps** (Single-Completion):
- Internal reasoning scaffold
- Model works through in thinking window
- No external feedback between steps
- Output is result of processing all steps

**Phases** (Multi-Turn):
- External execution flow
- Each phase involves tool calls, state updates
- Feedback between phases (tool results, state reads)
- Incremental output across multiple completions

### Workflow Design Principles

From reference patterns (`report-writer.md`, `research-subagent.md`):

1. **State Schema**: Multi-turn workflows define explicit state structure
2. **Output Protocol**: Where/how to write output (not just format)
3. **Phases with Actions**: Each phase has specific actions
4. **Principles**: Named principles guide behavior
5. **Error Handling**: Scenarios and recovery paths
6. **Critical Tags**: `<critical>` marks must-not-violate constraints

---

## File Content Responsibilities

### `system_prompt/00-overview.md`

Entry point for the section:
- What static AI instructions cover (system prompts, skills, agents, etc.)
- Routing to base-template vs workflow-design

### `system_prompt/10-base-template.md`

Canonical XML structure for ALL prompts:
- Purpose, key_knowledge, goal, background
- Workflow section structure
- Important rules
- Reference template to copy and adapt

### `20-workflow-design/00-overview.md`

Introduces workflow design discipline:
- Why workflows matter (they ARE the product)
- Single-completion vs multi-turn split
- How to navigate the pattern files

### `20-workflow-design/10-base.md` (Dense Reference)

Core principles for ALL workflows:
- XML structure patterns and conventions
- Steps vs phases distinction
- Constraint localization (global vs step-specific)
- Output format vs output protocol
- Using `<critical>` tags
- Error handling patterns
- Principles sections
- General structuring rules

### `20-workflow-design/20-single-completion.md`

Pattern for **thinking-window execution**:
- `<steps>` structure (internal reasoning scaffold)
- No external state
- Output is single response
- Examples: classification, extraction, generation

### `30-multi-turn/00-base.md`

Core pattern for **external state execution**:
- State schema design
- `<phases>` structure (external execution flow)
- Output protocol (where to write, not just format)
- Autonomous execution (runs to completion)
- Examples: research-subagent, report-writer

### `30-multi-turn/10-iterative-loop.md` (Technique)

User provides input each cycle:
- State machine stages (PREP → Q → REFLECT → END)
- Per-turn output format + final output format
- Memory handling rules
- Max rounds failsafe
- Examples: spec interviews, requirements gathering

### `30-multi-turn/20-parallel-agents.md` (Technique)

Spawn subagents with own state:
- Orchestrator pattern
- Subagent state files
- Coordination (spawn, wait, collect)
- Synthesis/report writing
- Examples: research system

---

## Success Criteria

- [ ] `system_prompt/00-overview.md` routes clearly to base-template or workflow-design
- [ ] `10-base-template.md` is standalone canonical XML structure
- [ ] `20-workflow-design/00-overview.md` introduces the discipline and explains patterns
- [ ] `20-workflow-design/10-base.md` is dense reference for all workflow principles
- [ ] `20-single-completion.md` emphasizes thinking-window design with `<steps>`
- [ ] `30-multi-turn/00-base.md` covers state schema and `<phases>`
- [ ] `30-multi-turn/10-iterative-loop.md` documents user-in-the-loop technique
- [ ] `30-multi-turn/20-parallel-agents.md` documents subagent spawning technique
- [ ] Examples from `.claude/agents/research/` inform the parallel-agents technique
- [ ] Examples from `.claude/skills/session/` inform the iterative-loop technique

---

## Open Questions

*None remaining*

---

## References

Multi-turn examples studied:
- `.claude/agents/research/report-writer.md` - Report synthesis with state
- `.claude/agents/research/research-subagent.md` - Incremental research with state updates
- `.claude/skills/session/` - Session management with phases

---

## Notes

The key realization: **workflows are the product**. Everything else (purpose, knowledge, goal, background) is context that informs workflow execution. The skill should teach workflow design as the primary discipline.
