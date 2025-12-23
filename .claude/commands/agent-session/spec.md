---
description: Enter spec mode to define requirements and goals before implementation planning
argument-hint: [topic] | continue [session-id] | finalize | list
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, AskUserQuestion
model: opus
---

# Spec Mode

Enter spec mode to define WHAT you want to build before planning HOW to build it.

## Skill Reference

Read the agent-session skill for templates and full documentation:
- Skill: `.claude/skills/agent-session/SKILL.md`
- Templates: `.claude/skills/agent-session/templates/`
- Working directory: `agents/sessions/`

## Variables

```
SPEC_ARGUMENTS = $ARGUMENTS
SESSIONS_DIR = agents/sessions
TEMPLATES_DIR = .claude/skills/agent-session/templates
```

## Instructions

Parse SPEC_ARGUMENTS to determine the action:

1. **No arguments or topic string**: Create new session OR list active sessions
2. **`continue [session-id]`**: Resume an existing session
3. **`finalize`**: Finalize the current spec (marks it ready for planning)
4. **`list`**: Show all sessions with their status

## Core Principles

Spec mode is:
- **Almost read-only** - Only writes to the session directory
- **Question-driven** - Asks clarifying questions to understand the problem
- **Focused on WHAT and WHY** - Not implementation details (that's plan mode)
- **Iterative** - Refines understanding through conversation

<workflows>
    <workflow name="new_session">
        <trigger>Topic string provided (not a subcommand)</trigger>
        <steps>
            <step id="1">Generate session_id: {YYYY-MM-DD}_{topic-slug}_{6-char-random-id}</step>
            <step id="2">Create directory structure:
                ```bash
                mkdir -p SESSIONS_DIR/{session_id}/research
                mkdir -p SESSIONS_DIR/{session_id}/context/diagrams
                mkdir -p SESSIONS_DIR/{session_id}/context/notes
                ```
            </step>
            <step id="3">Initialize state.json with:
                - current_phase: "spec"
                - phases.spec.status: "draft"
                - phases.spec.started_at: now()
                - Extract initial topic and description from arguments
            </step>
            <step id="4">Create initial spec.md from template (see spec_template below)</step>
            <step id="5">Write active_session.json to SESSIONS_DIR with current session_id</step>
            <step id="6">Enter question-driven exploration mode</step>
        </steps>
    </workflow>

    <workflow name="continue_session">
        <trigger>`continue [session-id]` or just `continue` (uses active session)</trigger>
        <steps>
            <step id="1">Load session from state.json</step>
            <step id="2">Read current spec.md to understand context</step>
            <step id="3">Review open_questions from state</step>
            <step id="4">Continue question-driven exploration</step>
        </steps>
    </workflow>

    <workflow name="finalize_spec">
        <trigger>`finalize` command</trigger>
        <steps>
            <step id="1">Load active session</step>
            <step id="2">Review spec.md for completeness</step>
            <step id="3">Ensure required sections are present:
                - Overview
                - High-level goals
                - Mid-level goals
            </step>
            <step id="4">Ask user to confirm finalization</step>
            <step id="5">Update state.json:
                - phases.spec.status: "finalized"
                - phases.spec.finalized_at: now()
            </step>
            <step id="6">Add finalization header to spec.md</step>
            <step id="7">Report: "Spec finalized. Ready for `/plan` phase."</step>
        </steps>
    </workflow>

    <workflow name="list_sessions">
        <trigger>`list` command or no arguments with existing sessions</trigger>
        <steps>
            <step id="1">Scan SESSIONS_DIR for session directories</step>
            <step id="2">Read state.json from each</step>
            <step id="3">Display table:
                | Session ID | Topic | Phase | Status | Updated |
            </step>
            <step id="4">Highlight active session if one exists</step>
        </steps>
    </workflow>

    <workflow name="question_driven_exploration">
        <description>The core interaction loop during spec mode</description>
        <principles>
            - Ask ONE focused question at a time
            - Explain WHY you're asking
            - After each answer, update spec.md incrementally
            - Surface assumptions explicitly
            - Use diagrams when they clarify understanding
            - Track open questions in state.json
        </principles>
        <question_categories>
            <category name="problem_space">
                - What problem are we solving?
                - Who experiences this problem?
                - What's the current workaround?
                - What triggers the need for this?
            </category>
            <category name="goals">
                - What does success look like?
                - How will we know we're done?
                - What's the minimum viable version?
            </category>
            <category name="constraints">
                - What can't change?
                - What dependencies exist?
                - What's the timeline?
                - Are there technical constraints?
            </category>
            <category name="scope">
                - What's explicitly NOT included?
                - What could be a future phase?
                - What's the priority order?
            </category>
            <category name="context">
                - How does this fit with existing systems?
                - Are there similar implementations to reference?
                - Who else is involved in this decision?
            </category>
        </question_categories>
        <after_each_answer>
            1. Acknowledge understanding
            2. Update relevant section in spec.md
            3. Note any decisions made (add to key_decisions)
            4. Identify if new questions emerged (add to open_questions)
            5. Remove answered questions from open_questions
            6. Ask next question OR summarize progress
        </after_each_answer>
    </workflow>
</workflows>

<spec_template>
# {Topic}

> **Session**: `{session_id}`
> **Status**: Draft
> **Created**: {date}

## Overview

{Initial understanding - to be refined through conversation}

## Problem Statement

{What problem are we solving? Why does it matter?}

## Goals

### High-Level Goals
{The north star - what does ultimate success look like?}

### Mid-Level Goals
{Major capabilities or milestones}

### Detailed Goals (Optional)
{Specific behaviors or features, added as conversation progresses}

## Non-Goals

{What we are explicitly NOT building - prevents scope creep}

## Success Criteria

{How do we know we're done? Testable outcomes}

## Context & Background

{Relevant existing systems, prior art, stakeholder input}

## Key Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| ... | ... | ... |

## Open Questions

- [ ] {Questions still needing answers}

## Diagrams

{Mermaid or ASCII diagrams as understanding develops}

## Notes

{Working notes, ideas, considerations}

---
*This spec is a living document until finalized.*
</spec_template>

<active_session_tracking>
File: agents/sessions/active_session.json
```json
{
  "session_id": "current-active-session-id",
  "path": "agents/sessions/{session_id}",
  "activated_at": "timestamp"
}
```

This file tracks which session is currently active, allowing:
- `/spec continue` without specifying session ID
- `/plan` to automatically pick up the finalized spec
- Quick status checks
</active_session_tracking>

<behavior_constraints>
DURING SPEC MODE:
- DO NOT write code to non-session directories
- DO NOT create implementation plans (that's plan mode)
- DO NOT make architecture decisions (focus on WHAT not HOW)
- DO read codebase files for context
- DO create diagrams in session/context/diagrams/
- DO update spec.md after each meaningful exchange
- DO track questions and decisions in state.json

ALLOWED WRITES:
- agents/sessions/{session_id}/**  (all session files)
- agents/sessions/active_session.json
</behavior_constraints>

<user_output>
When starting a new session:
```
## Spec Session Started

**Session ID**: `{session_id}`
**Topic**: {topic}
**Location**: `agents/sessions/{session_id}/`

I'll help you clarify what you want to build. I'll ask questions to understand
the problem, goals, and constraints before we move to planning.

{First question based on the topic}
```

When continuing a session:
```
## Resuming Spec Session

**Session ID**: `{session_id}`
**Topic**: {topic}
**Status**: {spec_status}

### Current Understanding
{Brief summary of spec.md}

### Open Questions
{List from state.json}

{Continue with next question or ask where to focus}
```

When finalizing:
```
## Spec Finalized

**Session ID**: `{session_id}`
**Topic**: {topic}

### Summary
{High-level and mid-level goals}

### Ready for Planning
The spec is now ready for the planning phase. Use `/plan` to begin
implementation planning, which will use this spec as its foundation.

**Spec Location**: `agents/sessions/{session_id}/spec.md`
```
</user_output>

<error_handling>
    <scenario name="No Arguments, No Active Session">
        Ask if user wants to:
        1. Start a new spec session (provide topic)
        2. List existing sessions
        3. Continue a specific session
    </scenario>
    <scenario name="Session Not Found">
        Show available sessions and ask user to select one.
    </scenario>
    <scenario name="Finalize Without Required Content">
        List missing required sections and offer to continue refining.
    </scenario>
</error_handling>
