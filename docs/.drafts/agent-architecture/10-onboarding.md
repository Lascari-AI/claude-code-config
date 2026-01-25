# Onboarding Flow

How new projects get set up with the documentation system.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ONBOARDING FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Goal: Get from "new project" to "docbase ready" so sessions can begin     │
│                                                                             │
│  NEW PROJECT ──▶ INIT ──▶ FOUNDATION ──▶ SCAFFOLD ──▶ CODEBASE ──▶ READY   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow

```
                         NEW PROJECT / USER
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:init         │
                    │  Initialize docs/   │
                    │                     │
                    │  Creates:           │
                    │  - docs/ structure  │
                    │  - 00-foundation/   │
                    │  - 10-codebase/     │
                    │  - 99-appendix/     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:interview-   │
                    │  foundation         │
                    │                     │
                    │  Interactive        │
                    │  interview to       │
                    │  extract:           │
                    │  - Purpose          │
                    │  - Principles       │
                    │  - Boundaries       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:write        │
                    │  foundation         │
                    │                     │
                    │  Generate:          │
                    │  - 10-purpose.md    │
                    │  - 20-principles.md │
                    │  - 30-boundaries.md │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:scaffold     │
                    │                     │
                    │  Map source dirs    │
                    │  to doc sections:   │
                    │  - src/api/ → 10-api│
                    │  - src/ui/ → 20-ui  │
                    │  - etc.             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:interview-   │
                    │  codebase           │
                    │                     │
                    │  Per-section        │
                    │  knowledge extract: │
                    │  - What does this   │
                    │    section do?      │
                    │  - Key concepts?    │
                    │  - Important files? │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  /docs:write        │
                    │  [section]          │
                    │                     │
                    │  Generate L2/L3     │
                    │  documentation:     │
                    │  - Section overview │
                    │  - Concept docs     │
                    └──────────┬──────────┘
                               │
                               ▼
                      ┌───────────────┐
                      │  DOCBASE      │
                      │  READY        │
                      │               │
                      │  Can now run  │
                      │  sessions     │
                      └───────────────┘
```

---

## Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/docs:init` | Create docs/ directory structure | First time setup |
| `/docs:interview-foundation` | Extract purpose, principles, boundaries | After init |
| `/docs:write foundation` | Generate foundation docs from interview | After foundation interview |
| `/docs:scaffold` | Map source to doc sections | After foundation complete |
| `/docs:interview-codebase [section]` | Extract knowledge for a section | Per-section |
| `/docs:write [section]` | Generate L2/L3 docs for section | After section interview |

---

## Artifacts Created

```
docs/
├── 00-foundation/
│   ├── 00-overview.md      # Foundation overview
│   ├── 10-purpose.md       # Why this system exists
│   ├── 20-principles.md    # Decision-making heuristics
│   └── 30-boundaries.md    # What we won't do
│
├── 10-codebase/
│   ├── 00-overview.md      # Codebase architecture overview (L1)
│   ├── 10-{section}/       # Per-section documentation (L2)
│   │   ├── 00-overview.md  # Section overview
│   │   └── *.md            # Concept docs (L3)
│   └── ...
│
└── 99-appendix/
    └── 00-overview.md      # Setup guides, operational docs
```

---

## Notes

- Onboarding can be done incrementally (one section at a time)
- Foundation should be done first — it informs all other documentation
- The interview process is interactive — agent asks questions, user provides context
- Documentation quality depends on the quality of interview responses

---

*Draft - expand with more detail on each step*
