# Agent Session Overhaul - Tying Everything Together

> **Session**: `2026-01-12_session-overhaul_k9m2x7`
> **Status**: ✅ Finalized
> **Created**: 2026-01-12
> **Finalized**: 2026-01-12

---
**SPEC FINALIZED** - This specification has been reviewed and approved. Ready for planning phase.

---

## Overview

A comprehensive overhaul of the agent session system to unify currently-separate agent systems (research, debug, docs) into a single cohesive session flow. The vision: every development task—feature, bug, chore—flows through one session that contains ALL artifacts with full traceability.

## Problem Statement

**Current State**: Various agent systems work well individually but are disconnected:
- Research agents output to a separate directory
- Debug sessions are standalone
- Documentation updates happen outside the development flow
- No bidirectional linking between artifacts
- Context is scattered rather than contained

**Desired State**: A unified session where:
- Everything starts with spec (understanding the problem fully before planning)
- Research is kicked off during spec and stored within the session
- All artifacts (research, plans, commits, doc updates) are contained in one folder
- Back-links connect spec ↔ research ↔ plan ↔ code changes ↔ docs
- Complete record of everything that happened for a given development cycle

## Goals

### High-Level Goals

**One session = complete development record**: Every development task (feature, bug, chore) flows through a unified session containing all artifacts with full traceability. WHY: Enables understanding what happened, why decisions were made, and how code evolved—all in one place.

### Mid-Level Goals

1. **Integrate Research into Sessions**: Research agents kick off during spec phase, output stored within session directory, back-linked to spec/plan. WHY: Research context shouldn't be orphaned—it informs the spec and should be traceable.

2. **Two Planning Modes (Quick/Full)**: Quick plan for chores/simple fixes (auto-generates, just QA). Full plan for complex features (more oversight). WHY: Not every task needs heavyweight process.

3. **Build with Checkpoint Commits**: Each checkpoint completion triggers a commit. WHY: Atomic, traceable progress.

4. **Documentation Agent Integration**: Docs updated as part of flow, referencing back to the spec that triggered changes. WHY: Docs should evolve with code, not be an afterthought.

5. **Debug Integration in Spec Phase**: Debug is a **sub-phase within spec**, not a separate session or checkpoint.

   **Flow**:
   ```
   SPEC ──▶ (need to understand bug) ──▶ DEBUG SUB-PHASE ──▶ SPEC (now informed) ──▶ PLAN ──▶ BUILD
                                              │
                                              ├── Make ephemeral changes (logs, repro)
                                              ├── Investigate and understand
                                              ├── Capture findings in debug/ artifacts
                                              └── Changes are NOT committed (revert or discard)
   ```

   **Key principles**:
   - Debug changes are **ephemeral** (for understanding only, not committed)
   - Understanding goes into `debug/{issue}.md` artifacts
   - After debug completes, return to spec phase with new understanding
   - Plan phase implements the proper fix based on debug findings
   - **NOT checkpoint 0** - Plan/build should be automatable without debug's messy investigation changes

   WHY this model: Keeps plan/build clean and automatable. Debug is exploratory; plan/build is deliberate.

### Detailed Goals

**Research Integration**:
- Research triggered by: user-initiated OR agent-initiated with confirmation (NOT automatic based on topic/complexity—too complex)
- Research is needed for almost any task (understanding codebase before speccing/planning)
- Two modes:
  - **Light**: Single research agent (chores, quick tasks) - reads docs, greps, LSP
  - **Full**: Parallel research agents (complex features) - multiple subagents, report synthesis
- **Critical**: Use research agent system, NOT built-in explore tool. WHY: Observability. Research agent tracks everything (examined files, line ranges, learnings), providing traceability if agent fails or we need to understand what happened.

