---
description: Enter spec mode to define requirements and goals before implementation planning
argument-hint: [topic | session-id | finalize] [description]
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
$1 = Primary argument (session-id, topic, or "finalize")
$2 = Optional additional context or description
SESSIONS_DIR = agents/sessions
TEMPLATES_DIR = .claude/skills/agent-session/templates
```

## Instructions

Parse `$1` and `$2` to follow the linear flow:

1. **`$1` matches existing session ID**: Load that session (check `SESSIONS_DIR/$1/state.json`)
   - If `$2 = "finalize"`: Jump to finalization phase for that session
2. **`$1` is a topic string**: Create a new session with `$1` as topic, `$2` as optional description
3. **`$1` is empty**: Create a new session (prompt user for topic)

Then proceed through: Initialize → Question-driven exploration → Finalize (on user approval)

## Core Principles

Spec mode is:
- **Almost read-only** - Only writes to the session directory
- **In-depth interviewing** - Asks thorough, non-obvious clarifying questions about literally anything to understand the problem
- **Focused on WHAT and WHY** - Not implementation details (that's plan mode)
- **Persistent** - Continues interviewing until the spec is truly complete

<workflows>
    <workflow name="spec_flow">
        <description>Linear flow from session resolution through finalization</description>
        <phase name="1_parse_inputs">
            <description>Parse positional arguments to determine session context</description>
            <inputs>
                - `$1`: Primary argument - one of:
                    - existing session ID → load that session
                    - topic string → create new session
                    - empty → prompt for topic
                - `$2`: Secondary argument - one of:
                    - "finalize" → trigger finalization (when $1 is session ID)
                    - description/context for new sessions (when $1 is topic)
            </inputs>
        </phase>
        <phase name="2_resolve_session">
            <description>Either load existing session or create new one</description>
            <branch condition="$1 matches existing session ID">
                <action>Load existing session</action>
                <steps>
                    <step id="1">Check if SESSIONS_DIR/$1/state.json exists</step>
                    <step id="2">Load state.json from SESSIONS_DIR/$1/</step>
                    <step id="3">Read current spec.md to restore context</step>
                    <step id="4">Review open_questions from state</step>
                </steps>
                <on_failure>Session not found → fall through to create new session</on_failure>
            </branch>
            <branch condition="$1 is topic string OR $1 is empty">
                <action>Create new session</action>
                <steps>
                    <step id="1">If $1 is empty, prompt user for topic</step>
                    <step id="2">Generate session_id: {YYYY-MM-DD}_{topic-slug}_{6-char-random-id}</step>
                    <step id="3">Create directory structure:
                        ```bash
                        mkdir -p SESSIONS_DIR/{session_id}/research
                        mkdir -p SESSIONS_DIR/{session_id}/context/diagrams
                        mkdir -p SESSIONS_DIR/{session_id}/context/notes
                        ```
                    </step>
                    <step id="4">Initialize state.json with:
                        - current_phase: "spec"
                        - phases.spec.status: "draft"
                        - phases.spec.started_at: now()
                        - topic: $1 (or prompted value)
                        - description: $2 (if provided)
                        - prior_session: null (will be set if user provides one)
                    </step>
                    <step id="5">Prompt for prior spec references:
                        - Use AskUserQuestion: "Are there prior specs to reference for context?"
                        - Options: "Yes - I have a prior session ID", "No - this is standalone"
                        - If yes, prompt for session ID input
                        - Update state.json prior_session field with provided ID
                    </step>
                    <step id="6">If prior_session provided:
                        - Read SESSIONS_DIR/{prior_session}/spec.md
                        - Extract key context: goals, decisions, constraints
                        - Note relevant prior context for this spec
                    </step>
                    <step id="7">Create initial spec.md from TEMPLATES_DIR/spec.md</step>
                </steps>
            </branch>
        </phase>
        <phase name="3_initialize">
            <description>Prepare session state for interaction</description>
            <steps>
                <step id="1">Confirm session is loaded and active</step>
                <step id="2">Display session status to user (new or resumed)</step>
                <step id="3">If resuming, summarize current understanding from spec.md</step>
                <step id="4">If resuming, list open questions from state.json</step>
            </steps>
        </phase>
        <phase name="4_question_driven_exploration">
            <description>The core interaction loop during spec mode</description>
            <principles>
                - Ask ONE focused question at a time
                - Be very in-depth - ask about literally anything: technical details, UI/UX, concerns, tradeoffs, edge cases
                - Avoid obvious questions - dig deeper into non-obvious aspects
                - Explain WHY you're asking
                - After each answer, ATOMICALLY update spec.md AND state.json before proceeding
                - Surface assumptions explicitly
                - Continue interviewing persistently until the spec is truly complete
                - Use diagrams when they clarify understanding
                - Capture the user's mental model, reasoning, and "taste" - not just requirements
                - Preserve nuance: the WHY behind each decision matters as much as the WHAT
                - Use user's own words when they convey important intent or preference
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
                <category name="deeper_exploration">
                    - What concerns you about this approach?
                    - What tradeoffs are you willing to accept?
                    - Are there UI/UX considerations that matter?
                    - What edge cases keep you up at night?
                    - What would make you consider this a failure even if it "works"?
                </category>
                <category name="taste_and_reasoning">
                    - What's your mental model for how this should work?
                    - Why does this particular approach resonate with you?
                    - What's the experience you're trying to create?
                    - When you imagine using this, what does it feel like?
                    - What would feel "off" even if it technically worked?
                    - Can you describe your aesthetic or preference for how this behaves?
                </category>
            </question_categories>
            <after_each_answer>
                <critical>Each answer triggers an ATOMIC save cycle - NEVER batch updates</critical>

                1. Acknowledge understanding (capture user's exact phrasing for nuance)
                2. Update spec.md IMMEDIATELY:
                   - Add/update relevant section
                   - Capture the WHY behind user's answer, not just the WHAT
                   - Preserve user's mental model and "taste" in their own words where valuable
                3. Update state.json IMMEDIATELY:
                   - Sync open_questions (add new, remove answered)
                   - Update key_decisions with rationale if decisions emerged
                   - Update goals arrays if goals emerged
                   - Set updated_at timestamp
                4. THEN ask next question OR summarize progress

                <rationale>
                This atomic pattern ensures no work is lost. The user's nuanced input
                is valuable - by saving after each exchange, we preserve context even
                if the session is interrupted.
                </rationale>
            </after_each_answer>
            <exit_condition>User signals readiness to finalize OR all key questions answered</exit_condition>
        </phase>
        <phase name="5_finalize">
            <description>Complete and lock the spec for planning phase</description>
            <trigger>User approval (explicit request or confirmation prompt)</trigger>
            <steps>
                <step id="1">Review spec.md for completeness</step>
                <step id="2">Ensure required sections are present:
                    - Overview
                    - High-level goals
                    - Mid-level goals
                </step>
                <step id="3">Ask user to confirm finalization</step>
                <step id="4">Update state.json:
                    - phases.spec.status: "finalized"
                    - phases.spec.finalized_at: now()
                </step>
                <step id="5">Add finalization header to spec.md</step>
                <step id="6">Report: "Spec finalized. Ready for `/plan` phase."</step>
            </steps>
            <on_incomplete>List missing required sections and continue exploration</on_incomplete>
        </phase>
    </workflow>
</workflows>

<templates>
    <location>TEMPLATES_DIR/spec.md</location>
    <description>Read the spec template from the templates directory when creating new sessions</description>
    <variables>
        - {{TOPIC}}: Session topic from $1
        - {{SESSION_ID}}: Generated session ID
        - {{DATE}}: Current date
        - {{INITIAL_UNDERSTANDING}}: Initial context from $2 or conversation
    </variables>
</templates>

<behavior_constraints>
DURING SPEC MODE:
- DO NOT write code to non-session directories
- DO NOT create implementation plans (that's plan mode)
- DO NOT make architecture decisions (focus on WHAT not HOW)
- DO NOT batch updates - save after EVERY exchange
- DO read codebase files for context
- DO create diagrams in session/context/diagrams/
- DO update spec.md AND state.json after each meaningful exchange (atomically)
- DO capture the user's reasoning and mental model, not just their answers
- DO use the user's own phrasing when it conveys important nuance or "taste"
- DO document WHY decisions were made, not just WHAT was decided

ALLOWED WRITES:
- agents/sessions/{session_id}/**  (all session files)
</behavior_constraints>

<user_output>
    <scenario name="prior_spec_prompt" trigger="After creating new session directory">
        Use AskUserQuestion to check for prior specs:
        ```
        question: "Are there prior specs to reference for context?"
        header: "Prior Spec"
        options:
          - label: "No prior spec"
            description: "This is a standalone spec with no prior context needed"
          - label: "Yes, link prior session"
            description: "I have a prior session ID to reference for context"
        ```
        If user selects "Yes", prompt for session ID via "Other" input field.
        Then read the prior spec.md and summarize relevant context.
    </scenario>
    <scenario name="new_session" trigger="Creating a new spec session">
```markdown
## Spec Session Started

