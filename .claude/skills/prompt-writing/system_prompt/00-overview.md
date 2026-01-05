---
covers: Patterns for writing static AI instructions—system prompts, commands, agent definitions, skills, and workflow files.
type: overview
concepts: [system-prompt, commands, agents, skills, workflows, directives]
---

# Static AI Instructions

Instructions loaded once, then executed. This covers everything from simple system prompts to complex agent definitions.

---

## Contents

- [What This Covers](#what-this-covers) — Artifact types that share this structure
- [Key Distinction](#key-distinction) — Control vs handoff: the fundamental split
- [Instruction Types](#instruction-types) — Routing to specific patterns

---

## What This Covers

All of these share the same underlying structure:

| Artifact | What It Is | Examples |
|----------|------------|----------|
| **System Prompt** | Traditional system message in API calls | Classification prompt, chat persona |
| **Command/Skill** | Expandable instruction triggered by user | `/commit`, `/review-pr`, skill files |
| **Agent Definition** | Full agent with tools and autonomous workflow | Research agent, code reviewer |
| **Workflow File** | Multi-phase autonomous execution | Build pipeline, data processing |
| **Directive** | Instruction handed to a running system | Claude Code task, background agent |

They're all "system prompts" in spirit—static instructions that shape AI behavior before dynamic context arrives.

**Key principle**: Static instructions define WHAT and HOW. Dynamic context (user prompt) provides the specific inputs and runtime state.

---

## Key Distinction

The fundamental split in prompt design: **who controls execution?**

| Aspect | Single-Completion | Multiturn |
|--------|-------------------|-----------|
| **Control** | Your code controls the LLM | Autonomous system controls itself |
| **Execution** | You call API, process response, decide next | System runs multiple turns on its own |
| **Loop Owner** | Your application | The agent/system |
| **Examples** | Classification, extraction, code-orchestrated agents | Claude Code skills, background agents, pipelines |

**Single-Completion**: Your code makes the LLM call. Your code processes the response. You decide what happens next. Even if you're doing multi-step agentic work, if YOUR code orchestrates the calls, it's single-completion.

**Multiturn**: You submit instructions to an autonomous system. The system decides what LLM calls to make, what tools to use, and when it's done. You direct; the system executes.

**The distinction is about WHO controls the execution loop, not whether tools are involved.**

Tool use is fine in single-completion—you can use structured outputs, function calling, etc. The question is: does your code handle the tool execution, or does an autonomous system?

### Choosing Your Pattern

```
Is YOUR code calling the LLM API and processing responses?
├─ YES → Single-Completion (10-single-completion.md)
│         Your code orchestrates, LLM completes tasks
│
└─ NO → Multiturn (you hand off to an autonomous system)
         │
         Does the user provide input each cycle?
         ├─ YES → Iterative Loop (20-multiturn/10-iterative-loop.md)
         │         Interviews, spec refinement, requirements
         │
         └─ NO → Autonomous (20-multiturn/00-base.md)
                  Skills, background agents, pipelines
```

For the canonical XML structure and copy-paste template, see [Base Template](10-base-template.md).

---

## Instruction Types

Templates for each pattern. See [Key Distinction](#key-distinction) for when to use each.

| Resource | File | Purpose |
|----------|------|---------|
| **Base Template** | `10-base-template.md` | Canonical XML structure to copy and adapt |
| **Single-Completion** | `10-single-completion.md` | Your code controls execution |
| **Multiturn Autonomous** | `20-multiturn/00-base.md` | System runs on its own |
| **Multiturn Iterative** | `20-multiturn/10-iterative-loop.md` | User provides input each cycle |
