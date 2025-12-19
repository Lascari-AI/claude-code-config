---
covers: The structural model — three zones, six layers, and separation of concerns.
concepts: [architecture, zones, layers, foundation, codebase, appendix, L1-L6]
---

# Architecture

The structural model that makes this framework work. Three zones organize documentation by semantic purpose; six layers provide progressive depth from overview to implementation.

---

## The Three Zones

The framework organizes `docs/` into three top-level zones by semantic purpose:

```
docs/
├── 00-foundation/     # Intent layer (why, principles, boundaries)
├── 10-codebase/       # Structure layer (mirrors code, L1-L6)
└── 99-appendix/       # Operational layer (setup, tooling)
```

### Foundation (`00-foundation/`)
**Why we build, how we decide.**

Contains purpose, principles, and boundaries that guide all decisions. This is the philosophical grounding—rarely changes, but informs everything.

- Purpose: What problem does this project solve?
- Principles: What trade-offs do we make and why?
- Boundaries: What will we NOT do?

### Codebase (`10-codebase/`)
**What we built, how it works.**

Mirrors the source code structure. Contains L1-L6 documentation that progressively reveals system understanding from overview to implementation.

Changes often as the code evolves.

### Appendix (`99-appendix/`)
**How to operate and contribute.**

Setup guides, tooling configuration, contribution guidelines. Operational concerns that don't fit in Foundation or Codebase.

Changes occasionally.

---

## The Six-Layer Hierarchy

Within the **Codebase** zone, documentation follows a six-layer depth hierarchy:

| Layer | Location | Purpose | Changes |
|-------|----------|---------|---------|
| **L1** | `10-codebase/00-overview.md` | Navigation hub and section index | Rarely |
| **L2** | Section `00-overview.md` files | Domain overviews with file trees | Sometimes |
| **L3** | Individual concept files | One idea per file (with code refs) | Often |
| **L4** | Top of source files | File contracts (header comments) | With code |
| **L5** | Function docstrings | Function contracts | With code |
| **L6** | Implementation | The code itself | Constantly |

### Layer Purposes

**L1-L3: The "Why" of Architecture**
- Lives in `docs/10-codebase/`
- Explains reasoning, mental models, design decisions
- Human-maintained, AI-consumed

**L4-L5: The "What" of Contracts**
- Lives in source code files
- Declares responsibilities and promises
- Boundary between documentation and implementation

**L6: The "How" of Implementation**
- The actual code
- Details that L4-L5 abstract away

---

## Separation of Concerns

| Zone/Layer | Answers | Example |
|------------|---------|---------|
| Foundation | "Why does this project exist?" | "We build X to solve Y for Z" |
| L1-L3 (Codebase docs) | "Why is it architected this way?" | "We use event sourcing because..." |
| L4 (File headers) | "What does this file do?" | "Handles user session lifecycle" |
| L5 (Docstrings) | "What does this function promise?" | "Returns validated token or throws" |
| L6 (Code) | "How does it work?" | The implementation |

**Key insight:** Each layer answers a different question. An agent working on authentication needs:
- L1-L3 for architectural context (don't duplicate the auth service)
- L4-L5 for contracts (what functions exist, what they promise)
- L6 for implementation details (the actual change)

---

## Navigation Pattern

```
Foundation (prime context)
    ↓
L1 (find relevant section)
    ↓
L2 (understand domain)
    ↓
L3 (find specific concept)
    ↓
L4 (identify target file)
    ↓
L5 (identify target function)
    ↓
L6 (make the change)
```

This mirrors how senior engineers naturally explore codebases—progressive depth based on need.
