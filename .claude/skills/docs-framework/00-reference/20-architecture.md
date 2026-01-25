---
covers: The structural model — three zones, six layers, and separation of concerns.
concepts: [architecture, zones, layers, foundation, codebase, appendix, L1-L6, vertical-slices, boundaries, domain-driven-design, progressive-revelation]
---

# Architecture

The structural model that makes this framework work. Three zones organize documentation by semantic purpose; six layers provide progressive depth from overview to implementation.

---

## Vertical Slices and Clear Boundaries

Like Factorio factories, each system owns its operation completely.

Good codebases (and good documentation) follow a vertical slice architecture:

- Each major system handles its functionality end-to-end
- Boundaries are explicit
  - Clear inputs, clear outputs
- You can understand one system without understanding the internals of another
- Systems connect at well-defined interfaces

The transmission and engine are connected (power flows from one to the other) but they are completely different domains. You can rebuild the transmission without understanding combustion dynamics. You only need to know: "torque comes in here, gear ratio happens, power goes out there."

### What This Means for Documentation

Each L2 section should be self-contained enough to work within:

- What does this system receive?
  - Inputs, dependencies
- What does this system produce?
  - Outputs, side effects
- Where are the boundaries?
  - What's inside vs outside this domain

When sections connect, the connection points should be explicit. If the Auth system produces a token that the API system consumes, both sections should document that interface, not the other system's internals.

This enables the mechanic's workflow: "I'm working on the transmission. I don't need to read the engine docs. I just need to know what comes in on the input shaft."

This principle shapes everything below: zones have clear purposes, layers have clear responsibilities, and each section documents one bounded context.

---

## Domain-Driven Design

The domain is the heart of software.

Domain-Driven Design (DDD) provides the conceptual vocabulary for how we structure documentation:

- Ubiquitous Language
  - Documentation uses the same terms as domain experts
  - When code says `Order`, docs say `Order`, and stakeholders say `Order`
  - No translation layer
- Bounded Contexts
  - Each major section (L2) represents a distinct domain boundary
  - The transmission is a bounded context; the engine is another
  - Dependencies between contexts are explicit
- Domain at the Center
  - L3 concept docs capture domain logic and rules
  - Technical implementation details are secondary to domain understanding

Documentation becomes the shared model between humans and AI. When an agent reads your docs, it learns the domain language, understands the boundaries, and can reason about business rules—not just call functions.

---

## Progressive Revelation

Engineers build understanding progressively, not randomly:

1. What is this system? → L1 (the index)
2. What are the major parts? → L2 (system overviews)
3. How does this concept work? → L3 (specific topics)
4. What does this file do? → L4 (file headers)
5. What does this function promise? → L5 (docstrings)
6. How is it implemented? → L6 (code)

This mirrors the repair manual: index → system chapter → subsystem → component → procedure → the actual bolts.

Agents navigate from intent to implementation the way experienced engineers do—loading only what's needed for the task at hand. You don't read the entire engine chapter to replace a spark plug. You navigate to the right spot, get the context you need, and work.

### What This Means for Overviews

An overview's job is comprehension at that level, not navigation to the next level.

After reading an L2 overview (a "system" section), you should be able to:

- Explain how this system works to a colleague
- Understand how the major pieces connect
- Know what comes in, what goes out, and what this system is responsible for
- Decide whether this is the right section for your task

The table of contents is a side effect. The abstract is the goal.

How you achieve this varies:

- A service might need a request flow diagram
- A domain module might need state transitions
- A data layer might need an entity relationship overview

Templates provide examples. The principle is what matters: give working understanding of the whole before drilling into parts.

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
