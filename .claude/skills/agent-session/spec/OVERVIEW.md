# Spec Phase

Define WHAT to build and WHY using a question-driven approach.

## Purpose

The spec phase captures requirements, goals, and context **before** implementation planning. It answers:
- What problem are we solving?
- What does success look like?
- What are we explicitly NOT building?

## Prerequisites

- New session created with `/session:spec [topic]`
- Or resuming existing session with `/session:spec [session-id]`

## Prior Spec References

When starting a new spec, you may link prior sessions for context:

- **Prompt**: After session creation, agent asks "Are there prior specs to reference?"
- **Storage**: Prior session ID stored in `state.json` as `prior_session` field
- **Context Loading**: If provided, agent reads prior spec.md to understand:
  - Related goals and decisions
  - Constraints that may carry over
  - Continuity with previous work

This enables building on prior work without duplicating context. The prior spec is read but not modified.

**Example state.json with prior reference:**
```json
{
  "prior_session": "2025-12-24_user-auth_k7m3x9",
  ...
}
```

## Workflow

```
1. User provides topic/context
     ↓
2. Create session, prompt for prior specs
     ↓
3. If prior spec: read for context
     ↓
4. Ask clarifying questions
     ↓
5. Draft spec sections iteratively
     ↓
6. User reviews and refines
     ↓
7. Finalize spec → Ready for plan phase
```

## Key Principles

1. **In-depth interviewing**: Ask thorough, non-obvious clarifying questions about literally anything to understand the problem
2. **Almost read-only**: Only write to session directory files
3. **WHAT not HOW**: Focus on outcomes, not implementation
4. **Persistent exploration**: Continue interviewing until the spec is truly complete
5. **Capture the why & user taste**: Don't just record requirements - capture reasoning, mental models, and preferences. Verbose input gets condensed, but nuance must survive.
6. **Atomic persistence**: After EVERY exchange, update spec.md AND state.json. Never batch updates. This prevents losing work.

## Spec Document Sections

| Section | Purpose |
|---------|---------|
| **Overview** | Brief understanding of the problem space |
| **Problem Statement** | What we're solving and why it matters |
| **Goals (High/Mid/Detailed)** | Hierarchical goals from north star to specifics |
| **Non-Goals** | Explicit exclusions to prevent scope creep |
| **Success Criteria** | Testable outcomes - how we know we're done |
| **Context & Background** | Prior art, existing systems, stakeholder input |
| **Key Decisions** | Important decisions with rationale and date |
| **Open Questions** | Questions needing answers (checkbox format) |
| **Diagrams** | Mermaid/ASCII visualizations |
| **Notes** | Working notes and considerations |

## Commands

| Command | Description |
|---------|-------------|
| `/session:spec [topic]` | Start new spec session |
| `/session:spec [session-id]` | Resume existing session |
| `/session:spec [session-id] finalize` | Finalize spec for planning |

## Outputs

- `spec.md` - Specification document
- `state.json` - Session state with fields including:
  - `prior_session` - ID of linked prior spec session (if any)
  - `current_phase`, `phases`, `open_questions`, `key_decisions`
- `research/` - Any research artifacts gathered

## Finalization Criteria

Before finalizing, ensure:
- [ ] Problem statement is clear
- [ ] High-level goals are defined
- [ ] Non-goals explicitly stated
- [ ] Success criteria are testable
- [ ] No critical open questions remain
- [ ] Key decisions are documented

## Templates

- [spec.md](templates/spec.md) - Specification template
- [state.json](templates/state.json) - Session state template
