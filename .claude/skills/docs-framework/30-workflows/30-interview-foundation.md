---
covers: Extract developer's vision, values, and boundaries through Socratic dialogue.
concepts: [interview, foundation, purpose, principles, boundaries, socratic]
---

# Docs Foundation Interview Workflow

Extract understanding that doesn't live in code: why the project exists, who it serves, guiding principles, and explicit boundaries. Socratic extraction that helps developers articulate things they may not have explicitly stated before.

---

## What This Is

The Foundation interview extracts understanding that doesn't live in code:

- Why the project exists at all
- Who it serves and who it doesn't
- The principles that guide decisions
- What the project explicitly won't become
- Trade-offs that have been consciously made

**This is Socratic extraction.** You're helping the developer articulate things they may not have explicitly stated before. Probe for clarity, push for specificity, crystallize vague ideas into concrete statements.

## How This Differs from Codebase Interviews

| Codebase Interview | Foundation Interview |
|--------------------|---------------------|
| Archaeological: read code, form questions | Generative: extract vision from developer |
| "I see X in the code..." | "You mentioned X, tell me more..." |
| Probes code/explanation mismatches | Probes vague statements for specificity |
| Feeds L2/L3 docs (Sections, Nodes) | Feeds Foundation docs (Purpose, Principles, Boundaries) |

## Your Role

You are a Socratic interviewer helping crystallize thought.

| Do | Don't |
|----|-------|
| Push for specificity on vague statements | Accept "we want to be good at everything" |
| Ask "what would you sacrifice for X?" | Let trade-offs stay implicit |
| Probe "who is this NOT for?" | Accept unbounded scope |
| Challenge: "how do you decide between..." | Assume principles are obvious |
| Synthesize: "So the core trade-off is..." | Put words in their mouth |
| Follow threads that reveal values | Stick to a rigid script |

## Before Starting

Read available context (if it exists):

- `README.md` — existing articulation of purpose
- `docs/00-foundation/` — existing Foundation docs to refine
- Project metadata (`package.json`, `pyproject.toml`, etc.)

This gives you something to react to, but expect most understanding to come from conversation.

## The Interview

No rigid phases, but ensure you cover all three Foundation areas: Purpose, Principles, Boundaries.

### 1. Initial Context

Read what exists, then open with your understanding:

```
I've looked at [what you read]. Here's my current understanding:

[Your interpretation of what this project is and why it exists]

Some things I'd like to understand better:
- [Question about purpose or scope]
- [Question about who this serves]
- [Something that seems unclear or implicit]

Let's start with: What problem are you really solving here?
```

### 2. Purpose Exploration

Extract the "why" at the deepest level:

**The Problem:**
> "What's the pain point that made you build this?"
> "Who experiences this problem most acutely?"
> "What were people doing before this existed?"

**Who We Serve:**
> "Who is the primary user? Paint me a picture of them."
> "Who is this explicitly NOT for?"
> "What constraints do your users have that shaped your approach?"

**Why This Approach:**
> "You could have solved this other ways. Why this approach?"
> "What did you give up by choosing this path?"
> "What alternatives did you consider and reject?"

**Success:**
> "If this project completely succeeds, what changes in the world?"
> "How would you know you've achieved your purpose?"

### 3. Principles Exploration

Extract the decision-making heuristics:

**Finding Principles:**
> "When you have two valid options, how do you decide?"
> "What would you sacrifice for speed? What would you never sacrifice?"
> "I noticed [pattern in decisions]. Is that a conscious principle?"

**Making Trade-offs Explicit:**
> "You mentioned valuing X. What do you trade away to get X?"
> "If you had to choose between [A] and [B], which wins? Why?"

**Testing Principles:**
> "Give me an example where this principle guided a real decision."
> "What would violating this principle look like in practice?"

Aim for 3-7 principles. Push for specificity:
- "Be user-friendly" → "Prioritize immediate usability over power-user features"
- "Keep it simple" → "Accept fewer features to maintain fast iteration"

### 4. Boundaries Exploration

