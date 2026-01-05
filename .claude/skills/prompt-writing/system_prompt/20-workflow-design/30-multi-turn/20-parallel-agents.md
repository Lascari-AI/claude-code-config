---
covers: Subagent spawning technique for parallel execution with coordinated synthesis
type: technique
concepts: [parallel-agents, orchestrator, subagent, coordination, synthesis, divide-and-conquer]
depends-on: [system_prompt/20-workflow-design/30-multi-turn/00-base.md]
---

# Parallel Agents Technique

A multi-turn technique where an orchestrator spawns multiple subagents, each with their own state, then synthesizes results.

Design principle: Divide-and-conquer with coordinated state. Each subagent works independently; orchestrator combines results.

---

## When to Use

Parallel agents apply when:

- **Divisible work**: Task splits into independent investigations
- **Parallelizable**: Subagents can run concurrently without blocking
- **State isolation**: Each subagent maintains own progress
- **Synthesis required**: Results must be combined into cohesive output

Examples: research systems, code analysis across multiple areas, parallel data processing, multi-file transformations.

**Key distinction**: Unlike iterative loops (user participates each round), parallel agents run autonomously and reunite for synthesis.

---

## The Orchestrator Pattern

Three-role architecture:

```
┌─────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                      │
│  - Parses request into queries                      │
│  - Spawns subagents (parallel)                      │
│  - Waits for completion                             │
│  - Spawns report writer                             │
└─────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│    SUBAGENT 1    │          │    SUBAGENT N    │
│  - Investigates  │   ...    │  - Investigates  │
│  - Writes state  │          │  - Writes state  │
└──────────────────┘          └──────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
              ┌──────────────────┐
              │  REPORT WRITER   │
              │  - Reads states  │
              │  - Reads code    │
              │  - Synthesizes   │
              └──────────────────┘
```

### Role Responsibilities

| Role | Responsibility | Output |
|------|----------------|--------|
| Orchestrator | Parse request, spawn agents, coordinate | Summary to user |
| Subagent | Focused investigation, incremental state updates | State file with findings |
| Report Writer | Read all states + code, synthesize | Final report file |

---

## Subagent State Files

Each subagent maintains a dedicated state file for progress and findings.

### State Schema

```json
{
  "id": "001",
  "title": "Query title",
  "objective": "What this subagent investigates",
  "search_hints": ["directories", "patterns", "keywords"],
  "status": "searching|analyzing|complete|failed",
  "started_at": "ISO_8601_timestamp",

  "examined": [
    {
      "file": "path/to/file.ts",
      "lines": "45-67, 120-145",
      "learned": [
        "Specific insight 1",
        "Specific insight 2"
      ]
    }
  ],

  "summary": "2-4 sentences synthesizing findings",
  "completed_at": "ISO_8601_timestamp"
}
```

### State Design Principles

1. **Incremental Updates**: Update after EACH file examined
2. **Reference Over Copy**: Store file paths + line numbers, not code
3. **Atomic Learnings**: Each "learned" item is a specific insight
4. **Resumable**: Partial findings preserved if subagent fails

---

## Coordination

Three coordination phases: spawn, wait, collect.

### Spawn Phase

```xml
<phase id="2" name="Spawn Subagents">
    <critical>
    Spawn ALL subagents in a SINGLE message with multiple parallel calls.
    Do NOT spawn sequentially—this wastes time.
    </critical>

    <action>For each query:
        - Spawn subagent with query details
        - Pass session path and subagent file name
    </action>
</phase>
```

**Critical**: Use a single message with multiple tool calls for true parallelism.

### Wait Phase

```xml
<phase id="3" name="Wait for Completion">
    <action>Monitor subagent state files for status changes</action>
    <action>Wait until all subagents reach "complete" or "failed"</action>
    <action>Note any failures for report</action>
</phase>
```

### Collect Phase

```xml
<phase id="4" name="Spawn Report Writer">
    <action>Spawn report-writer agent with:
        - Session path
        - List of completed subagent files
        - Original request
        - Output file path
    </action>
</phase>
```

