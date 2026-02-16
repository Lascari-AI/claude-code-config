---
name: orch_scout_and_build
description: Scout a codebase problem with a fast analyzer, then build the solution with a specialized implementation agent.
argument-hint: [problem-description]
---

# Purpose

Scout a codebase problem or research request with a fast analyzer agent, capture their detailed findings, then delegate the implementation to a specialized build agent. This two-phase approach ensures thorough analysis before implementation.

## Variables

PROBLEM_DESCRIPTION: $1
SLEEP_INTERVAL: 15 seconds
SCOUT_AGENT_NAME: (will be generated based on problem)
BUILD_AGENT_NAME: (will be generated based on problem)

## Instructions

- You can know a task is completed when you see an `agent_logs` from `check_agent_status` that has a `response` event_category followed by a `hook` with a `Stop` event_type.
- Run this workflow for BOTH agents in sequence. Complete the scout phase entirely before starting the build phase.
- The scout agent provides READ-ONLY analysis. The build agent performs the actual implementation.
- Do NOT delete agents after completion - leave them for inspection, debugging and prompt continuations.
- Pass the scout's findings to the build agent as context for implementation.
- Use the same `problem-keyword` for both agents so we know they are related.
- When you command each agent, instruct them to use thinking mode with the 'ultrathink' keyword in your prompt.

## Workflow

### Phase 1: Scout (Analysis)

- **(Create Scout)** First run `create_agent` to create a scout agent using the `scout-report-suggest-fast` subagent_template based on the `PROBLEM_DESCRIPTION`
  - Name the agent something descriptive like "scout-{problem-keyword}"
  - The agent should be configured for read-only analysis
- **(Command Scout)** Then run `command_agent` to command the scout agent to investigate and analyze the `PROBLEM_DESCRIPTION`
  - Instruct the agent to provide a detailed scout report with findings and suggested resolutions
- **(Check Scout)** The scout agent will work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the scout's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
  - Continue checking until you see a `response` event_category followed by a `hook` with a `Stop` event_type
- **(Report Scout)** Once the scout has completed, retrieve and analyze their findings from the agent logs.
  - Extract key information: affected files, root causes, suggested resolutions
  - Communicate the scout's findings to the user

### Phase 2: Build (Implementation)

- **(Create Build Agent)** Run `create_agent` to create a build agent using the `build-agent` subagent_template
  - Name the agent something descriptive like "build-{problem-keyword}"
  - The agent should be configured for implementation work
- **(Command Build Agent)** Then run `command_agent` to command the build agent to implement the solution
  - Provide the build agent with:
    - The original `PROBLEM_DESCRIPTION`
    - The scout agent's detailed findings and recommendations
    - Specific files to modify based on scout's analysis
  - Instruct the build agent to implement the resolution following the scout's suggestions
- **(Check Build Agent)** The build agent will work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the build agent's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
  - Continue checking until you see a `response` event_category followed by a `hook` with a `Stop` event_type
- **(Report Build)** Once the build agent has completed, report the implementation results to the user.

### Final Report

- **(Summary)** Provide a complete summary to the user:
  - Scout phase results: what was analyzed and discovered
  - Build phase results: what was implemented and how
  - Both agents are available for inspection (not deleted)
  - Any follow-up recommendations or next steps

## Report

Communicate to the user where you are at each step of the workflow:

1. **Scout Phase Starting**: "Creating scout agent to analyze {PROBLEM_DESCRIPTION}..."
2. **Scout Working**: "Scout agent is analyzing the codebase... (checking every {SLEEP_INTERVAL} seconds)"
3. **Scout Complete**: "Scout analysis complete. Key findings: [summary of scout's report]"
4. **Build Phase Starting**: "Creating build agent to implement the solution..."
5. **Build Working**: "Build agent is implementing changes... (checking every {SLEEP_INTERVAL} seconds)"
6. **Build Complete**: "Implementation complete. Changes made: [summary of build agent's work]"
7. **Final Summary**: "Scout-and-build workflow complete. Scout agent '{SCOUT_AGENT_NAME}' and build agent '{BUILD_AGENT_NAME}' are both available for inspection."
