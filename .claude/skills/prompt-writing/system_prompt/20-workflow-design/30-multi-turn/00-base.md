---
covers: External state workflow pattern for autonomous multi-turn execution
type: pattern
concepts: [multi-turn, phases, state-file, external-state, restartability, session-directory, autonomous]
depends-on: [system_prompt/20-workflow-design/10-base.md]
---

# Multi-Turn Workflows

Multi-turn workflows are defined by **external state management**. The agent writes to a state file after each action, enabling restartability, visibility, and recovery.

---

## The Core Concept

Unlike single-completion (all reasoning in one response), multi-turn agents persist their progress externally. This is the defining characteristic—everything else follows from it.

```
Single-Completion              Multi-Turn
─────────────────              ──────────
Input → Thinking → Output      Input → Action → Write State
                                        ↓
                               Action → Write State
                                        ↓
                               Action → Write State → Output
```

**What this enables:**

| Without State | With State |
|---------------|------------|
| Failure loses all work | Partial progress preserved |
| Can't see what happened | Full audit trail |
| Must complete in one run | Can pause and resume |
| No recovery path | Pick up exactly where left off |
| Black box execution | Observable progress |

---

## When to Use

Multi-turn workflows apply when:

- **Long-running execution**: Task requires many steps before completion
- **Failure recovery matters**: Partial progress should survive crashes
- **Visibility required**: Need to see what's happening during execution
- **Resumability needed**: May need to pause and continue later
- **Tool orchestration**: Workflow involves Read, Write, Task, Bash calls

Examples: spec interviews, research agents, report generation, code migration, background processing.

**Key insight**: You're directing an autonomous system that manages its own progress through external state.

---

## The State File Pattern

External state is what makes multi-turn special. The state file is the source of truth for progress.

### Why State Files Matter

1. **Restartability**: If the agent fails mid-execution, read state and resume
2. **Visibility**: Monitor progress without waiting for completion
3. **Auditability**: Full record of what happened and when
4. **Composability**: Other agents can read state and continue work

### State Update Rule

```xml
<critical>
    - Update state after EACH action, not in batches
    - Anti-pattern: Do work → Do more work → Update state at end
    - Correct: Do work → Update state → Do more work → Update state
    - This ensures partial progress survives failures
</critical>
```

### Minimal State Schema

Every multi-turn workflow needs at minimum:

```json
{
  "session_id": "unique-identifier",
  "status": "initializing|processing|complete|failed",
  "created_at": "ISO_8601_timestamp",
  "updated_at": "ISO_8601_timestamp"
}
```

Extend based on workflow needs:
- Progress tracking (`completed`, `total`, `current`)
- Results accumulation (`examined[]`, `findings[]`)
- Phase tracking (`current_phase`, `phases: {}`)

---

## Session Directory Structure

Multi-turn workflows operate within a session directory that contains all artifacts:

```
sessions/{session_id}/
├── state.json           # Progress tracking, metadata
├── {artifact}.md        # Primary output being built
├── subagents/           # Subagent state files (parallel patterns)
├── research/            # Research artifacts
└── context/             # Supporting files, diagrams
```

### Directory Design Principles

1. **Self-contained**: Everything needed to understand/resume lives in the directory
2. **Discoverable**: Standard naming conventions (state.json, not progress.json)
3. **Composable**: Subagents write to known locations within parent session

---

## The `<phases>` Structure

Phases define external execution flow—each phase involves tool calls and state updates.

```xml
<workflow>
    <phase id="1" name="Initialize">
        <action>
            - Validate input
        </action>
        <action>
            - Create session directory
        </action>
        <action>
            - Write initial state file
        </action>
    </phase>

    <phase id="2" name="Execute">
        <critical>
            - Update state after EACH action
        </critical>
        <action>
            - Perform operation
        </action>
        <action>
            - Update state with result
        </action>
        <action>
            - Repeat until complete
        </action>
    </phase>

    <phase id="3" name="Finalize">
        <action>
            - Synthesize results
        </action>
        <action>
            - Write final output
        </action>
        <action>
            - Update status to "complete"
        </action>
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
| Recovery | Read state, resume | Not applicable |

---

## Output Protocol

Multi-turn workflows write output to files, not response messages.

```xml
<output_protocol>
    <critical>
        You MUST:
        1. Write results to: {session}/output.md
        2. Update state after EACH item processed
        3. Return ONLY: "Complete. Results at: {path}"

        - Do NOT include full results in response message
    </critical>
</output_protocol>
```

### Why Files Over Responses

1. **Size**: Results may exceed response limits
2. **Persistence**: Files survive context truncation
3. **Composability**: Other agents read files, not message history
4. **Clarity**: Response confirms completion, files contain content

---

## Multi-Turn Techniques

Two specialized patterns build on this foundation:

### Iterative Loop

User provides input each cycle. System asks → user answers → state updates → repeat.

**Canonical example**: Spec mode (`/spec`)
- Builds spec.md incrementally through user interview
- state.json tracks open_questions, key_decisions, phase status
- Each exchange triggers atomic update to both files

→ See: [Iterative Loop](10-iterative-loop.md)
→ Real implementation: `.claude/commands/session/spec.md`

### Parallel Agents

Orchestrator spawns multiple subagents, each with their own state file.

**Canonical example**: Research system
- Each subagent writes subagent_{id}.json
- State updated after each file examined
- Report writer synthesizes all state files

→ See: [Parallel Agents](20-parallel-agents.md)
→ Real implementation: `.claude/agents/research/research-subagent.md`

---

## Error Handling

State files enable graceful failure handling:

```xml
<error_handling>
    <scenario name="Agent Crashes">
        <recovery>
            - Read state.json to find last known position
            - Resume from that point
            - Partial results preserved in state
        </recovery>
    </scenario>

    <scenario name="Partial Completion">
        <recovery>
            - status field indicates incomplete
            - Accumulated results still available
            - Can continue or report partial findings
        </recovery>
    </scenario>

    <scenario name="Unrecoverable Error">
        <recovery>
            - Set status: "failed"
            - Write error details to state
            - Preserve partial work for debugging
        </recovery>
    </scenario>
</error_handling>
```

---

## Checklist

When designing multi-turn workflows:

- [ ] State file initialized FIRST before any work
- [ ] State updated after EACH action (not batched)
- [ ] Session directory structure is self-contained
- [ ] Status field enables progress visibility
- [ ] Output written to files, not response messages
- [ ] Recovery path documented for failure scenarios
- [ ] Timestamps track when things happened
