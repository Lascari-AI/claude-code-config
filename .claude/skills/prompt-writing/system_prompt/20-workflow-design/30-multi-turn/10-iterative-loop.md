---
covers: User-in-the-loop technique for multi-turn workflows with cyclical input
type: technique
concepts: [iterative-loop, state-machine, user-in-loop, interview, spec-mode, atomic-updates]
depends-on: [system_prompt/20-workflow-design/30-multi-turn/00-base.md]
---

# Iterative Loop Technique

A multi-turn technique where the user provides input each cycle. The system runs autonomously between user inputs, updating state after each exchange.

**Canonical implementation**: Spec mode (`/spec`) — see `.claude/commands/agent-session/spec.md`

---

## When to Use

Iterative loops apply when:

- **User input each cycle**: System asks, user responds, repeat
- **Progressive refinement**: Each round builds on previous
- **Structured extraction**: Gathering information systematically
- **Artifact construction**: Building a document incrementally

Examples: spec interviews, requirements gathering, knowledge extraction, guided configuration.

**Key distinction**: Unlike autonomous multi-turn (system runs alone), iterative loops require user participation each round.

---

## The State + Artifact Pattern

Iterative loops manage TWO files that update together:

1. **state.json** — Progress tracking, metadata, structured data
2. **{artifact}.md** — The document being built incrementally

```
User answers question
        ↓
┌───────────────────────────────┐
│  ATOMIC UPDATE (both files)   │
│                               │
│  1. Update {artifact}.md      │
│  2. Update state.json         │
│                               │
│  THEN ask next question       │
└───────────────────────────────┘
```

### Why Both Files?

| state.json | {artifact}.md |
|------------|---------------|
| Machine-readable progress | Human-readable output |
| Enables resume on restart | The deliverable being built |
| Tracks open_questions, decisions | Captures full context, nuance |
| Structured data for logic | Prose, diagrams, details |

---

## Real Implementation: Spec Mode

The spec mode is the canonical iterative loop. Here's how it works:

### State Tracking (state.json)

```json
{
  "session_id": "2025-12-24_auth-system_k7m3x9",
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:45:00Z",
  "topic": "auth-system",

  "current_phase": "spec",
  "phases": {
    "spec": {
      "status": "draft",
      "started_at": "2025-12-24T10:00:00Z",
      "finalized_at": null
    }
  },

  "goals": {
    "high_level": ["Secure user authentication"],
    "mid_level": ["JWT-based sessions", "OAuth integration"]
  },

  "open_questions": [
    "Token expiry policy?",
    "Refresh token strategy?"
  ],

  "key_decisions": [
    {
      "decision": "Use JWT over session cookies",
      "rationale": "Stateless, works with mobile clients",
      "made_at": "2025-12-24T10:30:00Z"
    }
  ]
}
```

### Artifact Building (spec.md)

The spec document grows with each exchange:

```markdown
# Auth System

> **Session**: `2025-12-24_auth-system_k7m3x9`
> **Status**: Draft

## Overview

User authentication system for the web and mobile applications...

## Goals

### High-Level Goals
- Secure user authentication that works across all platforms

### Mid-Level Goals
- JWT-based sessions for stateless auth
- OAuth integration for social login

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Use JWT over session cookies | Stateless, works with mobile | 2025-12-24 |

## Open Questions

- [ ] Token expiry policy?
- [ ] Refresh token strategy?
```

### The Atomic Update Cycle

From spec mode's workflow:

```xml
<after_each_answer>
    <critical>
        - Each answer triggers an ATOMIC save cycle - NEVER batch updates
    </critical>

    1. Acknowledge understanding (capture user's exact phrasing for nuance)
    2. Update spec.md IMMEDIATELY:
        - Add/update relevant section
        - Capture the WHY behind user's answer, not just the WHAT
    3. Update state.json IMMEDIATELY:
        - Sync open_questions (add new, remove answered)
        - Update key_decisions with rationale if decisions emerged
        - Update goals arrays if goals emerged
        - Set updated_at timestamp
    4. THEN ask next question OR summarize progress
</after_each_answer>
```

---

## State Machine Stages

Iterative loops follow a deterministic state machine:

