---
covers: Workflow design as the central discipline for all instruction artifacts
type: overview
concepts:
  - workflow-design
  - steps
  - phases
  - single-completion
  - multi-turn
depends-on:
  - system_prompt/00-overview.md
  - system_prompt/10-base-template.md
---

# Workflow Design

The `<workflow>` section is where your prompt earns its value. Purpose provides context. Knowledge supplies facts. Goal defines success. But the **workflow IS the product**—it's the instruction sequence that directs model behavior.

---

## Core Insight

Everything else in your prompt is context. The workflow is action.

- **Purpose, Knowledge, Goal** → Set up the model's understanding
- **Workflow** → Direct what the model actually does

A well-designed workflow compensates for ambiguous goals. A poorly-designed workflow undermines perfect context. The workflow is the lever you have the most control over.

---

## The Fundamental Split

Workflow design splits into two patterns based on **execution model**:

| Aspect | Single-Completion | Multi-Turn |
|--------|-------------------|------------|
| **Structure** | `<steps>` | `<phases>` |
| **Execution** | Internal reasoning (thinking window) | External actions (tool calls, state) |
| **State** | None—everything in one response | External (JSON files, schemas) |
| **Output** | Single response | Incremental updates |
| **Control** | Your code orchestrates | Autonomous system executes |

**Steps** are internal—a reasoning scaffold within the model's thinking window. The model processes them all in one completion.

**Phases** are external—execution checkpoints with real-world effects. Each phase may involve tool calls, state updates, and user interactions across multiple completions.

---

## Pattern Navigation

| Pattern | File | When to Use |
|---------|------|-------------|
| Single-Completion | `20-single-completion.md` | Your code calls the API and processes responses |
| Multi-Turn Base | `30-multi-turn/00-base.md` | Autonomous system with external state |
| Iterative Loop | `30-multi-turn/10-iterative-loop.md` | User provides input each cycle |
| Parallel Agents | `30-multi-turn/20-parallel-agents.md` | Orchestrator spawns subagents |

---

## Choosing Your Pattern

```
Does YOUR code call the LLM API and process each response?
├─ YES → Single-Completion (20-single-completion.md)
│         Your code orchestrates; model completes discrete tasks
│
└─ NO → Multi-Turn (you hand off to an autonomous system)
         │
         Does the user provide input each cycle?
         ├─ YES → Iterative Loop (30-multi-turn/10-iterative-loop.md)
         │         Interviews, spec refinement, requirements gathering
         │
         └─ NO → Does the system spawn subagents?
                  ├─ YES → Parallel Agents (30-multi-turn/20-parallel-agents.md)
                  │         Research orchestration, distributed tasks
                  │
                  └─ NO → Autonomous Base (30-multi-turn/00-base.md)
                           Skills, background agents, pipelines
```

---

## Prerequisites

Before designing workflows, ensure you understand:

1. **Base Template** (`10-base-template.md`) — Canonical XML structure
2. **Base Principles** (`10-base.md`) — Core workflow design theory

Then proceed to the pattern that matches your execution model.
