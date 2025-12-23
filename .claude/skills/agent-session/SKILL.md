---
name: agent-session
description: Manage development sessions with spec/plan/build workflow. Use when starting new features, defining requirements, planning implementations, or tracking development cycles. Provides structured session management with state tracking.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# Agent Session Management

This skill provides structured session management for the development cycle:
**SPEC → PLAN → BUILD**

## Overview

An **Agent Session** is a workspace that tracks a complete development journey for a feature or project. Each session contains:
- **Specification** - What we're building and why
- **Plan** - How we'll implement it
- **Research** - Investigation and context
- **State tracking** - Progress through phases

## When to Use

Use this skill when:
- Starting a new feature or project that needs requirements clarification
- You want to separate "what" from "how" in your development process
- Tracking a multi-phase development effort
- Creating documentation that evolves with understanding

## Session Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   SPEC   │────▶│   PLAN   │────▶│  BUILD   │────▶│ COMPLETE │
│   MODE   │     │   MODE   │     │   MODE   │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │
     │ finalize       │ finalize       │ complete
     │                │                │
     ▼                ▼                ▼
  spec.md          plan.md          [code]
```

## Directory Structure

Sessions are stored in `agents/sessions/`:

```
agents/sessions/
├── active_session.json          # Currently active session pointer
└── {session-id}/                # Individual sessions
    ├── state.json               # Session state and metadata
    ├── spec.md                  # Specification document
    ├── plan.md                  # Implementation plan (created in plan phase)
    ├── research/                # Research artifacts
    └── context/                 # Supporting context
        ├── diagrams/
        └── notes/
```

## Session ID Format

```
{YYYY-MM-DD}_{topic-slug}_{6-char-random-id}
```

Example: `2025-12-23_user-export-feature_x7k9m2`

## Commands

| Command | Description |
|---------|-------------|
| `/session:spec [topic]` | Start new spec session |
| `/session:spec continue` | Continue active session |
| `/session:spec finalize` | Finalize current spec |
| `/session:spec list` | List all sessions |
| `/session:plan` | Start planning (requires finalized spec) |
| `/session:plan finalize` | Finalize the plan |

## Phases

### Spec Phase

**Purpose**: Define WHAT we're building

The spec phase is:
- **Question-driven** - Asks clarifying questions
- **Almost read-only** - Only writes to session directory
- **Focused on WHAT and WHY** - Not implementation details

Key sections in spec.md:
- Overview & Problem Statement
- High-Level Goals (north star)
- Mid-Level Goals (capabilities)
- Non-Goals (explicit exclusions)
- Success Criteria
- Key Decisions

### Plan Phase

**Purpose**: Design HOW to implement

The plan phase:
- Reads the finalized spec as foundation
- Analyzes existing codebase
- Makes architectural decisions
- Creates implementation steps

Key sections in plan.md:
- Codebase Analysis
- Architecture & Approach
- Implementation Steps (ordered, with files)
- Testing Strategy

### Build Phase

**Purpose**: Execute the plan

The build phase:
- Follows the plan step-by-step
- Tracks progress
- Updates state as steps complete

## State Schema

See [templates/state.json](templates/state.json) for the complete schema.

Key fields:
- `current_phase`: spec | plan | build | complete | abandoned
- `phases.{phase}.status`: draft | in_progress | finalized
- `goals.high_level`: Array of north star goals
- `goals.mid_level`: Array of capabilities
- `open_questions`: Questions needing answers
- `key_decisions`: Decisions with rationale

## Templates

Templates for session files are in this skill's `templates/` directory:
- [state.json](templates/state.json) - Session state schema
- [spec.md](templates/spec.md) - Specification template
- [plan.md](templates/plan.md) - Implementation plan template

## Granularity

Sessions support different granularity levels:
- **project** - Full project scope
- **feature** - Feature within a project
- **sub_feature** - Component of a feature

Child sessions can reference parent sessions via `parent_session` in state.json.

## Active Session Tracking

The `agents/sessions/active_session.json` file tracks the currently active session:

```json
{
  "session_id": "2025-12-23_user-export_x7k9m2",
  "path": "agents/sessions/2025-12-23_user-export_x7k9m2",
  "activated_at": "2025-12-23T10:30:00Z"
}
```

This allows commands to work without specifying session IDs.

## Best Practices

1. **Start with Spec** - Always clarify requirements before planning
2. **Finalize Before Advancing** - Complete each phase before moving on
3. **Track Decisions** - Document why, not just what
4. **Update Incrementally** - Don't wait to update documents
5. **Use Diagrams** - Visual aids clarify understanding
