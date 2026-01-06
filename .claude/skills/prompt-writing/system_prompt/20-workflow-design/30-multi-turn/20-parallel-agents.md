---
covers: Subagent spawning technique for parallel execution with coordinated synthesis
type: technique
concepts: [parallel-agents, orchestrator, subagent, state-isolation, incremental-updates, synthesis]
depends-on: [system_prompt/20-workflow-design/30-multi-turn/00-base.md]
---

# Parallel Agents Technique

A multi-turn technique where an orchestrator spawns multiple subagents, each with their own state file. Subagents work independently, updating state incrementally. Results are synthesized after all complete.

**Canonical implementation**: Research system — see `.claude/agents/research/`

---

## When to Use

Parallel agents apply when:

- **Divisible work**: Task splits into independent investigations
- **Parallelizable**: Subagents can run concurrently without blocking
- **State isolation**: Each subagent tracks its own progress
- **Synthesis required**: Results must be combined into cohesive output

Examples: codebase research, multi-file analysis, parallel data processing, distributed investigation.

**Key distinction**: Unlike iterative loops (user participates each round), parallel agents run autonomously and reunite for synthesis.

---

## The Core Pattern

Each subagent is a self-contained multi-turn workflow with its own state file:

```
Orchestrator spawns subagents (parallel)
            ↓
┌─────────────────────────────────────────┐
│  SUBAGENT 1         SUBAGENT 2         │
│  ┌──────────┐       ┌──────────┐       │
│  │ Action   │       │ Action   │       │
│  │ ↓        │       │ ↓        │       │
│  │ Update   │       │ Update   │       │
│  │ state    │       │ state    │       │
│  │ ↓        │       │ ↓        │       │
│  │ Action   │       │ Action   │       │
│  │ ↓        │       │ ↓        │       │
│  │ Update   │       │ Update   │       │
│  │ state    │       │ state    │       │
│  └──────────┘       └──────────┘       │
└─────────────────────────────────────────┘
            ↓
Report writer reads all state files + code
            ↓
        Final report
```

### Why State Files Per Subagent?

| Benefit | Description |
|---------|-------------|
| **Independence** | Each subagent's progress is isolated |
| **Observability** | Monitor each subagent's progress separately |
| **Failure isolation** | One failure doesn't affect siblings |
| **Resumability** | Failed subagent can be restarted alone |
| **Composability** | Different process can pick up and continue |

---

## Real Implementation: Research System

The research system is the canonical parallel agents implementation.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                      │
│  - Parses request into queries                      │
│  - Spawns subagents (parallel, single message)      │
│  - Waits for completion                             │
│  - Spawns report writer                             │
└─────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│  RESEARCH        │          │  RESEARCH        │
│  SUBAGENT 1      │   ...    │  SUBAGENT N      │
│                  │          │                  │
│  State file:     │          │  State file:     │
│  subagent_001    │          │  subagent_00N    │
└──────────────────┘          └──────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
              ┌──────────────────┐
              │  REPORT WRITER   │
              │                  │
              │  Reads all state │
              │  files + code    │
              │  → Final report  │
              └──────────────────┘
```

### Subagent State Schema

Each research subagent writes to `subagent_{id}.json`:

```json
{
  "id": "001",
  "title": "JWT Token Generation",
  "objective": "Understand how JWT tokens are created and signed",
  "search_hints": ["src/auth", "jwt", "sign", "token"],
  "status": "searching|analyzing|complete|failed",
  "started_at": "2025-12-24T10:00:00Z",

  "examined": [
    {
      "file": "src/auth/jwt.ts",
      "lines": "45-67, 120-145",
      "learned": [
        "JWT signed using RS256 algorithm",
        "Token expiry configurable via JWT_EXPIRY env var",
        "Payload includes user ID, roles, issued-at timestamp"
      ]
    },
    {
      "file": "src/auth/keys.ts",
      "lines": "10-30",
      "learned": [
        "RSA keys loaded from PEM files at startup",
        "Keys cached in memory after first load"
      ]
    }
  ],

  "summary": "JWT tokens are generated using RS256 signing with RSA keys...",
  "completed_at": "2025-12-24T10:15:00Z"
}
```

### Incremental State Updates

The subagent updates state after EACH file examined:

```xml
<phase id="3" name="Investigate">
    <action>
        - Read high-priority files
    </action>
    <action>
        - For EACH file examined, IMMEDIATELY update state file:
            - Append to examined array:
              {
                "file": "path/to/file.ts",
                "lines": "relevant line ranges",
                "learned": ["insight 1", "insight 2"]
              }
    </action>
    <action>
        - Stop when sufficient understanding achieved
    </action>
</phase>
```

**Why incremental?** If subagent fails mid-investigation:
- Partial findings preserved in `examined[]`
- Report writer uses available data
- Can resume from last examined file

---

## Spawning Pattern

### Critical: Single Message, Parallel Calls

```xml
<phase id="2" name="Spawn Subagents">
    <critical>
        - Spawn ALL subagents in a SINGLE message with multiple parallel calls
        - Do NOT spawn sequentially—this wastes time and prevents true parallelism
    </critical>

    <action>
        - For each query, spawn research-subagent with:
            - Session path
            - Subagent file: subagent_{id}.json
            - Query: id, title, objective, search_hints
    </action>
