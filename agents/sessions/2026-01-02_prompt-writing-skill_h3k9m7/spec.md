# Spec: Prompt Writing Skill

**Session ID**: `2026-01-02_prompt-writing-skill_h3k9m7`
**Status**: ✅ Finalized
**Created**: 2026-01-02
**Finalized**: 2026-01-04

---

## Overview

A skill that enables Claude to generate AI-consumable artifacts—prompts, commands, workflows, and similar instructions—that reflect the user's opinionated approach to AI interaction design.

**Target Consumer**: AI agents (not humans directly)
**Target Producer**: Claude, guided by this skill
**Core Value**: Codifying the user's specific style and preferences into reproducible AI artifacts

---

## User's Opinionated Approach (Analysis)

Based on analysis of the user's existing artifacts, the following patterns define their style:

### Core Philosophy

1. **Story-Driven Sequential Revelation**
   - Information is revealed strategically, not dumped at once
   - The model is led step-by-step from stateless to full context
   - Flow follows: **Context → Plan → Boundaries**

2. **Purpose Over Role**
   - Instead of "You are a [role]", define a clear mission for the computational instance
   - The AI's "reason for being" is to successfully complete the task
   - "Purpose" provides direction and meaning for the operational lifespan

3. **Background is the Differentiator**
   - The WHY behind the task is "often the differentiator between a good prompt and a great one"
   - Background enriches context, anchors generation in user's true objectives
   - Resolves ambiguity during generation by providing intent context

4. **Explicit Steps are Non-Negotiable**
   - Steps inject expert methodology, overriding the model's "statistically average" default
   - Provides control points for iteration, testing, and debugging
   - Enables reliable, production-level outputs with predictable behavior

5. **Constraints Are Localized (Vertical Slices)**
   - Per-step constraints where they apply, not all upfront
   - Global constraints for universal rules across all steps
   - Makes prompts easier to read, maintain, and debug

### Canonical Blueprint: Single-Task Prompts

```
System Prompt
├─ Purpose
│   ├─ Persona
│   └─ Mission
├─ Key Knowledge and Expertise
├─ Goal
├─ Background
├─ Mission Brief
├─ Workflow
│   ├─ Overview
│   ├─ Expected Inputs
│   ├─ Steps
│   │   └─ step ‹name›
│   │       ├─ description
│   │       └─ [Optional] Constraints
│   ├─ Global Constraints
│   ├─ Output Format
│   └─ [Optional] Examples
User Prompt
├─ Re-iteration of Key Information
└─ User Inputs
```

### Orchestrated Workflow Prompts (Commands/Agents)

For multi-phase processes with parallel execution and state coordination:

```markdown
---
name: agent-name
description: What this agent does
tools: Read, Write, Glob, Grep, Task, ...
model: opus
---

<purpose>
Clear mission statement for this agent.
</purpose>

<variables>
RESEARCH_REQUEST = $ARGUMENTS
NUM_SUBAGENTS = 3
</variables>

<input_format>
What this agent receives.
</input_format>

<output_protocol>
  <critical>
  What the agent MUST do with output.
  </critical>
</output_protocol>

<state_schema>
{
  "id": "session_id",
  "status": "initializing|researching|complete|failed",
  "created_at": "timestamp",
  ...
}
</state_schema>

<workflow>
    <phase id="1" name="Initialize">
        <action>First action</action>
        <action>Second action</action>
    </phase>
    <phase id="2" name="Execute">
        <critical>Important constraint</critical>
        <action>Main work</action>
    </phase>
    ...
</workflow>

<principles>
  <principle name="Name">
      Explanation of the principle.
  </principle>
</principles>

<error_handling>
    <scenario name="Error Type">
        - How to handle it
    </scenario>
</error_handling>

<important_notes>
- Critical reminders
- Constraints
</important_notes>
```

**Key orchestrated workflow patterns:**
1. **Frontmatter**: `name`, `description`, `tools`, `model`
2. **Purpose + Variables**: Mission and configurable parameters
3. **Input/Output protocols**: What comes in, what must go out
4. **State schema**: JSON structure for tracking progress
5. **Phased workflow**: Sequential phases with actions, `<critical>` tags for emphasis
6. **Principles**: Named guidance patterns
7. **Error handling**: Named scenarios with recovery steps

### Iterative Loop Prompt Structure

For interview-style loops with state machine transitions:

