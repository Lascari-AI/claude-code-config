# Agent Architecture: Overview

System-level view of the LAI Claude Code Config agent architecture.

---

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAI CLAUDE CODE CONFIG                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐    │
│   │  ONBOARDING │ ───▶ │   DOCBASE   │ ───▶ │   SESSION WORKFLOW      │    │
│   │             │      │   SETUP     │      │   (spec/plan/build/docs)│    │
│   └─────────────┘      └─────────────┘      └─────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Session Lifecycle

```
                            USER REQUEST
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              SESSION                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐             │  │
│  │   │  SPEC  │───▶│  PLAN  │───▶│ BUILD  │───▶│  DOCS  │             │  │
│  │   │        │    │        │    │        │    │        │             │  │
│  │   │ Define │    │ Design │    │Execute │    │ Update │             │  │
│  │   │ intent │    │  how   │    │  impl  │    │docbase │             │  │
│  │   └────────┘    └────────┘    └────────┘    └────────┘             │  │
│  │       │              │             │             │                  │  │
│  │       ▼              ▼             ▼             ▼                  │  │
│  │   spec.md       plan.md      code changes   doc updates            │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Session artifacts stored in: agents/sessions/{session-id}/                │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mental Model: The Bridge

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
│        │  v1   │ ═══════════════════════════════▶│  v2   │                 │
│        │       │          THE PLAN                │       │                 │
│        └───────┘         (the bridge)             └───────┘                 │
│                                                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Checkpoint 1       │                                  │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 2       │                                  │
│                    ├─────────────────────┤                                  │
│                    │  Checkpoint 3       │                                  │
│                    └─────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**SPEC** defines the destination (WHAT). **PLAN** builds the bridge (HOW). **BUILD** walks the bridge.

---

## Agent Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT TAXONOMY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     ORCHESTRATOR (Main Claude)                       │   │
│  │  - Interprets user intent                                           │   │
│  │  - Routes to appropriate workflow/agent                             │   │
│  │  - Maintains session state                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐              │
│           ▼                        ▼                        ▼              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   DOCS AGENTS   │    │ SESSION AGENTS  │    │ UTILITY AGENTS  │        │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤        │
│  │ - interview     │    │ - spec          │    │ - explore       │        │
│  │ - write         │    │ - plan          │    │ - research      │        │
│  │ - annotate      │    │ - build         │    │ - git/commit    │        │
│  │ - audit         │    │ - quick-plan    │    │                 │        │
│  │ - scaffold      │    │                 │    │                 │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Session Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SESSION COMPLEXITY LEVELS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FULL SESSION (Features, Major Changes)                                     │
│  ┌────────┐ → ┌────────┐ → ┌────────┐ → ┌────────┐                        │
│  │  SPEC  │   │  PLAN  │   │ BUILD  │   │  DOCS  │                        │
│  └────────┘   └────────┘   └────────┘   └────────┘                        │
│  User confirms at each stage                                               │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  QUICK SESSION (Chores, Bug Fixes)                                         │
│  ┌─────────────┐ → ┌────────┐ → ┌────────┐                                │
│  │ QUICK-PLAN  │   │ BUILD  │   │  DOCS  │                                │
│  └─────────────┘   └────────┘   └────────┘                                │
│  Auto-generated plan, user confirms once                                   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  RESEARCH SESSION (Investigation, No Code)                                  │
│  ┌──────────┐ → ┌──────────┐                                              │
│  │ RESEARCH │   │  REPORT  │                                              │
│  └──────────┘   └──────────┘                                              │
│  No code changes, findings documented                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow & Artifacts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARTIFACT FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ┌─────────────┐                                      │
│                        │   DOCBASE   │◀──────────────────────┐             │
│                        │   docs/     │                       │             │
│                        └──────┬──────┘                       │             │
│                               │ (context)                    │ (updates)   │
│                               ▼                              │             │
│  ┌─────────┐  intent   ┌─────────────┐  design   ┌─────────────┐          │
│  │  User   │ ────────▶ │    SPEC     │ ────────▶ │    PLAN     │          │
│  │ Request │           │             │           │             │          │
│  └─────────┘           │ agents/     │           │ agents/     │          │
│                        │ sessions/   │           │ sessions/   │          │
│                        │ {id}/spec   │           │ {id}/plan   │          │
│                        └─────────────┘           └──────┬──────┘          │
│                                                         │                  │
│                                                         │ (execute)        │
│                                                         ▼                  │
│                                                  ┌─────────────┐          │
│                                                  │    BUILD    │          │
│                                                  │             │──────────┘
│                                                  │ Code changes│
│                                                  │ + doc update│
│                                                  └─────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

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

---

## Document Index

| Document | Description |
|----------|-------------|
| [10-onboarding.md](10-onboarding.md) | Project onboarding and docbase setup |
| [20-spec.md](20-spec.md) | SPEC phase: defining intent |
| [30-plan.md](30-plan.md) | PLAN phase: designing implementation |
| [40-build.md](40-build.md) | BUILD phase: executing checkpoints |
| [50-docs-update.md](50-docs-update.md) | DOCS phase: updating documentation |
| [60-research.md](60-research.md) | Research system |

---

## Open Questions

- [ ] What triggers each session type? User choice or auto-detection?
- [ ] How do agents communicate state? Shared files vs. context passing?
- [ ] What hooks enforce the workflow? (pre-commit, pre-build, etc.)
- [ ] How does the UI layer (future) change agent interactions?
- [ ] Parallel agent execution? Or strictly sequential?

---

*Draft - iterate as design solidifies*
