# Agent Sessions

This directory contains session workspaces for the spec/plan/build development cycle.

> **Skill Reference**: See `.claude/skills/session/` for templates and documentation.

## Overview

Each session represents a complete development journey for a feature or project, containing:
- **Specification** (spec.md) - What we're building and why
- **Plan** (plan.md) - How we'll implement it
- **Research** - Investigation and context gathering
- **Build artifacts** - Progress tracking during implementation

## Directory Structure

```
agents/sessions/
├── active_session.json          # Currently active session pointer
└── {session-id}/                # Individual sessions
    ├── state.json               # Session state and metadata
    ├── spec.md                  # Specification document
    ├── plan.md                  # Implementation plan
    ├── research/                # Research artifacts
    └── context/                 # Supporting context
        ├── diagrams/
        └── notes/
```

Templates are stored in the skill directory: `.claude/skills/session/templates/`

## Session Lifecycle

```
SPEC → PLAN → BUILD → COMPLETE
```

### 1. Spec Phase (`/spec`)
- Define WHAT we're building
- Clarify goals, constraints, success criteria
- Question-driven exploration
- Output: Finalized spec.md

### 2. Plan Phase (`/plan`)
- Design HOW to implement
- Architecture decisions
- Step-by-step implementation plan
- Output: Finalized plan.md

### 3. Build Phase
- Execute the plan
- Track progress
- Output: Working implementation

## Commands

| Command | Description |
|---------|-------------|
| `/spec [topic]` | Start new spec session |
| `/spec continue` | Continue active session |
| `/spec finalize` | Finalize current spec |
| `/spec list` | List all sessions |
| `/plan` | Start planning (uses finalized spec) |

## Session ID Format

```
{YYYY-MM-DD}_{topic-slug}_{6-char-id}
```

Example: `2025-12-23_user-export-feature_x7k9m2`

## State Tracking

The `state.json` file tracks:
- Current phase and status
- Goals (high-level and mid-level)
- Open questions
- Key decisions with rationale
- Timestamps for all transitions

## Granularity

Sessions support different granularity levels:
- **project** - Full project scope
- **feature** - Feature within a project
- **sub_feature** - Component of a feature

Child sessions can reference parent sessions for context.