**Planning Modes**:
- **Goal**: Consistent plan structure for EVERY change. Even chores get a documented plan for traceability.
- **Quick Plan**:
  - Not interactive - generates plan automatically
  - Usually one checkpoint
  - For simple changes, quick fixes, chores
  - User QAs the result; can refine if needed (goes back to interview mode to update)
  - Pairs with **light research**
- **Full Plan**:
  - Interactive planning with oversight
  - Multiple checkpoints for complex changes
  - For features touching multiple parts of codebase
  - Pairs with **full research**
- **Mode selection**: User can choose if in the loop; agent may suggest based on complexity
- **Escalation**: If quick plan looks wrong during QA, just continue refining (same session, interview mode to update plan). Not a separate session.

**Documentation Integration**:
- **When**: At the END of session, after build is finalized and tests pass. A "cleanup" phase, not after each checkpoint.
- **What gets updated**: Agent determines this intelligently:
  - Codebase docs (`docs/10-codebase/`) for significant changes
  - Code-level headers and docstrings
  - Whatever the docs framework skill knowledge indicates is needed
- **Agent-driven decision**: Doc agent looks at checkpoint changes + spec (the "what" and "why") and decides:
  - Whether docs need updating at all (chore changing variable naming = probably not)
  - Where to update (using docs framework skill understanding)
  - What to change (headers, docstrings, codebase docs)
- **Key philosophy**: Rely on model intelligence + docs framework skill, NOT prescriptive rules. Agent has the knowledge to make good decisions about what needs documentation.
- **Not every session needs doc updates**: Agent determines significance. Dead code removal, variable renames, simple fixes may not warrant doc changes.

**Back-links and Traceability**:
- **Dual approach**:
  1. **Inline markdown links**: Human-readable navigation within documents (e.g., `See [auth research](./research/auth-system.md)`)
  2. **state.json as manifest**: Machine-readable overview of all artifacts and relationships
- **state.json tracks**:
  - `research_artifacts`: List of research files generated
  - `commits`: Git commits made during session, **linked to their checkpoint**
- **Commit ↔ Checkpoint linkage**: Each checkpoint in the plan knows which commit(s) it produced
- **Complete traceability chain**: spec → research → plan → checkpoint → commit → doc updates

**Checkpoint Commit Format**:
```
checkpoint-{N}: {Brief description}

{WHY - explanation of the reasoning behind the change}

Changes:
- {bullet list of what changed}
- {specific modifications}
```

Example:
```
checkpoint-4: Replace _inflight_spans with correlation_id pattern

Remove in-app timing state management in favor of correlation_id for grouping
related start/end events. This simplifies the TracePublisher by making it stateless
for span tracking.

Changes:
- Remove _inflight_spans dict from __init__
- Update ai_processing_start/complete to return/accept correlation_id
- Add user_id parameter to all updated methods
```

- Subject line: `checkpoint-{N}: {Brief description}`
- Body: Explains WHY (reasoning), not just what
- Changes section: Quick overview of WHAT was modified
- Follows existing git skill conventions where applicable

## Non-Goals

*What we are explicitly NOT building - prevents scope creep*

-

## Success Criteria

*How do we know we're done? Testable outcomes*

- [ ]

## Context & Background

### Existing Research System (`.claude/agents/research/`)

The research system is designed for **parallel investigation**:
- **Orchestrator** (`/research` command): Decomposes questions into parallel queries, spawns subagents
- **Research Subagents**: Focused investigation of one aspect, incrementally writes findings to state files
- **Report Writer**: Synthesizes all subagent findings into a styled report (cookbook/understanding/context)

Current output location: `research_sessions/{session_id}/`

Key design: Subagents record `examined` files with line ranges and `learned` insights. Report writer reads the actual code files to create reports with real code snippets.

### Existing Docs Framework (`.claude/skills/docs-framework/`)

Structured documentation designed to **capture WHY**, not just what:
- `docs/00-foundation/` - Purpose, principles, boundaries
- `docs/10-codebase/` - Mirrors source structure
- Cookbooks: Navigate (understand), Produce (create), Maintain (update)

