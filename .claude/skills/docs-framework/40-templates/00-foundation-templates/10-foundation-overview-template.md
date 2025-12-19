---
covers: Template for the Foundation zone overview file.
concepts: [foundation, overview, purpose, principles, boundaries]
---

# Foundation Overview Template

Template for `docs/00-foundation/00-overview.md`. This file links to the three core Foundation documents and explains how to use them.

---

## Template

```markdown
---
covers: Purpose, principles, and boundaries that guide all decisions in this system.
type: overview
---

# Foundation

The intent layer. Why we build, how we decide, and what we won't do. Read Foundation before diving into the Codebase to ensure changes align with the system's intent.

---

## Contents

### [10-purpose.md](10-purpose.md)
Why this system exists, the problem it solves, and who it serves.

### [20-principles.md](20-principles.md)
Decision-making heuristics that apply across all code and documentation.

### [30-boundaries.md](30-boundaries.md)
What this system explicitly will not do, and constraints we accept.

## How to Use Foundation

Read Foundation before diving into the Codebase. These documents prime your understanding of:
- **Why** the system exists (Purpose)
- **How** decisions should be made (Principles)
- **What** is out of scope (Boundaries)

This context ensures changes align with the system's intent, not just its current implementation.
```

---

## Notes

- Foundation has a fixed structure — don't add additional files here
- Keep Foundation documents concise — if you can't read them in 5 minutes, they're too long
- Changes to Foundation should be rare and deliberate
