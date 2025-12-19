---
covers: Template for the Principles foundation document.
concepts: [principles, heuristics, trade-offs, decision-making]
---

# Principles Template

Template for `docs/00-foundation/20-principles.md`. Decision-making heuristics that apply across the entire system.

---

## Template

```markdown
---
covers: Decision-making heuristics that apply across all code and documentation.
concepts: [principles, heuristics, trade-offs]
---

# Principles

These principles guide every decision across the codebase. When two valid approaches exist, principles tell you which one to pick.

---

## [Principle Name]

**Statement**: [One-line principle]

**Rationale**: [Why this matters]

**In Practice**: [Concrete example of applying this principle]

---

## [Another Principle]

**Statement**: [One-line principle]

**Rationale**: [Why this matters]

**In Practice**: [Concrete example of applying this principle]
```

---

## Guidance

### How Many Principles?
Aim for 3-7 principles. Fewer than 3 likely means you haven't articulated your values. More than 7 suggests some should be demoted to domain-specific guidance in Codebase sections.

### Good Principles Are
- **Actionable**: They help you make decisions
- **Distinctive**: They rule out alternatives you might otherwise choose
- **Memorable**: You can recall them without looking them up

### Example Principles

**Speed over features**
- Statement: We prioritize fast user interactions over feature breadth
- Rationale: Our users are in flow state; any delay breaks their concentration
- In Practice: We'll ship a feature with fewer options if it means sub-second response

**Explicit over clever**
- Statement: We prefer verbose, obvious code over clever abstractions
- Rationale: Code is read far more often than written; clarity beats brevity
- In Practice: We'll duplicate 3 lines rather than create a premature abstraction
