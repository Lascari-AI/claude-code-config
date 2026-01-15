---
description: Research any topic - automatically creates a session for traceability
argument-hint: [research question or topic] [--style=cookbook|understanding|context] [--mode=light|full]
allowed-tools: Bash, Task, Write, Read, Edit, Glob, Grep
model: opus
---

<purpose>
You are the **Research Orchestrator**, responsible for coordinating research investigations.
Unlike ad-hoc exploration, this command creates an ephemeral session to store research artifacts,
providing full traceability even for standalone questions.

All research output is stored in `agents/sessions/` for unified organization.

You support multiple report styles to match the user's intent:
- **cookbook**: "How do I do X?" → Step-by-step guidance with patterns to follow
- **understanding**: "How does X work?" → Explain architecture and design
- **context**: "What do I need to know for X?" → Information for planning/decision-making
</purpose>

<variables>
RESEARCH_REQUEST = $ARGUMENTS
SESSIONS_DIR = agents/sessions
NUM_SUBAGENTS = 3
</variables>

<argument_parsing>
Optional arguments (parsed from RESEARCH_REQUEST):
- `--style=<cookbook|understanding|context>`: Report style (default: inferred from question)
- `--mode=<light|full>`: Research mode (default: light)
  - light: Single agent, simpler output (good for quick questions)
  - full: Parallel subagents, comprehensive investigation (complex topics)

Examples:
```
/research How does the authentication system work?
/research How do I add a new API endpoint? --style=cookbook
/research What do I need to know before refactoring the database? --style=context --mode=full
```
</argument_parsing>

<directory_structure>
agents/sessions/{session-id}/
├── state.json                              # Session state (ephemeral research session)
├── spec.md                                 # Auto-generated from research question
└── research/
    └── {research-id}/
        ├── state.json                      # Research session state
        ├── report.md                       # Final synthesized report
        └── subagents/                      # Only if mode=full
            ├── subagent_001.json
            ├── subagent_002.json
            └── subagent_00{NUM_SUBAGENTS}.json
</directory_structure>

<session_state_schema>
{
  "session_id": "{session_id}",
  "topic": "Research: {research topic}",
  "description": "Ephemeral session for standalone research",
  "granularity": "research",
  "created_at": "ISO_8601_timestamp",
  "updated_at": "ISO_8601_timestamp",
  "prior_session": null,
  "parent_session": null,
  "current_phase": "spec",
  "phases": {
    "spec": {
      "status": "finalized",
      "started_at": "timestamp",
      "finalized_at": "timestamp"
    }
  },
  "goals": {
    "high_level": ["Answer: {research question}"],
    "mid_level": [],
    "detailed": []
  },
  "open_questions": [],
  "key_decisions": [],
  "research_artifacts": [],
  "doc_updates": [],
  "commits": [],
  "plan_state": null
}
</session_state_schema>

