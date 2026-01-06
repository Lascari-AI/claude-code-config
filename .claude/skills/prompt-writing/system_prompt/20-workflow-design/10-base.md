---
covers: What workflows are, how they work, and reference for workflow tags
type: reference
concepts:
  - workflow
  - phases
  - steps
  - actions
  - ultrathink
  - parallel
  - critical
  - constraints
depends-on:
  - system_prompt/20-workflow-design/00-overview.md
---

# Workflow Design: Fundamentals

A workflow is structured XML that guides an agent through step-by-step execution. It's the core of any instruction artifact—the part that directs what the model actually does.

---

## What is a Workflow?

A workflow breaks down a task into discrete, ordered units of work. Each unit has:

- **Identity** — A name and/or ID for reference
- **Instructions** — What to do in this unit
- **Constraints** — Rules that apply to this unit (optional)

The XML structure makes boundaries explicit. The model knows exactly where each unit begins, ends, and what's expected.

```xml
<workflow>
    <!-- Units of work, ordered and named -->
</workflow>
```

**Why XML?** Clear boundaries. Hierarchical nesting. Attributes for metadata. The model parses structure, not just content.

---

## Structural Elements

### Phases

Top-level execution units. Use for multi-turn workflows where each phase involves external actions (tool calls, state updates, waiting).

```xml
<phase id="1" name="Initialize">
    <action>
        - Validate input parameters
    </action>
    <action>
        - Create session directory
    </action>
    <action>
        - Write initial state file
    </action>
</phase>

<phase id="2" name="Execute">
    <action>
        - Process each item in queue
    </action>
    <action>
        - Update state after each completion
    </action>
</phase>

<phase id="3" name="Finalize">
    <action>
        - Synthesize results
    </action>
    <action>
        - Write final output
    </action>
</phase>
```

| Attribute | Required | Purpose |
|-----------|----------|---------|
| `id` | Yes | Numeric ordering (1, 2, 3...) |
| `name` | Yes | Human-readable phase name |

### Steps

Internal reasoning units. Use for single-completion workflows where the model processes everything in its thinking window.

```xml
<steps>
    <step id="1" name="parse_input">
        <description>
            - Extract key entities and relationships from the input
        </description>
    </step>

    <step id="2" name="analyze">
        <description>
            - Apply domain rules to evaluate the extracted data
        </description>
        <constraints>
            - Only use explicitly stated facts
            - Flag assumptions clearly
        </constraints>
    </step>

    <step id="3" name="synthesize">
        <description>
            - Combine analysis into structured output
        </description>
    </step>
</steps>
```

| Attribute | Required | Purpose |
|-----------|----------|---------|
| `id` | Optional | Numeric ordering for reference |
| `name` | Yes | Action verb identifier (snake_case) |

### Actions

Discrete tasks within a phase. Each action is one thing to do.

```xml
<phase id="2" name="Research">
    <action>
        - Search for relevant files using Glob
    </action>
    <action>
        - Read each file and extract key patterns
    </action>
    <action>
        - Update state with findings
    </action>
</phase>
```

Actions are implicit children of phases—no special attributes needed.

---

## Execution Modifier Tags

Tags that change HOW a unit executes.

### `<ultrathink>`

Signals the model to spend extra reasoning cycles on this unit. Use for complex decomposition, multi-factor analysis, or critical decisions.

```xml
<step id="1" name="decompose_query">
    <ultrathink>
        - This is the most critical step - spend significant effort here
        - Break the query into orthogonal subqueries that cover all aspects
        - Consider: scope, specificity, searchability, independence
    </ultrathink>
    <description>
        - Decompose the research request into 3-5 focused subqueries
        - Each subquery should be independently investigable
    </description>
</step>
```

```xml
<phase id="1" name="Understand Request">
    <ultrathink>
        - Parse the user's intent carefully - what do they ACTUALLY need?
        - Consider unstated assumptions and implicit requirements
    </ultrathink>
    <action>
        - Analyze the request for explicit and implicit requirements
    </action>
    <action>
        - Identify ambiguities that need clarification
    </action>
</phase>
```

**When to use:**
- Query decomposition (research, analysis)
- Architectural decisions
- Ambiguity resolution
- Any step where shallow thinking leads to poor outcomes

