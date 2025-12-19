---
covers: Templates for the Foundation zone — overview, purpose, principles, and boundaries.
type: overview
concepts: [templates, foundation, purpose, principles, boundaries]
---

# Foundation Templates

Templates for the Foundation zone. Fixed structure templates for the overview, purpose, principles, and boundaries documents that capture system intent.

---

## File Tree

```
00-foundation-templates/
├── 00-overview.md                      (this file)
├── 10-foundation-overview-template.md  Foundation zone entry point
├── 20-purpose-template.md              Why the system exists
├── 30-principles-template.md           Decision-making heuristics
└── 40-boundaries-template.md           What the system won't do
```

## Section Scope

The Foundation zone has a fixed structure. These templates provide the starting point for each required document:

- **Foundation Overview**: Entry point linking to the three Foundation documents
- **Purpose**: Why the system exists, who it serves, what success looks like
- **Principles**: Heuristics that guide all decisions across the codebase
- **Boundaries**: Explicit non-goals and constraints

## Child Nodes

### [10-foundation-overview-template.md](10-foundation-overview-template.md)
Template for `docs/00-foundation/00-overview.md`. Entry point for the Foundation zone with links to purpose, principles, and boundaries.

### [20-purpose-template.md](20-purpose-template.md)
Template for `docs/00-foundation/10-purpose.md`. Documents why the system exists, the problem it solves, and who benefits.

### [30-principles-template.md](30-principles-template.md)
Template for `docs/00-foundation/20-principles.md`. Decision-making heuristics that apply everywhere in the codebase.

### [40-boundaries-template.md](40-boundaries-template.md)
Template for `docs/00-foundation/30-boundaries.md`. Explicit non-goals, accepted constraints, and out-of-scope features.
