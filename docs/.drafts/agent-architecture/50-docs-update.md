# DOCS Phase — Update Documentation

The DOCS phase updates documentation at the end of a session.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOCS PHASE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Runs at END of session (after all checkpoints complete), NOT per-checkpoint│
│                                                                             │
│  Key Principles:                                                            │
│  • Agent determines what needs updating (not prescriptive rules)            │
│  • NOT every session needs doc updates                                      │
│  • Rely on model intelligence to assess significance                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## When Docs Need Updating

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOCS UPDATE DECISION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TYPICALLY NEEDS DOCS:                                                      │
│  ✓ New features                                                            │
│  ✓ Behavioral changes                                                      │
│  ✓ Architectural refactors                                                 │
│  ✓ New concepts introduced                                                 │
│                                                                             │
│  USUALLY DOESN'T NEED DOCS:                                                │
│  ✗ Variable renames                                                        │
│  ✗ Simple bug fixes                                                        │
│  ✗ Dead code removal                                                       │
│  ✗ Chores/cleanup                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Documentation Flow

```
                        BUILD complete
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Analyze Changes   │
                   │                     │
                   │   - What files      │
                   │     changed?        │
                   │   - What concepts   │
                   │     were added?     │
                   │   - What behavior   │
                   │     changed?        │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Assess Significance│
                   │                     │
                   │   - Is this a new   │
                   │     feature?        │
                   │   - Does behavior   │
                   │     change?         │
                   │   - Are new concepts│
                   │     introduced?     │
                   └──────────┬──────────┘
                              │
                   ┌──────────┴──────────┐
                   ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  Updates needed │   │  No updates     │
          │                 │   │  needed         │
          └────────┬────────┘   └────────┬────────┘
                   │                     │
                   ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  Determine scope│   │  Record in      │
          │  (see below)    │   │  state.json:    │
          └────────┬────────┘   │  "no updates    │
                   │            │   needed"       │
                   ▼            └─────────────────┘
          Continue to updates
```

---

## Documentation Scope

```
                   ┌─────────────────────┐
                   │   Determine Scope   │
                   │                     │
                   │   - L3 node update? │
                   │   - L2 overview?    │
                   │   - New section?    │
                   │   - L4/L5 headers?  │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │  Update    │  │  Update    │  │  Add       │
       │  L3 Nodes  │  │  L2 Index  │  │  L4/L5     │
       │            │  │            │  │  to source │
       │  Concept   │  │  Section   │  │            │
       │  docs      │  │  overview  │  │  File hdrs │
       │            │  │  & links   │  │  & fn docs │
       └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
             │               │               │
             └───────────────┼───────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │   Validate Links    │
                   │                     │
                   │   - All refs valid? │
                   │   - Code paths ok?  │
                   │   - No broken links │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Session Complete  │
                   │                     │
                   │   - Archive session │
                   │   - Update index    │
                   │   - Ready for next  │
                   └─────────────────────┘
```

---

## Documentation Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION LAYERS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  L1 - Codebase Overview (docs/10-codebase/00-overview.md)                  │
│       Updated for: Major architectural changes                              │
│                                                                             │
│  L2 - Section Overview (docs/10-codebase/{section}/00-overview.md)         │
│       Updated for: New concepts in section, structural changes              │
│                                                                             │
│  L3 - Concept Docs (docs/10-codebase/{section}/*.md)                       │
│       Updated for: Feature changes, behavioral changes                      │
│                                                                             │
│  L4 - File Headers (in source code)                                        │
│       Updated for: Files with changed purpose                               │
│                                                                             │
│  L5 - Function Docstrings (in source code)                                 │
│       Updated for: New/changed functions with complex behavior              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Artifacts

```
agents/sessions/{session-id}/
└── state.json
    └── doc_updates: [
          { "file": "docs/...", "action": "updated", "reason": "..." },
          ...
        ]
        OR
        doc_updates: [{ "action": "none", "reason": "No significant changes" }]

docs/
└── [updated documentation files]

src/
└── [updated L4/L5 in source files]
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/session:docs-update [session-id]` | Update documentation at end of session |

---

*Draft - expand with specific update patterns and examples*
