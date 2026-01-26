---
covers: The structural model — progressive disclosure enabled by vertical slices, clear boundaries, and layered depth.
concepts: [architecture, progressive-disclosure, vertical-slices, boundaries, zones, layers, L1-L6, shared-understanding]
---

# Architecture

The philosophy establishes why documentation matters. Now the question becomes: how do we build it?

The challenge is twofold:

1. **Capture human intent** 
   - The thoughts, decisions, and understanding that exist in your head need to be externalized in a structured way.

2. **Enable agent self-navigation** 
   - Once captured, agents must be able to find what they need on their own, without you pointing them to the right files every time.

The result is a **shared communication bridge**.

Documentation structured this way isn't just *for* agents—it benefits both parties equally:
- For you: 
  - A way to expand your own knowledge, thinking, and understanding. 
  - The discipline of structuring thoughts clarifies them.
- For agents: 
  - Efficient navigation and comprehension. 
  - They can find context autonomously.
- Together: 
  - A shared medium where both parties speak the same language and understand the same structure.

You can provide intent, but the agent can also navigate, create, and update it. 

This creates a living system that grows with your project.

---

# The Core Principle: Progressive Disclosure

The central organizing principle is **progressive disclosure**
- The ability to navigate from high-level intent down to specific implementation, loading only what's needed for the task at hand.

Engineers build understanding progressively, not randomly:

1. What is this system? → L1 (the index)
2. What are the major parts? → L2 (domain overviews)
3. How does this concept work? → L3 (specific topics)
4. What does this file do? → L4 (file headers)
5. What does this function promise? → L5 (docstrings)
6. How is it implemented? → L6 (code)

This mirrors the repair manual model from the philosophy: 
- index → system chapter → subsystem → component → procedure → the actual bolts.

You don't read the entire engine chapter to replace a spark plug. 

You navigate to the right spot, get the context you need, and work. 

Agents do the same, loading only what's relevant to their current task.

---

# What Makes Progressive Disclosure Work

Progressive disclosure only works if the documentation structure supports it. 

Three properties enable this:

## Vertical Slices

Each domain owns its operation completely.

- Each major system handles its functionality end-to-end
- You can understand one system without understanding the internals of another
- Systems connect at well-defined interfaces, not tangled dependencies

The transmission and engine are connected (power flows from one to the other) but they are completely different domains. 

You can rebuild the transmission without understanding combustion dynamics. 
- You only need to know: "torque comes in here, gear ratio happens, power goes out there."

This is why you can skip sections. 

If you're working on Service A, you don't need to read Service B's detailed documentation—because Service A is self-contained.

## Clear Boundaries

When systems connect, document the interface, not the internals.

If the Auth system produces a token that the API system consumes:
- Auth documents: "I produce tokens with this shape"
- API documents: "I consume tokens with this shape"
- Neither documents the other's implementation

This contains the blast radius of change. 

When Auth's internals change, only Auth's docs update—as long as the interface stays stable.

Each documented section should answer:
- What does this system receive? (inputs, dependencies)
- What does this system produce? (outputs, side effects)
- Where are the boundaries? (what's inside vs outside)

## Overviews at Every Level

You always know what exists without reading the details.

- L1 tells you what domains exist in the system
- L2 tells you what concepts exist within a domain
- Each overview provides enough context to decide: "Is this relevant to my task?"

This enables the mechanic's workflow: 

"I'm working on the transmission. I can see the engine exists and generally what it does, but I don't need to read its docs. I just need to know what comes in on the input shaft."

---

# The Implementation

The principles above are implemented through a specific structure: three zones organized by semantic purpose, and six layers organized by depth of detail.

## The Three Zones

The framework organizes `docs/` into three top-level zones by semantic purpose:

```
docs/
├── 00-foundation/     # Intent layer (why, principles, boundaries)
├── 10-codebase/       # Structure layer (mirrors code, L1-L6)
└── 99-appendix/       # Operational layer (setup, tooling)
```

### Foundation (`00-foundation/`)
**Understanding before implementation.**

The thinking layer—captures how you understand the problem, the shape of the solution, and the direction you're heading. This is NOT a PRD or formal requirements doc. It's exploratory: the artifact of working through what you're building and why.

Structure is freeform. Only `00-overview.md` is required. Common patterns include:
- Problem/landscape/approach (what's broken, what exists, how we'll tackle it)
- Vision/constraints/direction (where we're going, what shapes the path)
- Context/ideas/decisions (background, explorations, choices made)

Rarely changes once established, but informs everything that follows.

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

### Each Layer Answers a Different Question

| Zone/Layer | Question | Example |
|------------|----------|---------|
| Foundation | "What are we building and why?" | "Here's the problem, our vision, and how we're approaching it" |
| L1-L3 | "Why is it architected this way?" | "We use event sourcing because..." |
| L4 | "What does this file do?" | "Handles user session lifecycle" |
| L5 | "What does this function promise?" | "Returns validated token or throws" |
| L6 | "How does it work?" | The implementation |

This separation means an agent working on authentication loads:
- L1-L3 for architectural context (don't duplicate the auth service)
- L4-L5 for contracts (what functions exist, what they promise)
- L6 only for implementation details (the actual change)

Each layer provides exactly what's needed at that depth—nothing more.

---

## The Navigation Pattern

Putting it all together, the path from intent to implementation:

```
Foundation (prime context — understand the why)
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

The structure enables autonomous navigation. 

Given a task, an agent can:
  1. Start at Foundation to understand project intent
  2. Use L1 to find which domain is relevant
  3. Use L2 to understand that domain's architecture
  4. Drill into L3-L6 only as deep as the task requires

No human guidance needed. 

The documentation structure itself provides the map.
