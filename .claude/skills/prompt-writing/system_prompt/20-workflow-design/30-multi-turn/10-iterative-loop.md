---
covers: User-in-the-loop technique for multi-turn workflows with cyclical input
type: technique
concepts: [iterative-loop, state-machine, user-in-loop, interview, socratic, requirements]
depends-on: [system_prompt/20-workflow-design/30-multi-turn/00-base.md]
---

# Iterative Loop Technique

A multi-turn technique where the user provides input each cycle. The system runs autonomously between user inputs.

Design principle: Deterministic multi-stage interrogation loop. No pleasantries, no randomness, no hidden steps.

---

## When to Use

Iterative loops apply when:

- **User input each cycle**: System asks, user responds, repeat
- **Progressive refinement**: Each round builds on previous
- **Structured extraction**: Gathering information systematically
- **Validation required**: User confirms accuracy before proceeding

Examples: spec interviews, requirements gathering, Socratic dialogue, knowledge extraction.

**Key distinction**: Unlike autonomous multi-turn (system runs alone), iterative loops require user participation each round.

---

## State Machine Stages

Iterative loops follow a deterministic state machine:

```
┌──────┐
│ PREP │ → Inspect context, populate memory
└──┬───┘
   │
   ▼
┌──────┐
│  Q   │ ← Select gap, emit ONE question
└──┬───┘
   │ (await user reply)
   ▼
┌────────┐
│REFLECT │ → Parse reply, update memory
└──┬─────┘
   │
   ├─── (conditions met OR max rounds) ──→ END
   │
   └─── (else) ──→ Q (increment index)
```

### Stage Definitions

```xml
<stages>
    <stage name="PREP">
        Initial setup:
        - Inspect initial context
        - Populate `memory` with known facts
        - Set `question_index = 1`
        - Transition → Q
    </stage>

    <stage name="Q">
        Question emission:
        - Select highest-priority gap
        - Emit exactly ONE question
        - Await user reply
        - Transition → REFLECT
    </stage>

    <stage name="REFLECT">
        Process response:
        - Parse user reply
        - Update `memory`; prune `unresolved`
        - If done OR max rounds → END
        - Else increment → Q
    </stage>

    <stage name="END">
        Finalization:
        - Output FINAL_REPORT
        - No more questions
    </stage>
</stages>
```

### Loop State Variables

Track these across turns:

```xml
<loop_state_variables>
    - `stage`: PREP | Q | REFLECT | END
    - `question_index`: int
    - `memory`: obj (key facts extracted so far)
    - `unresolved`: list (open issues)
    - `max_rounds`: int (hard stop)
</loop_state_variables>
```

---

## Output Formats

Iterative loops require two output formats: per-turn and final.

### Per-Turn Output

Every message except END:

```json
{
  "question": "<string>",
  "loop_state": {
    "question_index": 3,
    "unresolved": ["deployment strategy", "auth method"]
  }
}
```

Or in natural language with structured internal tracking.

### Final Report

Once, at END stage:

```json
{
  "summary": "<concise synthesis>",
  "validated_facts": { ... },
  "open_items": [...]
}
```

### XML Definition

```xml
<output_formats>
    <turn_output>
        Every message except END:
        - Single focused question
        - Internal state tracking (hidden from user)
    </turn_output>

    <final_report>
        Once, at END stage:
        - Summary of all gathered information
        - Validated facts (confirmed by user)
        - Open items (unresolved questions)
    </final_report>
</output_formats>
```

---

## Memory Handling

Rules for what to retain across turns:

```xml
<memory_handling_rules>
    - Retain only facts CONFIRMED by user
    - Discard speculation or unconfirmed inferences
    - Never reveal raw loop_state to user
    - Update memory immediately after each reply
    - Prune contradictions when new info supersedes old
</memory_handling_rules>
```

### Memory Principles

| Do | Don't |
|----|-------|
| Store user-confirmed facts | Store your own inferences |
| Update immediately | Batch updates |
| Prune contradictions | Keep conflicting info |
| Track source (which question) | Assume accuracy |

---

## Max Rounds Failsafe

Prevent infinite loops with a hard limit:

```xml
<global_constraints>
    - Max rounds: 10 (configurable)
    - At max rounds, transition to END regardless of completion
    - Final report notes any unresolved items
</global_constraints>
```

### Graceful Termination

```xml
<termination_conditions>
    <condition name="Success">
        All success criteria met + user confirms accuracy
    </condition>
    <condition name="Max Rounds">
        Hit max_rounds limit, report incomplete status
    </condition>
    <condition name="User Exit">
        User explicitly requests to end
    </condition>
</termination_conditions>
```

---

## Examples

### Spec Interview Pattern

```xml
<stages>
    <stage name="PREP">
        - Read initial context from user
        - Identify what's already known
        - List required spec fields: goals, constraints, scope
    </stage>

    <stage name="Q">
        - Select highest-priority missing field
        - Ask ONE focused question
        - Example: "What is the primary goal of this feature?"
    </stage>

    <stage name="REFLECT">
        - Parse answer, extract key facts
        - Update spec draft
        - Check: all required fields populated?
    </stage>

    <stage name="END">
        - Present complete spec
        - Ask for final confirmation
        - Output spec document
    </stage>
</stages>
```

### Requirements Gathering Pattern

```xml
<success_criteria>
    - All user stories have acceptance criteria
    - Dependencies identified
    - Scope boundaries clear
    - User confirms completeness
</success_criteria>

<stages>
    <stage name="PREP">
        - List known requirements from initial input
        - Identify gaps in user stories
    </stage>

    <stage name="Q">
        - For each incomplete user story:
            - Ask for acceptance criteria
            - Ask for edge cases
        - For dependencies:
            - Ask what must exist first
    </stage>

    <stage name="REFLECT">
        - Update requirements document
        - Mark items as complete/incomplete
    </stage>

    <stage name="END">
        - Output complete requirements doc
        - List any items marked for future discussion
    </stage>
</stages>
```

---

## Template Reference

For the full canonical template with all sections:

→ See [20-multiturn/10-iterative-loop.md](../../20-multiturn/10-iterative-loop.md)

The template includes:
- Purpose and persona
- Domain scope
- Success criteria
- Complete interview protocol
- Memory handling rules
- Termination notice

---

## Checklist

When designing iterative loops:

- [ ] State machine stages defined with clear transitions
- [ ] Loop state variables specified
- [ ] Both per-turn AND final output formats defined
- [ ] Memory handling rules explicit (retain confirmed only)
- [ ] Max rounds failsafe included
- [ ] Success criteria are measurable
- [ ] Termination conditions cover all exit paths
- [ ] One-question-per-turn principle enforced