```
System Prompt
├─ PURPOSE
├─ PERSONA
├─ DOMAIN_SCOPE
├─ SUCCESS_CRITERIA
├─ PROTOCOL
│   ├─ GLOBAL_CONSTRAINTS
│   ├─ LOOP_STATE_VARIABLES (stage, index, memory, unresolved)
│   ├─ STAGES (state machine: PREP → Q → REFLECT → END)
│   ├─ OUTPUT_FORMATS (per-turn AND final)
│   └─ EXAMPLES
├─ MEMORY_HANDLING_RULES
└─ TERMINATION_NOTICE
User Prompt
├─ CONTEXT
└─ INITIAL_DATA
```

### User Prompt Formatting (Dynamic Context Assembly)

**Critical insight**: System prompt stays static; user prompt owns the dynamic context window.

```python
# Pattern: Modular formatters for each context type
def format_user_prompt(context, messages):
    prompt = "Analyze the context below and generate your response:\n\n"

    # Layer 1: Temporal grounding
    prompt += format_date_context(...)

    # Layer 2: Static reference data
    prompt += format_background_knowledge(...)  # <background_knowledge_base>

    # Layer 3: Constraints/requirements
    prompt += format_requirements(...)  # <carrier_requirements>

    # Layer 4: Decision-relevant data
    prompt += format_pricing_info(...)  # <pricing_information>

    # Layer 5: Situational context
    prompt += format_call_context(...)  # <call_context>

    # Layer 6: State accumulated so far
    prompt += format_collected_data(...)  # <booking_details>

    # Layer 7: History + analysis
    prompt += format_history(...)  # <rate_history>, <negotiation_analysis>

    # Layer 8: Recent conversation (sliding window)
    prompt += format_conversation_history(messages, max=20)

    # Final instruction
    prompt += "\nGenerate your next response..."
    return prompt
```

**Key user prompt principles**:
1. **Modular formatters**: Each context type has its own `format_*_context()` function
2. **XML semantic tags**: `<carrier_requirements>`, `<pricing_information>`, etc.
3. **Hierarchical nesting**: Tags contain sub-tags for structure
4. **Conditional inclusion**: Only include sections if data exists
5. **Sliding window**: Limit conversation history to prevent bloat
6. **Directive injection**: Runtime insertions via `<active_directives>`
7. **End instruction**: Brief reminder of the task

### XML Tag Conventions

```xml
<!-- Semantic wrapper tags -->
<background_knowledge_base>...</background_knowledge_base>
<carrier_requirements>
    <weight_restrictions>
        <min_weight>...</min_weight>
        <max_weight>...</max_weight>
    </weight_restrictions>
    <avoid_commodity_types>
        <type>...</type>
    </avoid_commodity_types>
</carrier_requirements>

<!-- Conversation history with role attribution -->
<recent_conversation_history>
    <message role='broker'>...</message>
    <message role='carrier'>...</message>
</recent_conversation_history>

<!-- Runtime directive injection -->
<active_directives>
    <background_directive priority="INTERRUPT">...</background_directive>
</active_directives>
```

### System Prompt Sections (Observed Patterns)

| Section | Purpose |
|---------|---------|
| `<purpose>` | Clear mission statement |
| `<your_role>` | Metaphor/framing (e.g., "ROUTER", "dispatcher") |
| `<system_boundaries>` | Hard constraints, what NOT to do |
| `<workflow_guidance>` | Phased flow with natural transitions |
| `<*_strategy>` | Domain-specific tactics (e.g., `<rate_negotiation_strategy>`) |
| `<*_evaluation>` | How to check/validate things |
| `<conversation_style>` | `<principles>` + `<anti_patterns>` |
| `<directive_handling>` | How to process runtime injections |
| `<output_format>` / `<output_instructions>` | What output should look like |
| `<important_rules>` | Critical constraints (numbered) |

---

## High-Level Goals

1. **Enable Claude to generate production-quality AI artifacts** in the user's opinionated style
2. **Codify the user's prompt engineering methodology** so it's reproducible without manual enforcement
3. **Cover the full spectrum of artifact types** needed for AI system development

---

## Mid-Level Goals

### Area 1: Single-Task Prompts
**What it is**: One-off, programmatic, done. A single completion that runs and finishes.
- May have pseudo-workflow steps (do this, then this, then this)
- But it's a single LLM call that produces output
- Examples: classification, extraction, generation, transformation

