---
description: Update documentation at end of session - agent determines what needs updating
argument-hint: <session-id>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(eza:*), Bash(tree:*), Bash(git:log), Bash(git:diff), AskUserQuestion
model: opus
---

# Docs Update

Update documentation at the end of a session after build + tests pass.

<purpose>
    - Update documentation to reflect code changes made during an agent session
    - Intelligently determine WHAT (if anything) needs updating based on change significance
    - Use docs-framework skill knowledge to make good documentation decisions
    - Track documentation updates in session state for traceability
</purpose>

<key_knowledge>
    - docs-framework skill: `.claude/skills/docs-framework/SKILL.md`
    - Maintain cookbook: `.claude/skills/docs-framework/10-cookbook/30-maintain.md`
    - Write workflow: `.claude/skills/docs-framework/30-workflows/50-write.md`
    - Annotate workflow: `.claude/skills/docs-framework/30-workflows/60-annotate.md`
    - Documentation layers: L2/L3 (codebase docs), L4 (file headers), L5 (function docstrings)
</key_knowledge>

<goal>
    - Ensure documentation stays aligned with code after session changes
    - Record what was updated (or explicitly note when no updates needed)
    - Complete the documentation cleanup phase of the session lifecycle
</goal>

<background>
    - This is the documentation cleanup phase at the END of a session
    - Runs AFTER build + tests pass, not per-checkpoint
    - NOT every session needs doc updates - agent determines significance
    - Rely on model intelligence + docs-framework skill, NOT prescriptive rules
    - Agent has knowledge to make good decisions about what needs documentation
</background>

<workflow>
    <overview>
        1. Load session context (state, spec, commits)
        2. Analyze changes to understand scope and significance
        3. Determine what documentation needs updating (if any)
        4. Execute updates using docs-framework workflows
        5. Update session state with doc_updates record
    </overview>

    <inputs>
        <input name="$1" type="string" required="true">
            Session ID - identifies the session directory in agents/sessions/
        </input>
    </inputs>

    <variables>
        - SESSIONS_DIR = agents/sessions
        - SESSION_PATH = SESSIONS_DIR/$1
    </variables>

    <phase id="1" name="load_session">
        <description>Load session context to understand what was built</description>
        <actions>
            <action>Read SESSION_PATH/state.json - get commits array and session metadata</action>
            <action>Read SESSION_PATH/spec.md - understand the "what" and "why"</action>
            <action>Extract commit SHAs from state.json commits array</action>
        </actions>
    </phase>

    <phase id="2" name="analyze_changes">
        <description>Understand the scope and significance of changes</description>
        <actions>
            <action>For each commit, examine the diff:
                ```bash
                git diff {sha}^..{sha} --stat
                git diff {sha}^..{sha}
                ```
            </action>
            <action>Build mental model of:
                - What files changed
                - What kind of changes (new features, refactors, fixes, chores)
                - The scope and significance
            </action>
        </actions>
    </phase>

    <phase id="3" name="determine_doc_needs">
        <description>Decide what documentation updates are needed (if any)</description>
        <decision_framework>
            <criterion name="Needs docs?" guidance="Use judgment based on change type">
                - Significant new feature? → Yes
                - Behavioral changes? → Yes
                - Refactor that restructures code? → Probably yes
                - Variable rename or simple fix? → Probably no
                - Dead code removal? → Probably no
                - Chore/cleanup? → No
            </criterion>
            <criterion name="What level?" guidance="Match doc layer to change type">
                - L2/L3 (Codebase docs): Significant features, architectural changes
                - L4 (File headers): Files with changed purpose, significant updates
                - L5 (Function docstrings): New/changed functions with complex behavior
            </criterion>
        </decision_framework>
        <actions>
            <action>Present analysis using AskUserQuestion:
                ```
                ## Doc Update Analysis

                **Session**: {session-id}
                **Commits analyzed**: {count}

                **Recommendation**: [Update needed / No update needed]

                **Reasoning**:
                - {explanation of what changed and why docs do/don't need updating}

                **Proposed updates** (if any):
                - [ ] L2/L3: {path} - {reason}
                - [ ] L4/L5: {path} - {reason}
                ```
            </action>
            <action>Ask user to confirm:
                - "Proceed with updates" → Continue to phase 4
                - "No updates needed" → Skip to phase 5 (record no updates)
                - "Adjust plan" → Refine what to update
            </action>
        </actions>
    </phase>

    <phase id="4" name="execute_updates">
        <description>Make documentation updates using docs-framework workflows</description>
        <condition>Only execute if updates were approved in phase 3</condition>
        <actions>
            <action>For L2/L3 codebase docs:
                - Load: `.claude/skills/docs-framework/30-workflows/50-write.md`
                - Use spec.md as implementation notes context
                - Follow the write workflow steps
            </action>
            <action>For L4/L5 code annotations:
                - Load: `.claude/skills/docs-framework/30-workflows/60-annotate.md`
                - Follow the annotate workflow steps
            </action>
            <action>Show each change before making it - user confirms each doc update</action>
        </actions>
    </phase>

    <phase id="5" name="update_state">
        <description>Record documentation updates in session state</description>
        <actions>
            <action>Update SESSION_PATH/state.json doc_updates array:
                ```json
                {
                  "doc_updates": [
                    {
                      "type": "L2" | "L3" | "L4" | "L5" | "none",
                      "path": "docs/10-codebase/..." or "src/...",
                      "description": "Brief description of what was updated",
                      "created_at": "ISO timestamp"
                    }
                  ]
                }
                ```
            </action>
            <action>If no updates needed, record explicitly:
                ```json
                {
                  "type": "none",
                  "description": "No doc updates needed - {brief reason}",
                  "created_at": "ISO timestamp"
                }
                ```
            </action>
        </actions>
    </phase>

    <global_constraints>
        - Rely on model intelligence - don't force docs where not needed
        - Show work to user - let them see analysis and approve changes
        - Use docs-framework workflows for actual updates
        - Always record outcome in state.json (even if "none")
    </global_constraints>

    <output_format>
        Report completion to user:
        ```markdown
        ## Docs Update Complete ✅

        **Session**: {session-id}
        **Updates made**: {count}

        ### Summary
        {list of what was updated, or "No documentation updates were needed for this session"}

        ### Next
        Session documentation cleanup phase complete.
        ```
    </output_format>
</workflow>

<important_rules>
    1. NOT every session needs doc updates - explicitly deciding "no updates needed" is a valid outcome
    2. Use the docs-framework skill workflows for actual documentation changes
    3. ALWAYS record the outcome in state.json doc_updates (even if empty/none)
</important_rules>
