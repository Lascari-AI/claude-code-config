---
name: session
description: Manage development sessions with spec/plan/build workflow. Use when starting new features, defining requirements, planning implementations, or tracking development cycles. Provides structured session management with state tracking.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# Agent Session Management

Structured session management for the development cycle: **SPEC → PLAN → BUILD**

## Purpose

An **Agent Session** is a workspace that tracks a complete development journey:
- **Specification** - Define WHAT to build and WHY
- **Plan** - Design HOW to implement with checkpoints
- **Build** - Execute the plan with verification

## When to Use

- Starting a new feature or project that needs requirements clarification
- Separating "what" from "how" in your development process
- Tracking a multi-phase development effort
- Creating documentation that evolves with understanding

## Session Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   SPEC   │────▶│   PLAN   │────▶│  BUILD   │────▶│   DOCS   │────▶│ COMPLETE │
│  (WHAT)  │     │  (HOW)   │     │  (DO)    │     │ (UPDATE) │     │          │
└────┬─────┘     └──────────┘     └────┬─────┘     └────┬─────┘     └──────────┘
     │                                 │                │
     ▼ (optional)                      ▼ (when issue)   └── Agent determines if
┌──────────┐                      ┌──────────┐             docs need updating
│  DEBUG   │                      │   FIX    │             (not all sessions do)
│(sub-phase)│                     │(sub-phase)│
└──────────┘                      └──────────┘
     │                                 │
     └── Ephemeral investigation       └── Interactive fix mode
         (findings → debug/)               (build-interactive)
```

## Mental Model: The Bridge

The session lifecycle is designed around a simple but powerful concept:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CURRENT STATE                              DESIRED STATE                  │
│   ────────────                               ─────────────                  │
│   The codebase                               What the spec                  │
│   as it exists                               defines we're                  │
│   right now                                  building                       │
│                                                                             │
│        ┌───────┐                                  ┌───────┐                 │
│        │       │                                  │       │                 │
│        │  v1   │ ═════════════════════════════▶   │  v2   │                 │
│        │       │          THE PLAN                │       │                 │
│        └───────┘         (the bridge)             └───────┘                 │
│                                                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Checkpoint 1       │                                  │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 2       │                                  │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 3       │                                  │
│                    ├─────────────────────┤                                  │
│                    │  ...                │                                  │
│                    └─────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Structure?

**Spec Mode** defines the **destination** — WHAT we're building and WHY.
- Describes the desired end state without prescribing how to get there
- Focuses on outcomes, requirements, and success criteria
- Is **state-focused**: "what should exist when we're done"

**Plan Mode** builds the **bridge** — HOW we transform the codebase.
- Analyzes the gap between current state and desired state
- Creates a sequence of checkpoints that incrementally close the gap
- Is **transition-focused**: "what changes get us there"

**Build Mode** walks the **bridge** — executing checkpoints one by one.
- Each checkpoint is a **waypoint**: a verifiable intermediate state
- Verification after each checkpoint allows course correction
- Progress is tracked so sessions can be paused and resumed

### The Key Insight

By separating WHAT from HOW, we gain:
1. **Clarity** - Requirements are locked before implementation begins
2. **Flexibility** - The plan can adapt without changing the destination
3. **Verifiability** - Each checkpoint can be validated against the spec
4. **Resumability** - Clear waypoints mean you can stop and restart anywhere
5. **Fault Recovery** - Self-contained tasks enable picking up at any point without redoing work

### Tracer Bullet Planning

Checkpoints should be structured as **vertical slices** (end-to-end), not horizontal layers:

```
The Bridge: Tracer Bullet Style
────────────────────────────────

CURRENT STATE                              DESIRED STATE
     │                                          │
     │    ┌──────────────────────────────┐      │
     │    │  CP1: Thin end-to-end slice  │──────┤ ← Working!
     │    ├──────────────────────────────┤      │
     │    │  CP2: Add depth/features     │──────┤ ← Working!
     │    ├──────────────────────────────┤      │
     │    │  CP3: More complexity        │──────┤ ← Working!
     │    ├──────────────────────────────┤      │
     │    │  CP4: Polish & edge cases    │──────┘ ← Complete!
     │    └──────────────────────────────┘
     │
     └── Each checkpoint produces testable, working code
```

**Principle**: Checkpoint 1 should produce a minimal but complete end-to-end flow. Subsequent checkpoints add to that working foundation. This enables thorough testing and validation at every stage, catching integration issues early rather than at the end.

## Phases

### Spec Phase
Define WHAT to build and WHY.
→ **Read**: [spec/OVERVIEW.md](spec/OVERVIEW.md)

**Debug Sub-Phase** (optional): When investigating a bug during spec, enter the debug sub-phase:

```
SPEC ──▶ (need to understand bug) ──▶ DEBUG SUB-PHASE ──▶ SPEC (informed) ──▶ PLAN ──▶ BUILD
                                            │
                                            ├── Make ephemeral changes (logs, repro)
                                            ├── Investigate and understand
                                            ├── Capture findings in debug/ artifacts
                                            └── Changes are NOT committed (revert or discard)