---

## Synthesis

Report writer combines subagent findings into cohesive output.

### Synthesis Process

```xml
<workflow>
    <phase id="1" name="Load Findings">
        <action>Read ALL subagent state files</action>
        <action>Extract examined files and learned items</action>
        <action>Build list of code files to read</action>
    </phase>

    <phase id="2" name="Read Actual Code">
        <critical>This is what makes the report valuable</critical>
        <action>Read code files referenced by subagents</action>
        <action>Focus on line ranges specified</action>
        <action>Select most illustrative snippets</action>
    </phase>

    <phase id="3" name="Synthesize">
        <action>Identify themes across subagent findings</action>
        <action>Group related learnings</action>
        <action>Connect complementary insights</action>
        <action>Note contradictions or gaps</action>
    </phase>

    <phase id="4" name="Write Report">
        <action>Write report with real code snippets</action>
        <action>Follow template structure</action>
        <action>Ensure summary addresses original request</action>
    </phase>
</workflow>
```

### Synthesis Principles

| Principle | Description |
|-----------|-------------|
| Theme Identification | Find patterns across multiple subagents |
| Synthesis Over Concatenation | Don't just list findings—connect them |
| Code Is King | Include real snippets, not just descriptions |
| Standalone Summary | Summary should work without reading full report |

---

## Examples

### Research System Orchestrator

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>Parse research request into distinct queries</action>
        <action>Create session directory structure</action>
        <action>Write initial state with query list</action>
    </phase>

    <phase id="2" name="Spawn Research">
        <critical>
        Spawn ALL subagents in SINGLE message.
        </critical>
        <action>For each query, spawn research-subagent with:
            - Session path
            - Subagent file: subagent_{id}.json
            - Query: id, title, objective, search_hints
        </action>
    </phase>

    <phase id="3" name="Wait">
        <action>Poll subagent state files until all complete</action>
    </phase>

    <phase id="4" name="Report">
        <action>Spawn report-writer with completed subagent list</action>
        <action>Return: "Research complete. Report at: {path}"</action>
    </phase>
</workflow>
```

### Subagent Investigation Pattern

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>Create state file with status: "searching"</action>
    </phase>

    <phase id="2" name="Search">
        <action>Use Glob and Grep to find relevant files</action>
        <action>Update status: "analyzing"</action>
    </phase>

    <phase id="3" name="Investigate">
        <critical>Update state after EACH file examined</critical>
        <action>Read files, extract learnings</action>
        <action>Append to examined array immediately</action>
    </phase>

    <phase id="4" name="Complete">
        <action>Write summary synthesizing learnings</action>
        <action>Set status: "complete"</action>
        <action>Return: "Complete: {state_file_path}"</action>
    </phase>
</workflow>
```

---

## Error Handling

Handle subagent failures gracefully:

```xml
<error_handling>
    <scenario name="Subagent Fails">
        - Note failure in orchestrator state
        - Continue with successful subagents
        - Report writer documents gaps from failed subagents
    </scenario>

    <scenario name="Partial Results">
        - Subagent state file contains partial examined array
        - Report writer uses available findings
        - Report notes incomplete investigation
    </scenario>

    <scenario name="All Subagents Fail">
        - Report error to user
        - Include any partial findings
        - Suggest manual investigation
    </scenario>
</error_handling>
```

---

## Template Reference

For real implementations of this pattern:

→ Orchestrator: See `.claude/agents/research/research-orchestrator.md`
→ Subagent: See `.claude/agents/research/research-subagent.md`
→ Report Writer: See `.claude/agents/research/report-writer.md`

---

## Checklist

When designing parallel agent systems:

- [ ] Orchestrator spawns ALL subagents in single message
- [ ] Each subagent has dedicated state file
- [ ] State schema enables incremental updates
- [ ] Subagents record file paths + line numbers (reference over copy)
- [ ] Report writer reads actual code files
- [ ] Synthesis identifies themes across subagents
- [ ] Error handling covers partial failures
- [ ] Output protocol minimizes response size (paths only)
