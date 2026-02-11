# BUILD Phase — Execute Implementation

The BUILD phase executes the plan checkpoint by checkpoint.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD PHASE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: Finalized plan.md with checkpoints                                  │
│  Output: Code changes, committed and verified                               │
│                                                                             │
│  Each checkpoint is executed, verified, and confirmed before the next.      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Build Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD MODES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INTERACTIVE (/session:build)                                       │   │
│  │                                                                     │   │
│  │  User confirms each checkpoint before proceeding.                   │   │
│  │  Best for: Complex changes, learning, careful review                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BACKGROUND (/session:build-background)                             │   │
│  │                                                                     │   │
│  │  Autonomous execution, notify on completion.                        │   │
│  │  Best for: Trusted plans, routine changes                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FIX-MODE (/session:build-interactive)                              │   │
│  │                                                                     │   │
│  │  Pause on error, collaborate with user to resolve.                  │   │
│  │  Best for: When issues arise during build                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Checkpoint Execution Loop

```
                            plan.md
                               │
                               ▼
              ┌────────────────────────────────┐
              │      CHECKPOINT LOOP           │
              │                                │
              │   For each checkpoint:         │
              └────────────────┬───────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │ CP 1    │          │ CP 2    │          │ CP 3    │
    └────┬────┘          └────┬────┘          └────┬────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Execute Changes │  │ Execute Changes │  │ Execute Changes │
│                 │  │                 │  │                 │
│ - Write code    │  │ - Write code    │  │ - Write code    │
│ - Run tests     │  │ - Run tests     │  │ - Run tests     │
│ - Verify works  │  │ - Verify works  │  │ - Verify works  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ User Checkpoint │  │ User Checkpoint │  │ User Checkpoint │
│ (if interactive)│  │ (if interactive)│  │ (if interactive)│
│                 │  │                 │  │                 │
│ "CP1 complete,  │  │ "CP2 complete,  │  │ "CP3 complete,  │
│  continue?"     │  │  continue?"     │  │  continue?"     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
      ┌──┴──┐              ┌──┴──┐              ┌──┴──┐
      │ ✓   │ ────────────▶│ ✓   │ ────────────▶│ ✓   │
      └─────┘              └─────┘              └─────┘
                                                   │
                                                   ▼
                                    ┌─────────────────────┐
                                    │   All CPs complete  │
                                    │   → DOCS phase      │
                                    └─────────────────────┘
```

---

## Single Checkpoint Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHECKPOINT EXECUTION DETAIL                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Load Checkpoint    │                                  │
│                    │  from plan.json     │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  For each task:     │                                  │
│                    │  - Execute change   │                                  │
│                    │  - Mark complete    │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Run Verification   │                                  │
│                    │  - Tests pass?      │                                  │
│                    │  - Manual checks?   │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                    ┌──────────┴──────────┐                                  │
│                    ▼                     ▼                                  │
│              ┌──────────┐          ┌──────────┐                            │
│              │  PASS    │          │  FAIL    │                            │
│              └────┬─────┘          └────┬─────┘                            │
│                   │                     │                                   │
│                   ▼                     ▼                                   │
│         ┌─────────────────┐    ┌─────────────────┐                         │
│         │ Update state    │    │ Enter FIX mode  │                         │
│         │ Mark CP done    │    │ Collaborate to  │                         │
│         │ Next checkpoint │    │ resolve issue   │                         │
│         └─────────────────┘    └─────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fix Mode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FIX MODE                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Triggered when: Tests fail, verification fails, or user requests          │
│                                                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Issue Detected     │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Pause Execution    │                                  │
│                    │  Analyze Error      │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Present Options    │                                  │
│                    │  to User            │                                  │
│                    │                     │                                  │
│                    │  □ Fix and retry    │                                  │
│                    │  □ Skip this task   │                                  │
│                    │  □ Abort checkpoint │                                  │
│                    │  □ Abort session    │                                  │
│                    └──────────┬──────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Collaborate on Fix │                                  │
│                    │  - Debug together   │                                  │
│                    │  - Apply fix        │                                  │
│                    │  - Re-verify        │                                  │
│                    └─────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Artifacts Produced

```
agents/sessions/{session-id}/
├── state.json       # Updated with build progress
│                    # - checkpoints[].status
│                    # - checkpoints[].completed_at
│                    # - commits[]
└── build-log.md     # Execution record (optional)

Source code:
├── [modified files per checkpoint]
└── Git commits per checkpoint (or at end)
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/session:build [session-id]` | Interactive build - task by task |
| `/session:build-background [session-id]` | Autonomous build |
| `/session:build-interactive [session-id]` | Fix mode - resolve issues |

---

*Draft - expand with error handling and recovery flows*
