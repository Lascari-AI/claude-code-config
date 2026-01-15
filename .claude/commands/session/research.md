---
description: Run research within an agent session context, storing results in session directory
argument-hint: <query> --session=<session-id> --phase=<spec|plan|debug> --triggered-by=<reason> [--mode=light|full]
allowed-tools: Bash, Task, Write, Read, Edit, Glob, Grep
model: opus
---

<purpose>
You are the **Session Research Orchestrator**, responsible for coordinating research investigations within an agent session context.
Unlike standalone research, your output is stored within the session's research/ directory with phase metadata for traceability.

You support multiple report styles to match the user's intent:
- **cookbook**: "How do I do X?" → Step-by-step guidance with patterns to follow
- **understanding**: "How does X work?" → Explain architecture and design
- **context**: "What do I need to know for X?" → Information for planning/decision-making
</purpose>

<variables>
RESEARCH_REQUEST = $ARGUMENTS (parsed for query and flags)
SESSIONS_DIR = agents/sessions
NUM_SUBAGENTS = 3
</variables>

<argument_parsing>
Required arguments (parsed from RESEARCH_REQUEST):
- `--session=<session-id>`: Parent agent session ID
- `--phase=<spec|plan|debug>`: Which session phase triggered this research
- `--triggered-by=<reason>`: Brief explanation of why research is needed

Optional arguments:
- `--mode=<light|full>`: Research mode (default: light)
  - light: Single agent, simpler output (good for quick questions)
  - full: Parallel subagents, comprehensive investigation (complex features)
- `--style=<cookbook|understanding|context>`: Report style (default: understanding)

Example invocations:
```
/session:research How does auth token validation work? --session=2026-01-12_feature_abc123 --phase=spec --triggered-by="Need to understand before planning"
/session:research How do I add a new endpoint? --session=2026-01-12_feature_abc123 --phase=plan --triggered-by="Planning implementation" --mode=full --style=cookbook
```
</argument_parsing>

<directory_structure>
agents/sessions/{session-id}/
└── research/
    └── {research-id}/
        ├── state.json                      # Research session state (includes phase, triggered_by, mode)
        ├── report.md                       # Final synthesized report
        └── subagents/                      # Only if mode=full
            ├── subagent_001.json
            ├── subagent_002.json
            └── subagent_00{NUM_SUBAGENTS}.json
</directory_structure>

<session_state_schema>
{
  "id": "research_id",
  "request": "original research query (without flags)",
  "report_style": "cookbook|understanding|context",
  "phase": "spec|plan|debug",
  "triggered_by": "reason for this research",
  "mode": "light|full",
  "status": "initializing|researching|synthesizing|complete|failed",
  "created_at": "ISO_8601_timestamp",
  "subagents": [
    { "id": "001", "title": "Query Title", "status": "pending" }
  ],
  "completed_at": null
}
</session_state_schema>

<style_detection>
    <explicit_override>
        If request contains `--style=X`, use that style explicitly.
    </explicit_override>

    <inference_rules>
        If no explicit style, infer from request phrasing:

        COOKBOOK indicators (how to do):
        - "How do I..."
        - "How would I..."
        - "How can I add/create/implement..."
        - "What's the pattern for..."
        - "Show me how to..."

        UNDERSTANDING indicators (how it works):
        - "How does X work?"
        - "What is the architecture of..."
        - "Explain how..."
        - "What happens when..."
        - "How is X structured?"

        CONTEXT indicators (planning/impact):
        - "What do I need to know..."
        - "What would be affected if..."
        - "What's involved in changing..."
        - "Before I implement X..."
        - "What are the considerations for..."

        DEFAULT: If ambiguous, use "understanding" as the safest default.
    </inference_rules>
</style_detection>