**Output**: System prompt (Markdown+XML) + User prompt formatter (Python)

### Area 2: Workflow Prompts (Agentic)
**What it is**: Multi-step agentic system (like Claude Code) that performs complex workflows.
- Agent runs multiple steps before finishing
- Has phases, state tracking, parallel execution
- Not necessarily user-in-the-loop—agent drives itself

**Output**: Command/agent definition (Markdown+XML with frontmatter)

### Area 3: Iterative Loop Prompts (User-in-the-Loop)
**What it is**: Workflow with user interaction at each cycle.
- Interview style, maintaining state across turns
- Phases with transitions, but user provides input each round
- Examples: spec interviews, knowledge extraction, Socratic dialogue

**Output**: Loop prompt (Markdown+XML with state machine)

### Cross-Cutting: User Prompt Formatting (Python)
**What it is**: Dynamic context assembly that pairs with any system prompt.
- Applies to all areas where user prompts need runtime formatting
- Modular formatters, semantic XML tags, sliding window

**Output**: Python functions (state → formatted string)

---

## Reference Examples

These are the real examples the skill should reference/bundle:

| Category | Example | Location | Demonstrates |
|----------|---------|----------|--------------|
| **Single-task system** | Main agent | `context/example-prompts/main-agent/system_prompt.py` | Comprehensive workflow guidance, conversation style |
| **Single-task system** | Background agent | `context/example-prompts/background-agent/system_prompt.py` | Simple router, decision prompt |
| **User prompt (Python)** | Main agent | `context/example-prompts/main-agent/user_prompt.py` | Modular formatters, layered XML context |
| **User prompt (Python)** | Background agent | `context/example-prompts/background-agent/user_prompt.py` | Lightweight state tracking |
| **Orchestrated workflow** | Research command | `.claude/commands/development/research.md` | Multi-phase orchestration, parallel subagents |
| **Orchestrated workflow** | Research subagent | `.claude/agents/research/research-subagent.md` | Focused investigator, incremental state |
| **Orchestrated workflow** | Report writer | `.claude/agents/research/report-writer.md` | Synthesis, template-driven output |
| **Iterative loop** | Interviewer structure | `context/6.1_interviewer_prompt_structure.md` | State machine, loop variables |

---

## Context & Background

The user has developed a sophisticated, principled approach to prompt engineering through practice. This approach is currently encoded in:
- Blog posts / reference documents (`6_single_task_prompt_structure.md`, `6.1_interviewer_prompt_structure.md`)
- Existing skills (`docs-framework`, `session`)
- Command definitions (XML-heavy workflow specifications)
- Production code examples (`background-agent/`, `main-agent/`)

The skill would codify this approach so Claude can generate artifacts that match this style without the user having to manually enforce the patterns each time.

**Key distinction clarified by user**:
- Single-task = single completion, runs and moves to next thing
- Iterative loop = longer-running process (like research) with multiple cycles
- User prompt formatting = the dynamic context assembly that pairs with static system prompts

---

## Requirements

### Functional Requirements

1. **Automatic invocation**: Skill triggers whenever Claude is writing prompts, workflows, subcommands, or anything sent to an AI for processing
2. **Dual output format**:
   - **User prompts** → Python files (functions taking state object, returning formatted string)
   - **System prompts / workflows / static artifacts** → Markdown files with XML formatting
3. **Template-based guidance**: Provide generic templates with principles explained + real example references (NOT fill-in-the-blank TODOs)
4. **Reference linking**: Link to real prompts (e.g., research prompt, main-agent, background-agent) so Claude can see patterns in action

### Non-Functional Requirements

1. Skill should be comprehensive enough to cover all AI artifact types
2. Templates should be generic enough to adapt to different domains
3. Principles should be clear enough that Claude can apply them without asking
4. Python formatters should follow the observed pattern (take state, return string)

---

## Scope

### In Scope (Confirmed)

1. **Single-task/completion prompts**: System prompts (Markdown+XML), user prompts (Python)
2. **Orchestrated workflow prompts**: Commands/agents with phased workflows (Markdown+XML)
3. **Iterative loop prompts**: State machine style for interviews/research (Markdown+XML)
4. **User prompt formatting**: Python functions for dynamic context assembly
5. Templates with principles + real example references (NOT fill-in-the-blank TODOs)
6. Automatic invocation when writing any AI-consumable artifact