Key insight: Docs framework is designed so research can read docs to understand the reasoning behind existing code.

### User's Mental Model

**Research as informed checkpoint, not constant background process**:

The user's preference is nuanced—NOT fully parallel background research, because:
1. **Coherence matters**: Continuing interview without research findings could lead to misaligned understanding
2. **Cost awareness**: Research agents are expensive and slow; shouldn't constantly kick off
3. **Understanding must stay in sync**: The interviewer needs research findings to ask informed questions

Two viable patterns:
- **Blocking research**: Pause interview → run research → continue with full understanding
- **Checkpoint research**: Kick off research when a topic needs investigation, brief pause, then sync up

Key insight: Research is about ensuring the agent has **complete understanding** before proceeding, not just background context gathering.

## Key Decisions

*Capture the WHY behind decisions, not just the WHAT. Include user's reasoning and preferences.*

| Decision | Rationale | Date |
|----------|-----------|------|
|          |           |      |

## Open Questions

- [x] What specific pain points exist with the current agent session system? → Disconnected systems (research, debug, docs separate from session)
- [x] What does 'tying everything together' mean? → Unified session containing all artifacts with back-links
- [x] How is research triggered? → User-initiated OR agent-initiated with confirmation (not automatic)
- [x] Research modes? → Light (single agent) vs Full (parallel agents) based on task complexity
- [x] Why use research agent over built-in explore? → Observability/traceability
- [x] Quick vs Full plan? → Quick = auto-generate (1 checkpoint, chores), Full = interactive (multi-checkpoint, features). User chooses or agent suggests. Both produce consistent plan structure.
- [x] Research ↔ Plan correlation? → Light research → Quick plan, Full research → Full plan
- [x] What docs need updating? → Agent determines intelligently using docs framework skill. Headers, docstrings, codebase docs as needed.
- [x] When do docs update? → At END of session (cleanup phase after build + tests pass), not per-checkpoint
- [x] How does doc agent know what to update? → Looks at changes + spec + docs framework skill knowledge. Relies on model intelligence.
- [x] How do back-links work? → Dual: inline markdown links (human-readable) + state.json manifest (machine-readable overview)
- [x] Track commits? → Yes, in state.json, linked to their checkpoint
- [x] Commit message format? → `checkpoint-{N}: {description}` + WHY body + Changes bullet list
- [x] Debug integration with code changes? → Debug is sub-phase of spec. Changes are ephemeral (not committed). Understanding captured in debug/ artifacts. Return to spec informed, then plan the proper fix.
- [x] Session directory structure? → Confirmed. context/ is flat. Research organized by session with phase metadata. Python script for initialization.

## Session Directory Structure

**Layout**:
```
agents/sessions/{session-id}/
├── state.json           # Session state, phase tracking, artifacts list, commits
├── spec.md              # WHAT: Goals, requirements, decisions
├── plan.json            # HOW: Checkpoints and tasks (machine-readable)
├── plan.md              # HOW: Human-readable plan (generated from plan.json)
├── research/            # Research artifacts (organized by research session)
│   ├── {research-id}/   # Each research session is isolated
│   │   ├── state.json   # Metadata: phase, triggered_by, mode (light/full)
│   │   ├── report.md    # Synthesized findings
│   │   └── subagents/   # Raw subagent findings (if full research)
│   │       └── subagent_001.json
│   └── {research-id}/   # Another research session
│       └── ...
├── context/             # Supporting materials (flat - diagrams, notes, external context)
└── debug/               # Debug session artifacts (if debugging occurred)
    └── {issue}.md       # Debug findings, reproduction steps, root cause
```

**Research Session Metadata** (`research/{id}/state.json`):
```json
{
  "id": "auth-flow-understanding_20260112_143022",
  "phase": "spec",           // When: spec, plan, debug
  "triggered_by": "Need to understand how auth tokens are validated",
  "mode": "light",           // light or full
  "status": "complete",
  "created_at": "2026-01-12T14:30:22Z"
}
```