### `<actions parallel="true">`

Signals that contained actions should execute concurrently, not sequentially.

```xml
<phase id="2" name="Spawn Subagents">
    <critical>
        - Execute these in a SINGLE message with multiple tool calls
    </critical>
    <actions parallel="true">
        <action>
            - Spawn subagent for query 1
        </action>
        <action>
            - Spawn subagent for query 2
        </action>
        <action>
            - Spawn subagent for query 3
        </action>
    </actions>
</phase>
```

```xml
<phase id="3" name="Gather Context">
    <actions parallel="true">
        <action>
            - Read configuration file
        </action>
        <action>
            - Read environment variables
        </action>
        <action>
            - Fetch remote schema
        </action>
    </actions>
    <action>
        - Merge all context sources  <!-- This runs after parallel actions -->
    </action>
</phase>
```

**When to use:**
- Spawning multiple subagents
- Reading multiple independent files
- Fetching data from multiple sources
- Any independent operations that don't depend on each other

### `<critical>`

Marks constraints that must not be violated. The model prioritizes these above other instructions.

```xml
<critical>
    - NEVER modify files outside the designated output directory
</critical>

<phase id="2" name="Execute">
    <critical>
        - Update state after EACH item processed
        - Do NOT batch updates—enables resume on failure
    </critical>
    <action>
        - Process items from queue
    </action>
</phase>
```

**When to use:**
- Safety constraints (file access, data handling)
- Execution order requirements
- Parallel vs sequential mandates
- Mandatory state updates

**Use sparingly**—overuse dilutes impact.

---

## Constraint Placement

Where you place constraints determines their scope.

### Step/Phase-Local

Rules that apply ONLY to one unit:

```xml
<step name="extract_entities">
    <description>
        - Extract named entities from text
    </description>
    <constraints>
        - Only extract entities mentioned explicitly
        - Do not infer relationships not stated
    </constraints>
</step>
```

### Global Constraints

Rules that apply EVERYWHERE in the workflow:

```xml
<global_constraints>
    - Maintain professional tone throughout
    - Never include PII in output
    - Stay within token budget
</global_constraints>
```

**Principle**: Localize to smallest applicable scope. Global only when truly global.

---

## Output Specification

### Output Format (Single-Completion)

Defines the **structure** of the response:

```xml
<output_format>
    {
      "classification": "positive|negative|neutral",
      "confidence": 0.0-1.0,
      "evidence": ["quote1", "quote2"]
    }
</output_format>
```

### Output Protocol (Multi-Turn)

Defines **where and how** to write output:

```xml
<output_protocol>
    <critical>
        - Write findings to: {session}/findings.md
        - Update state after EACH file processed
    </critical>
    <final_output>
        - Return ONLY: "Complete. Results at: {path}"
        - Do NOT include full results in response message
    </final_output>
</output_protocol>
```

---

## Quick Reference

| Tag | Purpose | Context |
|-----|---------|---------|
| `<workflow>` | Container for all execution units | Top-level |
| `<phase>` | External execution unit with tool calls | Multi-turn |
| `<step>` | Internal reasoning unit | Single-completion |
| `<action>` | Discrete task within a phase | Inside `<phase>` |
| `<ultrathink>` | Signal for deep reasoning | Inside any unit |
| `<actions parallel="true">` | Concurrent execution | Inside `<phase>` |
| `<critical>` | Must-not-violate constraint | Anywhere |
| `<constraints>` | Rules for a specific unit | Inside `<step>` |
| `<global_constraints>` | Rules for entire workflow | Top-level |
| `<output_format>` | Response structure | Single-completion |
| `<output_protocol>` | Where/how to write output | Multi-turn |

---

## Design Guidelines

1. **Be specific, not generic** — "Analyze sentiment using VADER methodology" beats "Analyze sentiment"

2. **Actions, not intentions** — "Extract the date field" not "Try to find dates"

3. **One responsibility per unit** — If a step does two things, split it

4. **Use `<ultrathink>` for critical decisions** — Don't let the model rush through important reasoning

5. **Parallelize when possible** — Independent operations should use `<actions parallel="true">`

6. **Localize constraints** — Put rules where they apply, not everywhere