### Out of Scope

- Evaluating/critiquing existing prompts (this is a generation skill, not a review skill)
- Non-AI artifacts (documentation, code that isn't prompts)
- Specific domain knowledge (the skill teaches structure, not domain content)

---

## Success Criteria

1. When Claude writes any AI-consumable artifact, it follows the user's opinionated patterns
2. User prompts are generated as Python formatter functions (state in, string out)
3. System prompts/workflows are generated as Markdown with XML structure
4. Output matches the quality/style of the user's existing production prompts
5. No fill-in-the-blank TODOs—templates are explanatory with real examples

---

## Skill Structure (Progressive Disclosure)

Following the docs-framework pattern with numbered directories:

```
prompt-writing/
├── SKILL.md                        # Lean entry point: triggers, routing, commands
├── 00-reference/                   # Philosophy and background (the WHY)
│   ├── 00-overview.md
│   ├── 10-philosophy.md            # Why structure matters, LLM characteristics
│   └── 20-principles.md            # Core principles (story-driven, purpose-over-role, etc.)
├── 10-prompt-types/                # The three prompt types
│   ├── 00-overview.md              # Explains all three, how to pick
│   ├── 10-single-task/
│   │   ├── 00-overview.md          # The WHY and when to use
│   │   └── 10-template.md          # Structure + markdown links to examples
│   ├── 20-workflow/
│   │   ├── 00-overview.md
│   │   └── 10-template.md
│   └── 30-iterative-loop/
│       ├── 00-overview.md
│       └── 10-template.md
├── 20-user-prompt/                 # Python formatter patterns (cross-cutting)
│   ├── 00-overview.md              # Principles of dynamic context assembly
│   └── 10-template.md              # Python patterns + links to examples
└── 99-appendix/
    ├── 00-overview.md
    └── 10-anti-patterns.md         # Common mistakes to avoid
```

**File purposes**:
- `SKILL.md`: Lean entry point—triggers, routing logic, commands table
- `00-overview.md`: Each section's table of contents and summary
- `*-philosophy.md` / `*-principles.md`: The WHY—reasoning, background
- `*-template.md`: The WHAT—concrete structure + markdown links to real examples

**Invocation**: Skill triggers whenever Claude is writing prompts, workflows, commands, or anything an agent would run.

**Routing**: SKILL.md routes to appropriate section based on intent:
1. Need to understand the approach? → `00-reference/`
2. Writing a prompt? → `10-prompt-types/` → pick the right type
3. Need Python formatters? → `20-user-prompt/`
4. Checking for mistakes? → `99-appendix/10-anti-patterns.md`

**Examples**: Each `template.md` contains markdown links to real examples (paths from `.claude`). No copies—just references.

---

## Anti-Patterns (Summary)

These will live in `99-appendix/10-anti-patterns.md`. Initial list:

| Anti-Pattern | Instead |
|--------------|---------|
| Generic roles ("You are a helpful assistant") | Use `<purpose>` with clear mission |
| Dumping all context at once | Progressive disclosure: Context → Plan → Boundaries |
| No background/WHY section | Always include why this task matters |
| Vague steps ("Process the data") | Inject expert methodology with explicit steps |
| All constraints upfront | Localize constraints (vertical slices) |

*More to be added as identified.*

---

## Open Questions

- *(Resolved)* Examples: **Link to existing locations** (no duplicates)
- *(Resolved)* Area detection: **Progressive disclosure** within skill, model decides based on context
- *(Captured)* Anti-patterns: Started list, will expand as more are identified

---

## Notes & Discussion

### Analysis Summary

The user's approach is grounded in understanding LLM computational characteristics:
- **Statelessness**: All context must be provided upfront
- **Sequential Processing**: Logical order builds understanding progressively
- **Attention Mechanism**: Context established before details = better relevance calculation
- **Literalness (Genie Effect)**: Explicit definition prevents unintended interpretations

The skill must embody these principles in everything it generates.

### Dual-Agent Pattern Observed

The example prompts show a dual-agent architecture:
- **Main Agent**: Handles conversation, comprehensive workflow guidance, receives directives
- **Background Agent**: Polls on loop, routes to tools, simpler decision-making

The background agent injects directives into the main agent's user prompt via `<active_directives>` tags. This pattern may be worth documenting as a reference architecture.
