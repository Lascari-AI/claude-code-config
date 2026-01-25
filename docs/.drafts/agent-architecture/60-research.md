# Research System

On-demand research for understanding code and gathering context.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCH SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Research is triggered ON-DEMAND, not automatically.                        │
│                                                                             │
│  Two entry points:                                                          │
│  • /research [query] — Standalone, creates ephemeral session                │
│  • /session:research — Within existing session                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Entry Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESEARCH ENTRY POINTS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  /research [query]                                                    │ │
│  │  Standalone research - creates ephemeral session for traceability     │ │
│  │                                                                       │ │
│  │  Example:                                                             │ │
│  │  /research How does the authentication system work?                   │ │
│  │  /research How do I add a new API endpoint? --style=cookbook          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  /session:research [query] --session=X --phase=X --triggered-by=X     │ │
│  │  Research within existing session - stores in session's research/     │ │
│  │                                                                       │ │
│  │  Example:                                                             │ │
│  │  /session:research How does auth work? --session=2026-01-12_feature   │ │
│  │    --phase=spec --triggered-by="Need to understand before planning"   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Research Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  --mode=light (default)                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Single agent performs research directly:                                   │
│  1. Explore codebase (tree, glob, grep)                                     │
│  2. Read relevant files                                                     │
│  3. Document findings incrementally                                         │
│  4. Write report.md                                                         │
│                                                                             │
│  Best for: Quick questions during spec/plan phases                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  --mode=full                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Parallel subagents for comprehensive investigation:                        │
│                                                                             │
│           ┌─────────────────┐                                               │
│           │ Research        │                                               │
│           │ Orchestrator    │                                               │
│           └────────┬────────┘                                               │
│                    │ spawns parallel                                        │
│        ┌───────────┼───────────┐                                           │
│        ▼           ▼           ▼                                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                                 │
│  │ subagent  │ │ subagent  │ │ subagent  │  (research-subagent type)       │
│  │ 001       │ │ 002       │ │ 003       │                                 │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                                 │
│        │             │             │                                        │
│        └─────────────┼─────────────┘                                        │
│                      ▼                                                      │
│           ┌─────────────────┐                                               │
│           │ report-writer   │  (synthesizes findings)                       │
│           └────────┬────────┘                                               │
│                    ▼                                                        │
│               report.md                                                     │
│                                                                             │
│  Best for: Complex features needing comprehensive investigation             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Report Styles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPORT STYLES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Style is inferred from question phrasing OR specified with --style=X      │
│                                                                             │
│  ┌─────────────┬────────────────────────────────────────────────────────┐  │
│  │ cookbook    │ "How do I do X?"                                       │  │
│  │             │ → Step-by-step guidance with patterns to follow        │  │
│  │             │                                                        │  │
│  │             │ Triggers: "How do I...", "How would I...",             │  │
│  │             │           "Show me how to...", "What's the pattern..." │  │
│  ├─────────────┼────────────────────────────────────────────────────────┤  │
│  │ understanding│ "How does X work?" (DEFAULT)                          │  │
│  │             │ → Explain architecture and design                      │  │
│  │             │                                                        │  │
│  │             │ Triggers: "How does X work?", "Explain how...",        │  │
│  │             │           "What happens when...", "How is X structured?"│  │
│  ├─────────────┼────────────────────────────────────────────────────────┤  │
│  │ context     │ "What do I need to know for X?"                        │  │
│  │             │ → Information for planning/decision-making             │  │
│  │             │                                                        │  │
│  │             │ Triggers: "What do I need to know...",                 │  │
│  │             │           "What would be affected if...",              │  │
│  │             │           "Before I implement X..."                    │  │
│  └─────────────┴────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Research Flow

```
                         Research Request
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Parse Arguments    │
                    │  - query            │
                    │  - mode             │
                    │  - style            │
                    │  - session (if any) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Initialize         │
                    │  - Create session   │
                    │    (if standalone)  │
                    │  - Create research/ │
                    │    directory        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Explore Codebase   │
                    │  - Tree structure   │
                    │  - Glob for files   │
                    │  - Grep for terms   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  mode=light     │   │  mode=full      │
          │                 │   │                 │
          │  Single agent   │   │  Spawn parallel │
          │  researches     │   │  subagents      │
          │  directly       │   │                 │
          └────────┬────────┘   └────────┬────────┘
                   │                     │
                   │                     ▼
                   │            ┌─────────────────┐
                   │            │  Wait for all   │
                   │            │  subagents      │
                   │            └────────┬────────┘
                   │                     │
                   │                     ▼
                   │            ┌─────────────────┐
                   │            │  Spawn report   │
                   │            │  writer         │
                   │            └────────┬────────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Write report.md    │
                    │  using style        │
                    │  template           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Update session     │
                    │  state with         │
                    │  research artifact  │
                    └─────────────────────┘
```

---

## Artifacts

```
Standalone research (/research):
agents/sessions/{research-session-id}/
├── state.json                    # Ephemeral session state
├── spec.md                       # Auto-generated from question
└── research/
    └── {research-id}/
        ├── state.json            # Research metadata
        ├── report.md             # Final report
        └── subagents/            # (only if mode=full)
            ├── subagent_001.json
            ├── subagent_002.json
            └── subagent_003.json

Within-session research (/session:research):
agents/sessions/{parent-session-id}/
├── state.json                    # Parent session (updated with artifact ref)
├── spec.md
└── research/
    └── {research-id}/
        ├── state.json            # Includes: phase, triggered_by, mode
        ├── report.md             # Findings
        └── subagents/            # (only if mode=full)
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/research [query]` | Standalone research |
| `/session:research [query] --session=X --phase=X --triggered-by=X` | Research within session |

### Optional Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--mode` | `light`, `full` | `light` | Single agent vs parallel subagents |
| `--style` | `cookbook`, `understanding`, `context` | inferred | Report format |

---

*Draft - expand with subagent coordination details*
