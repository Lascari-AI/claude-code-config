---
covers: High-level architecture, system structure, and navigation index for the codebase documentation.
type: overview
---

# LAI Claude Code Config: System Architecture (L1)

[1-2 sentences: "How to think about this system." Is it a modular monolith? Event-driven microservices? CLI with functional core? Give the agent the "shape" of the application.]

---

## System Metaphor / Mental Model
{1-2 paragraphs expanding on the opening. Help the reader build a mental model before diving into details.}

## High-Level Architecture

### The Big Picture
{Explain the primary data flow. e.g., "Requests enter via API Gateway -> Processed by Workflow Engine -> State persisted in Postgres."}

```mermaid
graph TD
    A[{Component A}] --> B[{Component B}]
    B --> C[{Component C}]
```

### Key Architectural Decisions
{Brief notes on major technical choices. For the "why" behind these decisions, see [Foundation/principles](../00-foundation/20-principles.md).}

- **{Decision 1}**: {e.g., "PostgreSQL for persistence"}
- **{Decision 2}**: {e.g., "Event sourcing for audit trail"}

## File Tree

```
docs/10-codebase/
├── 00-overview.md                 (this file)
├── {10-section-a}/                {Brief description}
├── {20-section-b}/                {Brief description}
└── ...
```

## Section Index

### [{10-section-a}/]({10-section-a}/00-overview.md)
**{Role Metaphor}.** {What this section contains and why it exists.}

## Cross-Cutting Concerns
{Briefly mention where to find things that touch everything}
- **{Concern 1}**: See [{path-to-doc}]({path-to-doc})

## Related
- [Foundation](../00-foundation/00-overview.md) - Purpose, principles, and boundaries
- [Appendix](../99-appendix/00-overview.md) - Setup guides and operational docs
