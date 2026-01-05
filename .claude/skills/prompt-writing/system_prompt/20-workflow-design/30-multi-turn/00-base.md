---
covers: External state workflow pattern for autonomous multi-turn execution
type: pattern
concepts: [multi-turn, phases, state-schema, output-protocol, autonomous, external-state]
depends-on: [system_prompt/20-workflow-design/10-base.md]
---

# Multi-Turn Workflows

Design workflows where an autonomous system executes multiple turns on its own—you submit instructions, the system runs.

---

## When to Use

Multi-turn workflows apply when:

- **Autonomous execution**: System decides what LLM calls to make
- **External state**: Progress persists across completions
- **Tool orchestration**: Workflow involves Read, Write, Task, Bash calls
- **Incremental output**: Results build up over multiple turns

Examples: research agents, report writers, code migration tools, background processing.

**Key insight**: You're directing an autonomous system, not orchestrating LLM calls yourself.

---

## The `<phases>` Structure

Phases define external execution flow—each phase involves tool calls and state updates.

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>Validate input</action>
        <action>Create output directory</action>
        <action>Write initial state file</action>
    </phase>

    <phase id="2" name="Execute">
        <critical>
            Spawn ALL tasks in a SINGLE message with parallel calls.
        </critical>
        <action>For each item, perform operation</action>
        <action>Update state after each completion</action>
    </phase>

    <phase id="3" name="Finalize">
        <action>Synthesize results</action>
        <action>Write final output</action>
        <action>Return summary to user</action>
    </phase>
</workflow>
```

### Phases vs Steps

| Aspect | Phases (Multi-Turn) | Steps (Single-Completion) |
|--------|---------------------|---------------------------|
| Execution | External—tool calls between | Internal—thinking window |
| State | Explicit JSON files | Implicit in reasoning |
| Feedback | Between phases (tool results) | None between steps |
| Output | Incremental across turns | Single response |

---

## State Schema Design

Multi-turn workflows require explicit state for progress tracking.

```xml
<state_schema>
{
  "id": "session_id",
  "status": "initializing|processing|complete|failed",
  "created_at": "ISO_8601_timestamp",
  "progress": {
    "total": 10,
    "completed": 3,
    "current": "item_004"
  },
  "results": []
}
</state_schema>
```

### State Design Principles

1. **Status field**: Always include for progress visibility
2. **Timestamps**: Track when phases started/completed
3. **Progress tracking**: Enable resume if interrupted
4. **Results accumulation**: Store incrementally, not just at end

---

## Output Protocol

Define where and how output is written—not just format.

```xml
<output_protocol>
    <critical>
    You MUST:
    1. Write findings to: {session}/findings.md
    2. Update state after EACH file processed
    3. Return ONLY: "Complete. Results at: {path}"

    Do NOT include full results in response message.
    </critical>
</output_protocol>
```

### Output Protocol Elements

| Element | Purpose |
|---------|---------|
| Target file | Where to write results |
| Update frequency | When to write (each item, each phase, at end) |
| Response format | What to return to user/orchestrator |
| Constraints | What NOT to include in response |

---

## Phase Anatomy

Each phase contains:

```xml
<phase id="2" name="Process Items">
    <!-- Critical constraints for this phase -->
    <critical>
        Update state after EACH item, not in batches.
    </critical>

    <!-- Sequential actions within the phase -->
    <action>Read next item from queue</action>
    <action>Process item</action>
    <action>Write result to output file</action>
    <action>Update state with completion</action>

    <!-- Optional: phase-specific notes -->
    <note>Skip items that have already been processed</note>
</phase>
```

### Phase Attributes

- **id**: Numeric identifier for ordering
- **name**: Human-readable phase name
- **actions**: Sequential steps within the phase
- **critical**: Must-not-violate constraints for this phase

---

## Using `<critical>` Tags

Mark constraints that must not be violated:

```xml
<critical>
Spawn ALL subagents in a SINGLE message.
Do NOT spawn sequentially—this wastes time.
</critical>

<critical>
Write to state file after EACH item processed.
Do NOT batch updates—enables resume on failure.
</critical>

<critical>
Response must be ONLY: "Complete. Report at: {path}"
Do NOT include report content in response.
</critical>
```

Place `<critical>` tags:
- Inside `<output_protocol>` for output constraints
- Inside `<phase>` for phase-specific constraints
- At top level for global constraints

---

## Examples

### Research Subagent Pattern

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>Read assigned objective from orchestrator</action>
        <action>Initialize state file with status: "researching"</action>
    </phase>

    <phase id="2" name="Investigate">
        <critical>Update state after EACH file examined</critical>
        <action>Search for relevant files</action>
        <action>Read and analyze each file</action>
        <action>Record learnings in state</action>
    </phase>

    <phase id="3" name="Complete">
        <action>Write summary of findings</action>
        <action>Set status to "complete"</action>
    </phase>
</workflow>
```

### Report Writer Pattern

```xml
<workflow>
    <phase id="1" name="Load Template">
        <action>Read template for specified style</action>
        <action>Understand required sections</action>
    </phase>

    <phase id="2" name="Read Findings">
        <action>Read all subagent state files</action>
        <action>Extract examined files and learnings</action>
    </phase>

    <phase id="3" name="Read Actual Code">
        <critical>This is what makes your report valuable</critical>
        <action>Read code files referenced by subagents</action>
        <action>Select most illustrative snippets</action>
    </phase>

    <phase id="4" name="Synthesize">
        <action>Identify themes across findings</action>
        <action>Group related learnings</action>
        <action>Organize by template structure</action>
    </phase>

    <phase id="5" name="Write Report">
        <action>Write report following template</action>
        <action>Include real code snippets</action>
    </phase>

    <phase id="6" name="Complete">
        <critical>Return ONLY: "Report written to: {path}"</critical>
    </phase>
</workflow>
```

---

## Template Reference

For the full canonical template with all sections:

→ See [20-multiturn/00-base.md](../../20-multiturn/00-base.md)

The template includes:
- YAML frontmatter structure
- Variables section
- Input/output format
- State schema
- Workflow with phases
- Principles
- Error handling

---

## Checklist

When designing multi-turn workflows:

- [ ] State schema enables progress tracking and resume
- [ ] Output protocol specifies where to write, not just format
- [ ] Phases represent external execution boundaries
- [ ] `<critical>` tags mark must-not-violate constraints
- [ ] Each phase has clear actions
- [ ] Error scenarios have recovery paths
- [ ] Response format is minimal (paths only, not full content)
