---
covers: What this system explicitly will not do, and constraints we accept.
concepts: [boundaries, constraints, scope, non-goals]
---

# Boundaries

Explicit non-goals and accepted constraints. Knowing what we won't do is as important as knowing what we will.

---

## What This System Is NOT

- **NOT vibe coding** — No "throw ideas at AI and see what sticks." Every change follows a structured session workflow with captured intent.

- **NOT a replacement for engineering skill** — Assumes you already know good practices. The system amplifies competent developers; it doesn't teach fundamentals.

- **NOT for quick hacks** — Designed for complex systems that need maintenance over time. If you just need a one-off script, this is overkill.

- **NOT a black box** — Full traceability is the core value proposition. If you can't see what happened, we failed.

## Constraints We Accept

- **Every change goes through a session** — Various levels of complexity and control are available, but the session is the unit of work. No ad-hoc modifications outside the workflow.

- **Upfront documentation investment required** — The system works best when the docbase contains institutional knowledge. Initial setup effort pays off over time.

- **Opinionated flows enforced** — Until the system is stable, users follow the prescribed workflow. Flexibility comes after stability.

- **Single-developer focus** — Multi-user collaboration is not a priority in the current design. Optimized for one developer working with AI.

## Out of Scope

| Feature | Status | Rationale |
|---------|--------|-----------|
| Multi-user collaboration | Not a priority (for now) | Focus on single-dev + AI workflow first |
| Vibe coding workflows | Deliberately excluded (not ever) | Fundamentally contradicts our purpose |
| Users without engineering knowledge | Not the target audience | System amplifies skill, doesn't teach it |
| Quick hack mode | Not planned | Traceability requires structure |