</phase>
```

### Directory Structure

```
research_sessions/{session_id}/
├── state.json              # Orchestrator state
├── subagents/
│   ├── subagent_001.json   # Subagent 1 state
│   ├── subagent_002.json   # Subagent 2 state
│   └── subagent_003.json   # Subagent 3 state
└── report.md               # Final synthesized report
```

---

## Synthesis Phase

After all subagents complete, a report writer synthesizes results:

### Report Writer Workflow

```xml
<workflow>
    <phase id="1" name="Load Findings">
        <action>
            - Read ALL subagent state files
        </action>
        <action>
            - Extract examined files and learned items
        </action>
        <action>
            - Build list of code files to read
        </action>
    </phase>

    <phase id="2" name="Read Actual Code">
        <critical>
            - This is what makes the report valuable
        </critical>
        <action>
            - Read code files referenced in examined arrays
        </action>
        <action>
            - Focus on line ranges specified
        </action>
        <action>
            - Select most illustrative snippets
        </action>
    </phase>

    <phase id="3" name="Synthesize">
        <action>
            - Identify themes across subagent findings
        </action>
        <action>
            - Group related learnings
        </action>
        <action>
            - Connect complementary insights
        </action>
        <action>
            - Note contradictions or gaps
        </action>
    </phase>

    <phase id="4" name="Write Report">
        <action>
            - Write comprehensive report with real code snippets
        </action>
        <action>
            - Follow template structure
        </action>
    </phase>
</workflow>
```

### Reference Over Copy

Subagents record file paths and line numbers, not code:

| In State File | Not In State File |
|---------------|-------------------|
| `"file": "src/auth/jwt.ts"` | Full source code |
| `"lines": "45-67"` | Copy of the code |
| `"learned": ["Uses RS256"]` | Implementation details |

The report writer reads the actual code when synthesizing. This keeps state files small and ensures the report has fresh, accurate code.

---

## Error Handling

### Partial Failures

```xml
<error_handling>
    <scenario name="One Subagent Fails">
        <recovery>
            - Note failure in orchestrator state
            - Continue with successful subagents
            - Report writer documents gap from failed subagent
        </recovery>
    </scenario>

    <scenario name="Subagent Partial Results">
        <recovery>
            - Subagent state file contains partial examined[]
            - Report writer uses available findings
            - Report notes incomplete investigation
        </recovery>
    </scenario>

    <scenario name="All Subagents Fail">
        <recovery>
            - Report error to user
            - Include any partial findings
            - Suggest manual investigation
        </recovery>
    </scenario>
</error_handling>
```

### Resumability

Because each subagent has its own state:

1. Check status of each subagent state file
2. Re-spawn only failed/incomplete subagents
3. Existing complete subagents don't re-run
4. Report writer waits for all to reach terminal state

---

## Subagent Design Principles

From the research subagent implementation:

```xml
<principles>
    <principle name="Incremental Updates">
        <guidance>
            - Update state file after EACH file is examined
            - If you fail mid-investigation, partial findings are preserved
        </guidance>
    </principle>

    <principle name="Focused Investigation">
        <guidance>
            - Stay laser-focused on your assigned objective
            - Resist scope creep - investigate only your specific query
            - Stop when you have sufficient evidence
        </guidance>
    </principle>

    <principle name="Reference Over Copy">
        <guidance>
            - Record file paths and line numbers, not full code snippets
            - The report-writer will read the actual code
            - Keep learned items concise
        </guidance>
    </principle>

    <principle name="State Isolation">
        <guidance>
            - Your state file is your contract with the orchestrator
            - Write everything there, not to response messages
        </guidance>
    </principle>
</principles>
```

---

## Template Reference

For implementing parallel agents:

**Orchestrator**: Manages spawning, waiting, report triggering
- Spawns all subagents in single parallel call
- Monitors state files for completion
- Triggers report writer when all done

**Subagent**: `.claude/agents/research/research-subagent.md`
- Focused investigation with incremental state updates
- Status progression: searching → analyzing → complete
- examined[] grows after each file read

**Report Writer**: `.claude/agents/research/report-writer.md`
- Reads all state files
- Reads actual code files referenced
- Synthesizes into final report

---

## Checklist

When designing parallel agent systems:

- [ ] Orchestrator spawns ALL subagents in single message
- [ ] Each subagent has dedicated state file
- [ ] State updated after EACH action (incremental)
- [ ] Subagents use reference over copy (file paths, not code)
- [ ] Status field tracks: initializing → processing → complete/failed
- [ ] Report writer reads actual code files
- [ ] Synthesis identifies themes across subagents
- [ ] Error handling covers partial failures
- [ ] Output protocol minimizes response size (paths only)
