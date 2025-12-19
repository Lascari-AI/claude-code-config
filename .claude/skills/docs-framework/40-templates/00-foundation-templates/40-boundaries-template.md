---
covers: Template for the Boundaries foundation document.
concepts: [boundaries, constraints, scope, non-goals]
---

# Boundaries Template

Template for `docs/00-foundation/30-boundaries.md`. Explicit non-goals and constraints that prevent scope creep.

---

## Template

```markdown
---
covers: What this system explicitly will not do, and constraints we accept.
concepts: [boundaries, constraints, scope]
---

# Boundaries

Explicit non-goals and accepted constraints. Knowing what we won't do is as important as knowing what we will.

---

## What This System Is NOT

[Explicit non-goals. What might someone expect this to do that it deliberately doesn't?]

- We are not a [X]
- We do not [Y]
- This is not intended for [Z use case]

## Constraints We Accept

[Trade-offs we've consciously made. What do we give up in exchange for what we gain?]

- We accept [limitation] in exchange for [benefit]
- We prioritize [A] over [B], meaning [consequence]

## Out of Scope

[Features or use cases we explicitly won't support, even if requested.]

- [Feature X] — [why it's out of scope]
- [Use case Y] — [why it's out of scope]
```

---

## Guidance

### What This System Is NOT
Prevent scope creep by being explicit. "We are not a team collaboration tool" immediately clarifies hundreds of potential feature requests.

### Constraints We Accept
Name the trade-offs you've made. "We accept eventual consistency in exchange for lower latency" helps future developers understand why certain patterns exist.

### Out of Scope
This is different from "not yet implemented." Out of scope means "we've considered this and decided against it." Include brief reasoning so the decision doesn't get relitigated.

### Why Boundaries Matter
Without explicit boundaries:
- Feature requests pile up for things the system was never meant to do
- Architecture drifts toward accommodating everything
- New developers don't know what to push back on
