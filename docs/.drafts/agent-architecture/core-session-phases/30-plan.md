# PLAN Phase — Design Implementation

The PLAN phase designs HOW to implement what the spec defines.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLAN PHASE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: Finalized spec.md                                                   │
│  Output: plan.md with checkpoints                                           │
│                                                                             │
│  The plan is THE BRIDGE from current state to desired state.                │
│  Each checkpoint is a verifiable waypoint.                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Planning Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLANNING MODES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FULL PLAN (/session:plan)                                          │   │
│  │                                                                     │   │
│  │  For: Features, refactoring, complex work                           │   │
│  │  Process: Interactive tier-by-tier planning with user confirmation  │   │
│  │  Checkpoints: Multiple, each verifiable                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUICK PLAN (/session:quick-plan)                                   │   │
│  │                                                                     │   │
│  │  For: Chores, bug fixes, small changes (1-3 files)                  │   │
│  │  Process: Auto-generated plan, user QAs result                      │   │
│  │  Checkpoints: Usually 1                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Mode Correlation:                                                          │
│  • Light research → Quick plan → Fast build                                │
│  • Full research → Full plan → Careful build                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Full Plan Flow

```
                            spec.md
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Analyze Spec      │
                    │                     │
                    │   - Extract goals   │
                    │   - Identify scope  │
                    │   - List constraints│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Research Codebase │
                    │                     │
                    │   - Find touch      │
                    │     points          │
                    │   - Understand      │
                    │     existing code   │
                    │   - Identify risks  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Design Approach   │
                    │                     │
                    │   - Architecture    │
                    │     decisions       │
                    │   - File changes    │
                    │   - Dependencies    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Create Checkpoints│
                    │                     │
                    │   Break into steps: │
                    │   □ Checkpoint 1    │
                    │   □ Checkpoint 2    │
                    │   □ Checkpoint 3    │
                    │   (each verifiable) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   User Approval     │
                    │                     │
                    │   "Does this plan   │
                    │    look right?"     │
                    └──────────┬──────────┘
                               │
                      ┌────────┴────────┐
                      ▼                 ▼
                ┌──────────┐      ┌──────────┐
                │ Approved │      │ Revise   │
                │          │      │          │──┐
                └────┬─────┘      └──────────┘  │
                     │                 ▲        │
                     │                 └────────┘
                     ▼
          ┌─────────────────────┐
          │   plan.md written   │
          │   → BUILD phase     │
          └─────────────────────┘
```

---

## Checkpoint Design: Tracer Bullet Style

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRACER BULLET CHECKPOINTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Checkpoints should be VERTICAL SLICES (end-to-end), not horizontal layers │
│                                                                             │
│  CURRENT STATE                              DESIRED STATE                   │
│       │                                          │                          │
│       │    ┌──────────────────────────────┐      │                          │
│       │    │  CP1: Thin end-to-end slice  │──────┤ ← Working!               │
│       │    ├──────────────────────────────┤      │                          │
│       │    │  CP2: Add depth/features     │──────┤ ← Working!               │
│       │    ├──────────────────────────────┤      │                          │
│       │    │  CP3: More complexity        │──────┤ ← Working!               │
│       │    ├──────────────────────────────┤      │                          │
│       │    │  CP4: Polish & edge cases    │──────┘ ← Complete!              │
│       │    └──────────────────────────────┘                                 │
│       │                                                                     │
│       └── Each checkpoint produces testable, working code                   │
│                                                                             │
│  Principle: CP1 should produce a minimal but complete end-to-end flow.      │
│  Subsequent checkpoints add to that working foundation.                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Checkpoint Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHECKPOINT ANATOMY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Each checkpoint contains:                                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Checkpoint 1: [Title]                                              │   │
│  │                                                                     │   │
│  │  Goal: What this checkpoint accomplishes                            │   │
│  │                                                                     │   │
│  │  Tasks:                                                             │   │
│  │  - [ ] Task 1                                                       │   │
│  │  - [ ] Task 2                                                       │   │
│  │  - [ ] Task 3                                                       │   │
│  │                                                                     │   │
│  │  Files to modify:                                                   │   │
│  │  - path/to/file1.ts                                                 │   │
│  │  - path/to/file2.ts                                                 │   │
│  │                                                                     │   │
│  │  Verification:                                                      │   │
│  │  - How to verify this checkpoint is complete                        │   │
│  │  - Test command: `npm test`                                         │   │
│  │  - Manual check: [description]                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## IDK Tasks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IDK TASKS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  When the planner encounters uncertainty, it creates an IDK task:           │
│                                                                             │
│  - [ ] IDK: Determine best approach for [X]                                │
│        Options considered: A, B, C                                         │
│        Needs: Research / User input / Experimentation                      │
│                                                                             │
│  IDK tasks are resolved BEFORE build begins:                                │
│  • Research: Spawn /research --session=X                                    │
│  • User input: Ask user to choose                                          │
│  • Experimentation: Spike in debug mode                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Artifacts Produced

```
agents/sessions/{session-id}/
├── plan.json        # Source of truth - structured checkpoint data
├── plan.md          # Human-readable (auto-generated from plan.json)
└── research/        # Any research triggered during planning
    └── {research-id}/
        └── report.md
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/session:plan [session-id]` | Interactive tier-by-tier planning |
| `/session:quick-plan [session-id]` | Auto-generate plan for simple tasks |
| `/session:plan [session-id] finalize` | Finalize the plan |

---

*Draft - expand with detailed tier-by-tier planning flow*