**Session ID**: `{session_id}`
**Topic**: {topic}
**Location**: `agents/sessions/{session_id}/`
{if prior_session}**Prior Context**: `{prior_session}` - {brief summary of prior spec}{/if}

I'll interview you in-depth about literally anything relevant: technical details,
UI/UX, concerns, tradeoffs, edge cases, and more. I'll ask non-obvious questions
and continue until we've thoroughly captured your vision.

{First question based on the topic}
```

    </scenario>
    <scenario name="resume_session" trigger="Loading an existing session">
```markdown
## Spec Session Resumed

**Session ID**: `{session_id}`
**Topic**: {topic}
**Status**: {spec_status}

### Current Understanding
{Brief summary of spec.md}

### Open Questions
{List from state.json}

{Continue with next question or ask where to focus}
```
    </scenario>

    <scenario name="finalize" trigger="User approves spec finalization">
```markdown
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
    </scenario>
</user_output>

<error_handling>
    <scenario name="No Arguments">
        Prompt user for a topic to begin a new spec session.
    </scenario>
    <scenario name="Session ID Not Found">
        Inform user the session wasn't found, offer to create a new session instead.
    </scenario>
    <scenario name="Finalize Without Required Content">
        List missing required sections and continue question-driven exploration.
    </scenario>
    <scenario name="Finalize Without Session ID">
        Inform user that a session ID is required to finalize.
    </scenario>
</error_handling>