Extract what the project explicitly won't do:

**Non-Goals:**
> "What might someone expect this to do that it deliberately doesn't?"
> "What feature requests would you refuse even if users begged?"
> "What is this NOT trying to be?"

**Accepted Constraints:**
> "What limitations have you consciously accepted?"
> "What trade-offs are baked into the design?"

**Out of Scope:**
> "What use cases are explicitly unsupported?"
> "What adjacent problems are you NOT solving?"

Push back on "we haven't gotten to that yet" — distinguish "not yet" from "not ever."

### 5. Coverage Check

Mentally track what you've covered:

- [ ] The core problem and who experiences it
- [ ] Primary users and their constraints
- [ ] Why this approach over alternatives
- [ ] What success looks like
- [ ] 3-7 decision-making principles
- [ ] Key trade-offs made
- [ ] What this is NOT
- [ ] Accepted constraints
- [ ] Out-of-scope features/use cases

If an area is thin, gently steer:
> "We've talked a lot about what you're building. I want to make sure we also capture what you've decided NOT to build..."

### 6. Synthesize Understanding

When you feel you have the full picture:

```
Let me summarize what I've learned about [project]:

**Purpose**: [Why it exists, who it serves]

**Core Principles**:
- [Principle 1]
- [Principle 2]
- [Principle 3]

**Key Boundaries**:
- This is NOT [what it's not]
- We accept [constraint] for [benefit]

Is there anything critical I'm missing or getting wrong?
```

Get confirmation before capturing.

### 7. Capture the Report

Save to `docs/.drafts/foundation.interview.md`:

```markdown
# Foundation Interview Report: [Project Name]

**Date**: [timestamp]

---

## Summary

[2-3 sentences: What this project is and its core purpose]

## Purpose Findings

### The Problem
[What problem does this solve? Who has this problem? Why does it matter?]

### Who We Serve
[Primary users. Their needs. Their constraints. Who this is NOT for.]

### Why This Approach
[Key trade-offs. Why built this way vs alternatives.]

### Success Looks Like
[Observable outcomes indicating success]

## Principles Findings

### Identified Principles

**[Principle Name]**
- Statement: [One-line principle]
- Rationale: [Why this matters]
- Example: [How it guided a real decision]

**[Another Principle]**
- Statement: [One-line principle]
- Rationale: [Why this matters]
- Example: [How it guided a real decision]

[Repeat for 3-7 principles]

### Key Trade-off Patterns
[What consistently gets prioritized over what]

## Boundaries Findings

### What This Is NOT
[Explicit non-goals]

### Accepted Constraints
[Limitations consciously accepted and why]

### Out of Scope
[Features/use cases deliberately excluded]

## Open Questions

[Things not fully resolved. Tensions to revisit. Ambiguities that remain.]

---

*Ready for drafting: /docs:draft foundation*
```

### 8. Close the Interview

```
Interview complete.

Saved to: docs/.drafts/foundation.interview.md

Key findings:
- Purpose: [Core purpose in one line]
- Principles: [Number] principles identified
- Boundaries: [Key boundary or non-goal]

Next: Run /docs:draft foundation to generate Foundation documentation.
```

## Guidance

**Push for specificity.** Vague principles ("be user-friendly") aren't useful. Keep probing until you have concrete, actionable statements.

**Distinguish "not yet" from "not ever."** Features not yet built are different from features deliberately excluded. Boundaries are about conscious decisions, not roadmap gaps.

**Look for tensions.** When principles seem to conflict, that's valuable. "We want to be fast AND thorough" — which wins when they conflict?

**Use their language.** The developer's terminology matters. Preserve it for the drafting phase.

**Run until complete.** You're done when you could explain to another developer why this project exists, how to make decisions aligned with its values, and what not to build.

**This is generative, not archaeological.** Unlike codebase interviews where you read code and ask about it, here you're helping the developer articulate things they may never have written down.

## Output

- Foundation interview report saved to `docs/.drafts/foundation.interview.md`
- Structured findings ready for `/docs:draft foundation`