**Benefits**:
- See exactly when each research happened (spec vs plan vs debug)
- Understand WHY each research was triggered
- Subagents are isolated per research session (not mixed together)
- Easy to trace: "research session X was triggered during spec to understand Y"

**Notes**:
- `debug/` captures debugging investigation if it happened during spec
- `context/` is **flat** - just a place for any supporting materials (rarely used)
- `plan.json` is source of truth; `plan.md` is generated for readability

**Session Initialization**:
- Create a Python script to generate directory structure
- Agent runs the script instead of manually creating directories
- Saves tokens and ensures consistent structure

## Diagrams

### Unified Session Flow (Draft)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED SESSION                                      │
│  agents/sessions/{session-id}/                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        SPEC PHASE                               │    │
│  │                                                                 │    │
│  │   ┌──────────────┐         ┌──────────────────────────────┐     │    │
│  │   │  Interview   │◀───────▶│  Background Research         │     │    │
│  │   │  (user ↔ AI) │         │  • Reads docs for "why"      │     │    │
│  │   │              │  topics │  • Reads code for context    │     │    │
│  │   │              │────────▶│  • Outputs to research/      │     │    │
│  │   └──────┬───────┘         └──────────────────────────────┘     │    │
│  │          │                              │                       │    │
│  │          ▼                              ▼                       │    │
│  │   ┌──────────────┐             ┌──────────────┐                 │    │
│  │   │   spec.md    │◀────────────│  research/   │                 │    │
│  │   │  (enriched)  │  back-links │  *.md/*.json │                 │    │
│  │   └──────────────┘             └──────────────┘                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     PLAN PHASE                                  │    │
│  │                                                                 │    │
│  │   Quick Plan ────────────▶ Auto-generate, user QAs result       │    │
│  │   Full Plan  ────────────▶ Interactive planning with oversight  │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     BUILD PHASE                                 │    │
│  │                                                                 │    │
│  │   Checkpoint 1 ──▶ commit ──▶ doc update                        │    │
│  │   Checkpoint 2 ──▶ commit ──▶ doc update                        │    │
│  │   ...                                                           │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Notes

### Design Philosophy: Rely on Model Intelligence

A key principle across this system: **trust the agent's intelligence rather than prescribing exact rules**.

Examples:
- Doc agent determines what needs updating (not prescriptive "update X when Y")
- Research agent decides what's relevant (not prescriptive file lists)
- Agent suggests research/plan mode based on complexity (not rigid triggers)

The skills (docs-framework, research agents) provide **knowledge**; the agent applies that knowledge **intelligently**. This is more maintainable than complex rule systems and leverages what LLMs are good at.

### Session Lifecycle (Current Understanding)

```
SPEC ──▶ RESEARCH ──▶ PLAN ──▶ BUILD ──▶ TEST ──▶ DOC CLEANUP ──▶ COMPLETE
  │         │           │         │                    │
  │    (light/full)  (quick/     (checkpoint          (agent determines
  │                   full)       commits)             what needs update)
  │
  └── interview + research checkpoints
```

### Enhanced state.json Structure (Draft)

```json
{
  "session_id": "2026-01-12_feature-x_abc123",
  "topic": "Feature X",
  // ... existing fields ...

  "research_artifacts": [
    "research/auth-system.md",
    "research/database-layer.md"
  ],

  "checkpoints": [
    {
      "id": 1,
      "title": "Add service skeleton",
      "status": "complete",
      "commits": ["abc1234", "def5678"]
    },
    {
      "id": 2,
      "title": "Implement core logic",
      "status": "complete",
      "commits": ["ghi9012"]
    }
  ],

  "doc_updates": [
    "docs/10-codebase/services/feature-x.md"
  ]
}
```

---
*This spec is a living document until finalized.*