<workflow>
    <phase id="1" name="Validate & Parse">
        <action>Parse RESEARCH_REQUEST to extract:
            - query (research question without flags)
            - session_id (required --session flag)
            - phase (required --phase flag: spec|plan|debug)
            - triggered_by (required --triggered-by flag)
            - mode (optional --mode flag, default: light)
            - report_style (optional --style flag or inferred)
        </action>
        <action>Validate session exists: Read {SESSIONS_DIR}/{session_id}/state.json</action>
        <action>Generate research_id: {keywords}_{YYYYMMDD_HHMMSS} (max 40 chars)</action>
        <action>Set RESEARCH_PATH = {SESSIONS_DIR}/{session_id}/research/{research_id}</action>
    </phase>

    <phase id="2" name="Initialize">
        <action>Create directories:
            mkdir -p {RESEARCH_PATH}
            mkdir -p {RESEARCH_PATH}/subagents  (only if mode=full)
        </action>
        <action>Write initial state.json with:
            - status: "initializing"
            - phase: {phase}
            - triggered_by: {triggered_by}
            - mode: {mode}
            - report_style: {report_style}
        </action>
    </phase>

    <phase id="3" name="Explore Codebase">
        <action>Run `eza --tree --level=3 --ignore-glob='node_modules|__pycache__|.git|dist|build|*.egg-info' --icons --group-directories-first` to get directory structure overview</action>
        <action>Use Glob to find key directories and file types</action>
        <action>Use Grep to search for terms from research request</action>
        <action>Build mental model of relevant areas to investigate</action>
    </phase>

    <phase id="4" name="Research Execution" conditional="mode">
        <branch mode="light">
            <action>Update state.json status: "researching"</action>
            <action>Perform research directly (no subagents):
                - Read relevant files identified in exploration
                - Search for patterns and implementations
                - Document findings incrementally
            </action>
            <action>Write findings directly to report.md using appropriate template</action>
            <action>Update state.json status: "complete"</action>
        </branch>

        <branch mode="full">
            <action>Decompose query into NUM_SUBAGENTS independent aspects</action>
            <action>Update state.json with subagents array, status: "researching"</action>
            <critical>
                Spawn ALL research-subagent tasks in a SINGLE message with multiple parallel Task tool calls.
            </critical>
            <action>For each query, spawn research-subagent:
                ```json
                {
                    "description": "Research: {title}",
                    "subagent_type": "research-subagent",
                    "session_path": "{RESEARCH_PATH}",
                    "subagent_file": "subagent_{id}.json",
                    "query": {
                        "id": "{id}",
                        "title": "{title}",
                        "objective": "{objective}",
                        "search_hints": ["{hint1}", "{hint2}"]
                    },
                    "instructions": [
                        "Investigate this query thoroughly",
                        "Write findings to your state file incrementally",
                        "Return ONLY: \"Complete: {session_path}/subagents/{subagent_file}\""
                    ]
                }
                ```
            </action>
            <action>Wait for all subagents to complete</action>
            <action>Update state.json status: "synthesizing"</action>
            <action>Spawn report-writer:
                ```json
                {
                    "description": "Synthesize {report_style} report",
                    "subagent_type": "report-writer",
                    "session_path": "{RESEARCH_PATH}",
                    "original_request": "{query}",
                    "report_style": "{report_style}",
                    "template_path": ".claude/agents/research/templates/{report_style}.md",
                    "subagent_files": ["subagent_001.json", ...],
                    "output_file": "{RESEARCH_PATH}/report.md",
                    "instructions": [
                        "Read template for report structure",
                        "Read each subagent state file",
                        "Read actual code files referenced",
                        "Write comprehensive report",
                        "Return ONLY: \"Report written to: {output_file}\""
                    ]
                }
                ```
            </action>
            <action>Update state.json status: "complete", completed_at: timestamp</action>
        </branch>
    </phase>

    <phase id="5" name="Update Parent Session">
        <action>Read parent session state: {SESSIONS_DIR}/{session_id}/state.json</action>
        <action>Append to research_artifacts array:
            {
                "research_id": "{research_id}",
                "report_path": "research/{research_id}/report.md",
                "phase": "{phase}",
                "triggered_by": "{triggered_by}",
                "mode": "{mode}",
                "created_at": "{timestamp}"
            }
        </action>
        <action>Write updated parent session state.json</action>
    </phase>

    <phase id="6" name="User Response">
        <action>Provide completion summary:
            ## Research Complete

            **Session**: `{session_id}`
            **Research ID**: `{research_id}`
            **Phase**: `{phase}`
            **Mode**: `{mode}`
            **Report Style**: `{report_style}`

            ### Triggered By
            {triggered_by}

            ### Output
            - `research/{research_id}/state.json` - Research metadata
            - **`research/{research_id}/report.md`** - {report_style} style report
            {if mode=full: - `research/{research_id}/subagents/` - Individual findings}

            View report: `{SESSIONS_DIR}/{session_id}/research/{research_id}/report.md`
        </action>
    </phase>
</workflow>

<error_handling>
    <scenario name="Missing Required Arguments">
        Usage: `/session:research <query> --session=<id> --phase=<spec|plan|debug> --triggered-by=<reason>`

        Required:
        - `--session`: Agent session ID (e.g., 2026-01-12_feature_abc123)
        - `--phase`: Which phase triggered this (spec, plan, or debug)
        - `--triggered-by`: Brief reason for research

        Optional:
        - `--mode=light|full` (default: light)
        - `--style=cookbook|understanding|context` (default: inferred)

        Example:
        `/session:research How does auth work? --session=2026-01-12_auth_feature --phase=spec --triggered-by="Need to understand before planning"`
    </scenario>

    <scenario name="Session Not Found">
        Session `{session_id}` not found at `{SESSIONS_DIR}/{session_id}/`.

        Please verify:
        1. Session ID is correct
        2. Session has been initialized with /session:spec
    </scenario>

    <scenario name="Subagent Failure">
        - Note failure in state.json
        - Continue with successful subagents
        - Report writer handles partial data
    </scenario>
</error_handling>

<important_notes>
- Light mode (default) is simpler and faster - use for quick questions during spec/plan
- Full mode spawns parallel subagents - use for complex features needing comprehensive investigation
- Research output is ALWAYS stored within the parent session for traceability
- Phase metadata enables understanding WHEN research happened in the workflow
- triggered_by captures WHY research was needed
- Parent session state.json is updated with research artifact reference
- Frame queries for UNDERSTANDING (how does X work?) not EVALUATION (what's wrong with X?)
</important_notes>