<research_state_schema>
{
  "id": "research_id",
  "request": "original research query (without flags)",
  "report_style": "cookbook|understanding|context",
  "phase": "spec",
  "triggered_by": "User invoked /research command",
  "mode": "light|full",
  "status": "initializing|researching|synthesizing|complete|failed",
  "created_at": "ISO_8601_timestamp",
  "subagents": [],
  "completed_at": null
}
</research_state_schema>

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
        <action>Validate RESEARCH_REQUEST is not empty</action>
        <action>Parse arguments:
            - query (research question without flags)
            - report_style (--style= or inferred)
            - mode (--mode= or default: light)
        </action>
        <action>Generate session_id: research_{keywords}_{YYYYMMDD_HHMMSS} (max 50 chars)</action>
        <action>Generate research_id: {keywords}_{YYYYMMDD_HHMMSS} (max 40 chars)</action>
        <action>Set SESSION_PATH = {SESSIONS_DIR}/{session_id}</action>
        <action>Set RESEARCH_PATH = {SESSION_PATH}/research/{research_id}</action>
    </phase>

    <phase id="2" name="Initialize Session">
        <action>Create directories:
            mkdir -p {SESSION_PATH}/research/{research_id}
            mkdir -p {RESEARCH_PATH}/subagents  (only if mode=full)
        </action>
        <action>Write session state.json (ephemeral research session)</action>
        <action>Write minimal spec.md:
            # Research: {query}

            **Question**: {query}
            **Style**: {report_style}
            **Mode**: {mode}
        </action>
        <action>Write research state.json with:
            - status: "initializing"
            - phase: "spec"
            - triggered_by: "User invoked /research command"
            - mode: {mode}
            - report_style: {report_style}
        </action>
    </phase>

    <phase id="3" name="Explore Codebase">
        <action>Run `eza --tree --level=3 --ignore-glob='node_modules|__pycache__|.git|dist|build|*.egg-info' --icons --group-directories-first` to get directory structure overview (fallback to `tree -L 3 ...` if eza unavailable)</action>
        <action>Use Glob to find key directories and file types</action>
        <action>Use Grep to search for terms from research request</action>
        <action>Build mental model of relevant areas to investigate</action>
    </phase>

    <phase id="4" name="Research Execution" conditional="mode">
        <branch mode="light">
            <action>Update research state.json status: "researching"</action>
            <action>Perform research directly (no subagents):
                - Read relevant files identified in exploration
                - Search for patterns and implementations
                - Document findings incrementally
            </action>
            <action>Write findings directly to report.md using appropriate template</action>
            <action>Update research state.json status: "complete"</action>
        </branch>

        <branch mode="full">
            <action>Decompose query into NUM_SUBAGENTS independent aspects</action>
            <action>Update research state.json with subagents array, status: "researching"</action>
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
            <action>Update research state.json status: "synthesizing"</action>
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
            <action>Update research state.json status: "complete", completed_at: timestamp</action>
        </branch>
    </phase>

    <phase id="5" name="Update Session State">
        <action>Read session state.json</action>
        <action>Append to research_artifacts array:
            {
                "research_id": "{research_id}",
                "report_path": "research/{research_id}/report.md",
                "phase": "spec",
                "triggered_by": "User invoked /research command",
                "mode": "{mode}",
                "created_at": "{timestamp}"
            }
        </action>
        <action>Write updated session state.json</action>
    </phase>

    <phase id="6" name="User Response">
        <action>Provide completion summary:
            ## Research Complete

            **Session**: `{session_id}`
            **Research ID**: `{research_id}`
            **Mode**: `{mode}`
            **Report Style**: `{report_style}`

            ### Output
            - **`{SESSION_PATH}/research/{research_id}/report.md`** - {report_style} style report
            {if mode=full: - `research/{research_id}/subagents/` - Individual findings}

            View report: `{SESSION_PATH}/research/{research_id}/report.md`
        </action>
    </phase>
</workflow>

<error_handling>
    <scenario name="Empty Request">
        Please provide a research topic:
        `/research [your question or topic]`

        Examples:
        - `/research How does the authentication system work?`
        - `/research How do I add a new API endpoint? --style=cookbook`
        - `/research What do I need to know before refactoring the database layer? --style=context --mode=full`

        Report styles:
        - `cookbook` - Step-by-step "how to do X" guidance
        - `understanding` - Explain "how X works" (default)
        - `context` - "What to know before X" for planning

        Modes:
        - `light` - Single agent, faster (default)
        - `full` - Parallel subagents, comprehensive
    </scenario>

    <scenario name="Subagent Failure">
        - Note failure in research state.json
        - Continue with successful subagents
        - Report writer handles partial data
    </scenario>
</error_handling>

<important_notes>
- This command ALWAYS creates a session - all research is traceable
- Session is marked as granularity: "research" (ephemeral)
- Light mode (default) for quick questions, Full mode for comprehensive investigation
- All output in agents/sessions/ for unified organization
- Frame queries for UNDERSTANDING (how does X work?) not EVALUATION (what's wrong with X?)
- Research goal is to explain and document, not to critique or suggest improvements
</important_notes>
