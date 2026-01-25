---
covers: Decision-making heuristics that apply across all code and documentation.
concepts: [principles, heuristics, trade-offs, opinionation, traceability]
---

# Principles

These principles guide every decision across the codebase. When two valid approaches exist, principles tell you which one to pick.

---

## Opinionation First, Flexibility Later

**Statement**: Enforce the prescribed flow until stable, then open up customization.

**Rationale**: Stability before flexibility — you can't customize what doesn't work yet. Early users must follow the session lifecycle strictly. Once the core workflow is proven, we can introduce escape hatches and customization points.

**In Practice**: New features follow the session workflow (spec → plan → build → docs) without shortcuts. We don't add "quick mode" or bypasses until the structured flow is battle-tested.

---

## Traceability Over Speed

**Statement**: Prioritize traceability and quality; speed follows model improvements.

**Rationale**: Trust is built on knowing what happened, not how fast it happened. Every action should be auditable. When AI models improve, speed comes for free — but traceability must be designed in from the start.

**In Practice**: We log decisions, capture intent in specs, and link implementations back to plans — even when it would be faster to "just do it." May be slower than unstructured AI coding, but fully auditable.

---

## Happy Path First

**Statement**: Optimize the structured session flow before handling edge cases.

**Rationale**: Everything packaged into a session — that's the unit of work. Get the main workflow working excellently before investing in edge cases, error recovery, or alternative flows.

**In Practice**: A session that works perfectly for 80% of cases ships before a session that handles 100% of cases poorly. Edge cases and escape hatches come later, after the core is solid.

---

## Key Trade-off Patterns

These principles create consistent trade-offs across the system:

| We Choose | Over | Because |
|-----------|------|---------|
| Discipline now | Freedom later | Stability enables eventual flexibility |
| Quality and traceability | Speed | Trust requires knowing what happened |
| Structured flows | Ad-hoc flexibility | Sessions are the unit of work |
| Institutional knowledge | Just-in-time prompting | Context prevents repeated mistakes |