```

Key principles:
- Debug changes are **ephemeral** - for understanding only, NOT committed
- Understanding goes into `debug/{issue-slug}.md` artifacts
- After debug completes, return to spec with new understanding
- Plan phase implements the proper fix based on debug findings
- Keeps plan/build clean and automatable - debug is exploratory, plan/build is deliberate

### Plan Phase
Design HOW to implement with checkpoints and IDK tasks.
→ **Read**: [plan/OVERVIEW.md](plan/OVERVIEW.md)

**Two Planning Modes**:

| Mode | Command | Use When |
|------|---------|----------|
| **Quick Plan** | `/session:quick-plan` | Chores, bug fixes, small changes (1-3 files) |
| **Full Plan** | `/session:plan` | Features, refactoring, complex work (multiple checkpoints) |

**Quick Plan**: Auto-generates complete plan (~1 checkpoint), user QAs result. Faster, less overhead.

**Full Plan**: Interactive tier-by-tier planning with user confirmation at each stage. More control, thorough.

**Mode Correlation**:
- Light research → Quick plan → Fast build
- Full research → Full plan → Careful build

**Escalation**: If quick plan generates something too complex, user can escalate to full plan for interactive refinement within the same session.

### Build Phase
Execute the plan checkpoint by checkpoint. Two modes available:
- **Interactive** (`/session:build`) - Task-by-task with confirmation (default)
- **Autonomous** (`/session:build-background`) - Execute and report
→ **Read**: [build/OVERVIEW.md](build/OVERVIEW.md)

### Docs Update Phase
Update documentation at the end of a session after build + tests pass.

**Key principles**:
- Runs at END of session (after all checkpoints complete), NOT per-checkpoint
- Agent determines what needs updating using docs-framework skill knowledge
- **NOT every session needs doc updates** - agent determines significance
- Rely on model intelligence, not prescriptive rules

**What gets updated** (agent decides):
- **L2/L3 (Codebase docs)** - For significant features, architectural changes
- **L4 (File headers)** - For files with changed purpose
- **L5 (Function docstrings)** - For new/changed functions with complex behavior

**Change types that typically need docs**:
- New features ✓
- Behavioral changes ✓
- Architectural refactors ✓

**Change types that usually don't**:
- Variable renames ✗
- Simple bug fixes ✗
- Dead code removal ✗
- Chores/cleanup ✗

**Outcome tracking**: Results recorded in `state.json.doc_updates` array (even if "no updates needed").

## Commands

| Command | Description |
|---------|-------------|
| `/session:spec [topic]` | Start new spec session |
| `/session:spec [session-id]` | Resume existing session |
| `/session:spec [session-id] finalize` | Finalize session spec |
| `/session:quick-plan [session-id]` | Auto-generate plan for simple tasks (QA at end) |
| `/session:plan [session-id]` | Interactive tier-by-tier planning |
| `/session:plan [session-id] finalize` | Finalize the plan |
| `/session:build [session-id]` | Interactive build - task-by-task with confirmation |
| `/session:build-background [session-id]` | Autonomous build - execute checkpoint |
| `/session:build-interactive [session-id]` | Interactive fix mode - work with user to resolve issues during build |
| `/session:docs-update [session-id]` | Update documentation at end of session |

## Session Directory Structure

```
agents/sessions/{session-id}/
├── state.json       # Session state, phase tracking, commits, artifacts
├── spec.md          # WHAT: Goals, requirements, decisions
├── plan.json        # HOW: Checkpoints and tasks (source of truth)
├── plan.md          # HOW: Human-readable (auto-generated from plan.json)
├── research/        # Research artifacts (organized by research session)
│   └── {research-id}/
│       ├── state.json   # Metadata: phase, triggered_by, mode
│       ├── report.md    # Synthesized findings
│       └── subagents/   # Raw subagent findings (if full research)
├── context/         # Supporting materials (flat - diagrams, notes, etc.)
└── debug/           # Debug session artifacts (if debugging occurred)
    └── {issue}.md   # Debug findings, reproduction steps, root cause
```

**Initialization**: Use `python .claude/skills/session/scripts/init-session.py --topic "Topic"` to create session directories. The script auto-generates the session ID and initializes state.json from template.

## Session ID Format

```
{YYYY-MM-DD}_{topic-slug}_{6-char-random-id}
```

Example: `2025-12-23_user-export-feature_x7k9m2`

## Granularity

Sessions support different granularity levels:
- **project** - Full project scope
- **feature** - Feature within a project
- **sub_feature** - Component of a feature

Child sessions can reference parent sessions via `parent_session` in state.json.

## Best Practices

1. **Start with Spec** - Always clarify requirements before planning
2. **Finalize Before Advancing** - Complete each phase before moving on
3. **Track Decisions** - Document why, not just what
4. **Update Incrementally** - Don't wait to update documents
5. **Use Diagrams** - Visual aids clarify understanding