```
┌──────┐
│ INIT │ → Create session, initialize files
└──┬───┘
   │
   ▼
┌──────┐
│  Q   │ ← Select gap, emit ONE question
└──┬───┘
   │ (await user reply)
   ▼
┌────────┐
│ UPDATE │ → Parse reply, update BOTH files
└──┬─────┘
   │
   ├─── (complete OR max rounds) ──→ FINALIZE
   │
   └─── (more questions) ──→ Q
```

### Stage Definitions

```xml
<stages>
    <stage name="INIT">
        <actions>
            - Create session directory
            - Initialize state.json with status: "draft"
            - Create {artifact}.md from template
            - Transition → Q
        </actions>
    </stage>

    <stage name="Q">
        <actions>
            - Select highest-priority gap
            - Emit exactly ONE focused question
            - Explain WHY you're asking
            - Await user reply
            - Transition → UPDATE
        </actions>
    </stage>

    <stage name="UPDATE">
        <critical>
            - Atomic update - both files, every time
        </critical>
        <actions>
            - Parse user reply
            - Update {artifact}.md with new content
            - Update state.json (questions, decisions, goals)
            - Set updated_at timestamp
            - If done → FINALIZE, else → Q
        </actions>
    </stage>

    <stage name="FINALIZE">
        <actions>
            - Confirm with user
            - Set status: "finalized"
            - Add finalization header to artifact
            - Report completion
        </actions>
    </stage>
</stages>
```

---

## Question Design

### One Question Per Turn

Ask ONE focused question. Multiple questions diffuse attention and complicate state updates.

```xml
<!-- Bad: Multiple questions at once -->
<question>
    What authentication method do you want? Also, what about token expiry?
    And should we support OAuth?
</question>

<!-- Good: ONE focused question with rationale -->
<question>
    What authentication method should we use—JWT tokens, session cookies,
    or something else? I'm asking because this affects our session management
    architecture.
</question>
```

### Explain the Why

Each question includes rationale:

```xml
<question_format>
    <template>
        - [Question]
        - I'm asking because [why this matters / how it affects the design]
    </template>
</question_format>
```

### Question Categories

From spec mode's question categories:

| Category | Example Questions |
|----------|-------------------|
| Problem Space | What problem are we solving? What's the current workaround? |
| Goals | What does success look like? What's the minimum viable version? |
| Constraints | What can't change? What dependencies exist? |
| Scope | What's explicitly NOT included? What's the priority order? |
| Deeper Exploration | What concerns you? What tradeoffs are acceptable? |

---

## Termination Conditions

```xml
<termination_conditions>
    <condition name="Success">
        <criteria>
            - All required sections complete
            - User confirms finalization
        </criteria>
    </condition>

    <condition name="Max Rounds">
        <criteria>
            - Hit max_rounds limit (e.g., 15)
            - Report incomplete status
        </criteria>
    </condition>

    <condition name="User Exit">
        <criteria>
            - User explicitly requests to end early
        </criteria>
    </condition>
</termination_conditions>
```

### Graceful Incomplete

If terminated early, state and artifact preserve all progress:
- State shows what was answered vs. still open
- Artifact contains all gathered information
- Can resume later by loading the session

---

## Template Reference

For implementing iterative loops, spec mode provides a reference implementation. These templates illustrate the pattern—your iterative loop may have different state fields and artifact structures based on your specific workflow.

**Spec Mode Implementation**: `.claude/commands/agent-session/spec.md`
- Complete workflow with all stages
- Question categories
- State schema
- Atomic update pattern

**Example State Template**: `.claude/skills/agent-session/spec/templates/state.json`
- Session metadata, phase tracking, goals/decisions/questions
- *Your workflow's state schema will differ based on what you're tracking*

**Example Artifact Template**: `.claude/skills/agent-session/spec/templates/spec.md`
- Document structure with section placeholders
- *Your artifact structure depends on what you're building (spec, config, report, etc.)*

**Key takeaway**: Study spec mode for the *pattern* (atomic updates, state + artifact, question-driven), then design state and artifact schemas appropriate to your workflow's domain.

---

## Checklist

When designing iterative loops:

- [ ] Both state.json AND artifact file defined
- [ ] Atomic update after EVERY exchange (never batch)
- [ ] One question per turn
- [ ] Questions include "why I'm asking"
- [ ] Termination conditions cover all exit paths
- [ ] State enables resume from any point
- [ ] Finalization requires user confirmation
