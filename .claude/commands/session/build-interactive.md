---
description: Interactive fix mode - work with user to resolve issues during build
argument-hint: [session-id]
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, AskUserQuestion
model: opus
---

<purpose>
    - Collaborative troubleshooting partner for resolving issues encountered during build phase
    - Bridge between autonomous build execution and human problem-solving intuition
    - Ensure fixes are documented for session continuity and future reference
</purpose>

<key_knowledge>
    - session state management (state.json, plan.json, dev-notes.json)
    - Build phase checkpoint/task structure and progress tracking
    - DevNotes schema and categories (deviation, discovery, decision, blocker, resolution)
    - Debugging methodology: reproduce → isolate → fix → verify
</key_knowledge>

<goal>
    - Resolve the user's reported issue through collaborative investigation
    - Document the fix in dev-notes.json for traceability
    - Return user to normal build flow with clear next steps
</goal>

<background>
    - Build phase executes autonomously but sometimes produces unexpected results
    - User needs to step out of the automated flow to address a specific problem
    - Fixes should be captured so the session maintains a complete record
    - After resolution, user resumes with `/session:build` from where they left off
</background>

<workflow>
    <overview>
        1. Load session context
        2. Ask what's wrong (user-initiated problem statement)
        3. Investigate and fix collaboratively
        4. Log resolution to dev-notes.json
        5. Return user to build flow
    </overview>

    <inputs>
        <input name="session_id" type="string" required="true">
            Session identifier (e.g., 2026-01-15_my-feature_abc123)
        </input>
    </inputs>

    <variables>
        SESSIONS_DIR = agents/sessions
    </variables>

    <phase id="1" name="Load Context">
        <action>
            - Read `SESSIONS_DIR/{session_id}/state.json`
        </action>
        <action>
            - Read `SESSIONS_DIR/{session_id}/plan.json`
        </action>
        <action>
            - Read `SESSIONS_DIR/{session_id}/dev-notes.json` (if exists)
        </action>
        <action>
            - Extract current position from `plan_state`:
                - `current_checkpoint`
                - `current_task_group`
                - `current_task`
        </action>
    </phase>

    <phase id="2" name="Ask What's Wrong">
        <critical>
            - Do NOT investigate autonomously
            - Do NOT run tests automatically
            - Do NOT make assumptions about the problem
            - WAIT for user to describe the issue
        </critical>

        <action>
            - Display current context:
                ```
                ## Build Interactive - Fix Mode

                **Session**: {session_id}
                **Position**: Checkpoint {N}, Task {X.Y.Z} - {task_title}

                ---

                **What's not working?**
                ```
        </action>
        <action>
            - Await user response describing the problem
        </action>
    </phase>

    <phase id="3" name="Investigate and Fix">
        <critical>
            - Stay interactive - confirm before each significant action
            - Show your work - display findings, proposed changes
            - Follow user's lead - they know the problem context
        </critical>

        <actions>
            <action name="investigate">
                - Use Read, Grep, Glob to explore the issue
                - Share relevant code snippets with user
                - Propose hypotheses about root cause
            </action>
            <action name="confirm">
                - Before making changes, describe what you'll do
                - Get explicit user approval
            </action>
            <action name="fix">
                - Make changes using Edit/Write tools
                - Show the resulting diff or new content
            </action>
            <action name="verify">
                - Run tests or verification commands as appropriate
                - Report results to user
            </action>
            <action name="iterate">
                - If not resolved, return to investigate
                - Continue until user confirms fix works
            </action>
        </actions>
    </phase>

    <phase id="4" name="Log Resolution">
        <action>
            - Append DevNote entry to `dev-notes.json`:
                ```json
                {
                    "id": "dn-{next_id}",
                    "timestamp": "{ISO_timestamp}",
                    "scope": { "type": "task", "ref": "{current_task_id}" },
                    "category": "resolution",
                    "content": "{Brief description of what was fixed and how}"
                }
                ```
        </action>
    </phase>

    <phase id="5" name="Return to Build">
        <action>
            - Display completion message:
                ```
                ## Issue Resolved

                **Fix**: {brief summary of what was fixed}
                **Logged**: dev-notes.json ({note_id})

                ---

                To continue building, run:
                `/session:build {session_id}`
                ```
        </action>
    </phase>

    <global_constraints>
        - NO sub-agents - execute everything directly in this conversation
        - NO autonomous investigation - always ask first, act second
        - ALWAYS log the fix to dev-notes.json before completing
        - STAY in dialogue - this is collaborative, not autonomous
    </global_constraints>
</workflow>

<important_rules>
    1. NEVER investigate or run commands before user describes the problem
    2. ALWAYS confirm approach with user before making code changes
    3. ALWAYS document the resolution in dev-notes.json
</important_rules>
