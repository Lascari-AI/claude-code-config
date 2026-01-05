---
covers: Core workflow design principles that apply to ALL patterns
type: reference
concepts:
  - steps
  - phases
  - constraints
  - critical-tags
  - output-format
  - error-handling
  - principles
depends-on:
  - system_prompt/20-workflow-design/00-overview.md
---

# Workflow Design: Base Principles

This is the dense reference for workflow design theory. These principles apply regardless of whether you're building single-completion or multi-turn workflows.

---

## Steps vs Phases

The fundamental structural choice in workflow design.

### Steps (Single-Completion)

```xml
<steps>
    <step name="analyze">
        <description>What to do and how</description>
        <constraints>Rules for THIS step only</constraints>
    </step>
</steps>
```

**Characteristics:**
- Internal reasoning scaffold
- Model processes all steps in thinking window
- No external feedback between steps
- Output is result of processing entire sequence
- Your code controls execution

### Phases (Multi-Turn)

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>First action</action>
        <action>Second action</action>
    </phase>
    <phase id="2" name="Execute">
        <critical>Must-not-violate constraint</critical>
        <action>Main work</action>
    </phase>
</workflow>
```

**Characteristics:**
- External execution flow
- Each phase involves tool calls, state updates
- Feedback between phases (tool results, state reads)
- Incremental output across multiple completions
- Autonomous system controls execution

---

## Constraint Localization

Where you place constraints matters.

### Step-Specific Constraints

```xml
<step name="extract_entities">
    <description>Extract named entities from text</description>
    <constraints>
    - Only extract entities mentioned explicitly
    - Do not infer relationships not stated
    </constraints>
</step>
```

Use for rules that apply ONLY to one step. Keeps the step self-contained.

### Global Constraints

```xml
<global_constraints>
- Maintain professional tone throughout
- Never include PII in output
- Stay within token budget
</global_constraints>
```

Use for rules that apply EVERYWHERE. Avoids repetition across steps.

### Phase-Level Critical

```xml
<phase id="2" name="Execute">
    <critical>
    Spawn ALL tasks in a SINGLE message with multiple parallel calls.
    Do NOT spawn them sequentially.
    </critical>
    <action>For each query, spawn subagent</action>
</phase>
```

Use for must-not-violate constraints within a specific phase.

**Principle**: Localize constraints to smallest applicable scope. Global only when truly global.

---

## Output Format vs Output Protocol

These serve different purposes.

### Output Format (Single-Completion)

Defines the **structure** of the response.

```xml
<output_format>
{
  "classification": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "evidence": ["quote1", "quote2"]
}
</output_format>
```

Your code receives this structure directly.

### Output Protocol (Multi-Turn)

Defines **where and how** to write output, not just structure.

```xml
<output_protocol>
  <critical>
  Write findings incrementally to state file.
  After EACH file examined, update the findings array.
  </critical>

  <final_output>
  Summarize to user only after all phases complete.
  </final_output>
</output_protocol>
```

The system persists state between completions.

---

## Using `<critical>` Tags

Mark constraints that must not be violated.

```xml
<critical>
NEVER modify files outside the designated output directory.
</critical>
```

**When to use:**
- Safety constraints (file access, data handling)
- Execution order that must not change
- Parallel vs sequential requirements
- Mandatory state updates

**Characteristics:**
- Visually distinct in prompt
- Models prioritize these constraints
- Should be rare—overuse dilutes impact

---

## Error Handling Patterns

### Scenario-Based (Multi-Turn)

```xml
<error_handling>
    <scenario name="Empty Request">
        Ask user for required input with usage example.
    </scenario>
    <scenario name="File Not Found">
        - Log warning to state
        - Skip and continue with remaining files
        - Note in final summary
    </scenario>
    <scenario name="Subagent Failure">
        - Mark subagent as failed in state
        - Continue with successful subagents
        - Include partial results in report
    </scenario>
</error_handling>
```

### Inline Handling (Single-Completion)

```xml
<step name="validate_input">
    <description>
    Check input meets requirements.

    If invalid:
    - Return error structure with specific message
    - Do not proceed to subsequent steps
    </description>
</step>
```

---

## Principles Sections

Named principles guide behavior across the workflow.

```xml
<principles>
  <principle name="Incremental Updates">
      Update state file after EACH significant action.
      Never batch updates—immediate persistence.
  </principle>

  <principle name="Focused Investigation">
      Stay laser-focused on assigned objective.
      Note tangential findings but don't pursue.
  </principle>

  <principle name="Evidence Over Assertion">
      Support every claim with specific evidence.
      Quote relevant code or documentation.
  </principle>
</principles>
```

**When to use:**
- Behavioral guidance that spans multiple phases
- Quality standards for output
- Decision-making frameworks

---

## Important Rules / Notes

For top-level constraints that need visibility.

### Numbered Rules (Strong Emphasis)

```xml
<important_rules>
1. NEVER modify production data
2. ALWAYS validate input before processing
3. Include reasoning with every classification
</important_rules>
```

### Important Notes (General Reminders)

```xml
<important_notes>
- Token budget is constrained—be concise
- User expects YAML output format
- This runs in CI/CD context
</important_notes>
```

---

## General Design Guidelines

1. **Be specific, not generic** — "Analyze sentiment using VADER methodology" beats "Analyze sentiment"

2. **Inject expert methodology** — The description is where your domain expertise goes

3. **Actions, not intentions** — "Extract the date field" not "Try to find dates"

4. **One responsibility per step/phase** — If a step does two things, split it

5. **Explicit state transitions** — Make phase boundaries clear

6. **Fail gracefully** — Define behavior for edge cases

7. **Test the boundaries** — Your prompt should handle malformed input, empty data, and edge cases
