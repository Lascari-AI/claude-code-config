---
covers: Why documentation is the source of truth — the philosophy behind docs-first development.
concepts: [philosophy, lossy-projection, specs-as-source, progressive-revelation, docs-first]
---

# Why This Framework

**Code is a lossy projection of intent.** You can't reconstruct "why" from "how."

The real work isn't writing code — it's explaining the problem, deciding how to solve it, and capturing what you learn. 

Code is one expression of that understanding. It can be rewritten entirely. The decisions and reasoning are what persist.

This framework structures that understanding so both humans and AI agents can read it.

---

## The Problem

AI agents have intelligence. What they lack is context.

Every invocation starts fresh — no memory of your architecture, patterns, or decisions. Without documentation, agents reverse-engineer intent from code: slow, error-prone, misaligned.

The fix isn't smarter AI. It's shared understanding.

---

## The Insight

**Specs change slowly. Code changes fast.**

Your decisions — architecture, flows, trade-offs — evolve over months. Code changes constantly: refactors, rewrites, migrations. 

If specs are solid, you can rebuild correctly every time. 

**The specification contains more information than the code it produces.**

Physical engineering knows this. A mechanic in Tokyo rebuilds a Detroit engine using only the manual. Boeing documents every component and tolerance — "the plane is the documentation" would be absurd. The US Constitution is a versioned specification: amendments update it, judicial review checks compliance, precedents test edge cases.

Software abandoned this rigor. We're correcting it.

---

## Progressive Revelation

Engineers build understanding progressively, not randomly:

1. What is this system? → L1
2. What are the major parts? → L2
3. How does this domain work? → L3
4. What does this file do? → L4
5. What does this function promise? → L5
6. How is it implemented? → L6

This framework codifies that pattern. Agents navigate from intent to implementation the way experienced engineers do — loading only what's needed for the task at hand.

---

## Docs-First Development

An opinionated approach:

1. **Document decisions and intent** — the slow-changing source of truth
2. **Implement against that documentation** — code expresses the spec
3. **Keep them synchronized** — docs evolve with the system

As AI writes more code, the highest-leverage skill becomes expressing intent clearly. Documentation becomes the source; generated code becomes the artifact.

Structure beats brute force. Even with massive context windows, signal-to-noise matters — structured docs find exactly what's needed, fast.

---

## The Bottom Line

This framework encodes your mental model so agents can execute against it.

Not by making AI smarter, but by making your intelligence shareable.

---

## References

- [Advanced Context Engineering for Coding Agents](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents) — Dex Horthy
- [Specs are the New Code](https://www.youtube.com/watch?v=8rABwKRsec4) — Sean Grove, AI Engineer 2025
