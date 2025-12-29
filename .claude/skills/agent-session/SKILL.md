---
name: agent-session
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
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   SPEC   │────▶│   PLAN   │────▶│  BUILD   │────▶│ COMPLETE │
│  (WHAT)  │     │  (HOW)   │     │  (DO)    │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
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

## Phases

### Spec Phase
Define WHAT to build and WHY.
→ **Read**: [spec/OVERVIEW.md](spec/OVERVIEW.md)

### Plan Phase
Design HOW to implement with checkpoints and IDK tasks.
→ **Read**: [plan/OVERVIEW.md](plan/OVERVIEW.md)

### Build Phase
Execute the plan checkpoint by checkpoint. Two modes available:
- **Interactive** (`/session:build`) - Task-by-task with confirmation (default)
- **Autonomous** (`/session:build-background`) - Execute and report
→ **Read**: [build/OVERVIEW.md](build/OVERVIEW.md)

## Commands

| Command | Description |
|---------|-------------|
| `/session:spec [topic]` | Start new spec session |
| `/session:spec [session-id]` | Resume existing session |
| `/session:spec [session-id] finalize` | Finalize session spec |
| `/session:plan [session-id]` | Start/resume planning |
| `/session:plan [session-id] finalize` | Finalize the plan |
| `/session:build [session-id]` | Interactive build - task-by-task with confirmation |
| `/session:build-background [session-id]` | Autonomous build - execute checkpoint |

## Session Directory Structure

```
agents/sessions/{session-id}/
├── state.json       # Session state and progress
├── spec.md          # WHAT: Goals, requirements, context
├── plan.json        # HOW: Checkpoints and tasks (source of truth)
├── plan.md          # HOW: Human-readable (generated)
├── research/        # Research artifacts
└── context/         # Supporting materials
```

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
