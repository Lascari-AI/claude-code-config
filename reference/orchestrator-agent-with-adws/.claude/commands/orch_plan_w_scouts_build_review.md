---
name: orch_plan_w_scouts_build_review
description: Three-phase workflow - plan the task with a custom planner, build the solution with a specialist, then validate with a reviewer.
argument-hint: [task-description]
---

# Purpose

Execute a comprehensive three-phase development workflow: first create a custom planner agent to analyze the task and design an implementation plan, then delegate building to a specialist build agent, and finally validate the work with a review agent. This ensures thorough planning, quality implementation, and comprehensive validation.

## Variables

TASK_DESCRIPTION: $1
SLEEP_INTERVAL: 15 seconds
PLANNER_AGENT_NAME: (will be generated based on task)
BUILD_AGENT_NAME: (will be generated based on task)
REVIEW_AGENT_NAME: (will be generated based on task)

## Instructions

- You can know a task is completed when you see an `agent_logs` from `check_agent_status` that has a `response` event_category followed by a `hook` with a `Stop` event_type.
- Run this workflow for ALL THREE agents in sequence. Complete each phase entirely before starting the next.
- Phase 1: Planner creates the implementation plan (custom system prompt designed by you)
- Phase 2: Build agent implements based on the plan (uses `build-agent` template)
- Phase 3: Review agent validates the work (uses `review-agent` template)
- Do NOT delete agents after completion - leave them for inspection and debugging. We might have additional work for these agents to complete.
- Pass findings from each phase to the next agent as context.
- When you command each agent, instruct them to use thinking mode with the 'ultrathink' keyword in your prompt.

## Workflow

### Setup: Create All Agents Upfront

- **(Create Planner)** Run `create_agent` to create a planner agent WITHOUT using a subagent_template
  - Name the agent something descriptive like "planner-{task-keyword}"
  - **IMPORTANT**: Design a custom system prompt for the planner based on TASK_DESCRIPTION that instructs the agent to:
    - Analyze the task requirements thoroughly
    - Explore the codebase to understand existing patterns
    - Design a detailed implementation plan
    - Identify all files that need to be created or modified
    - Specify the technical approach and architecture decisions
    - Create a structured plan document in the `specs/` directory
    - The planner should be configured with tools: Read, Glob, Grep, Write, Bash
- **(Create Build Agent)** Run `create_agent` to create a build agent using the `build-agent` subagent_template
  - Name the agent something descriptive like "builder-{task-keyword}"
  - Use the same `task-keyword` so agents are clearly related
  - The agent should be configured for file implementation work
- **(Create Review Agent)** Run `create_agent` to create a review agent using the `review-agent` subagent_template
  - Name the agent something descriptive like "reviewer-{task-keyword}"
  - Use the same `task-keyword` so agents are clearly related
  - The agent should be configured for analysis and validation work

### Phase 1: Plan (Analysis & Design)

- **(Command Planner)** Run `command_agent` to command the planner agent to analyze and plan the TASK_DESCRIPTION
  - Instruct the agent to create a comprehensive implementation plan
  - Ensure the plan includes: objective, requirements, files to modify, step-by-step tasks, acceptance criteria
- **(Check Planner)** The planner agent will work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the planner's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
  - Continue checking until you see a `response` event_category followed by a `hook` with a `Stop` event_type
- **(Report Planner)** Once the planner has completed, retrieve and analyze their plan from the agent logs.
  - Extract key information: plan location, files to modify, implementation approach
  - Read the plan file from `specs/` directory to understand the full context
  - Communicate the planner's findings to the user

### Phase 2: Build (Implementation)

- **(Command Build Agent)** Run `command_agent` to command the build agent to implement the solution
  - Provide the build agent with:
    - The original TASK_DESCRIPTION
    - The planner's detailed plan (reference the plan file path)
    - Specific files to create/modify based on planner's analysis
    - Implementation approach from the plan
  - Instruct the build agent to implement the solution following the plan's specifications
- **(Check Build Agent)** The build agent will work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the build agent's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
  - Continue checking until you see a `response` event_category followed by a `hook` with a `Stop` event_type
- **(Report Build)** Once the build agent has completed, report the implementation results to the user.
  - Extract what was built from the agent logs
  - Note any files created or modified
  - Communicate build completion and key deliverables

### Phase 3: Review (Validation)

- **(Command Review Agent)** Run `command_agent` to command the review agent to validate the work
  - Provide the review agent with:
    - The original TASK_DESCRIPTION
    - The planner's plan for comparison
    - Instructions to analyze git diffs and validate implementation
    - Request a risk-tiered report (Blockers, High Risk, Medium Risk, Low Risk)
  - Instruct the review agent to produce a comprehensive validation report
- **(Check Review Agent)** The review agent will work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the review agent's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
  - Continue checking until you see a `response` event_category followed by a `hook` with a `Stop` event_type
- **(Report Review)** Once the review agent has completed, report the validation results to the user.
  - Extract the review findings from agent logs
  - Note the location of the review report
  - Communicate PASS/FAIL verdict and any critical issues
  - Highlight any blockers that need immediate attention

### Final Report

- **(Summary)** Provide a complete summary to the user:
  - Plan phase results: what was planned and where the plan is located
  - Build phase results: what was implemented and which files were modified
  - Review phase results: validation verdict and any issues found
  - All three agents are available for inspection (not deleted)
  - Any follow-up recommendations or next steps based on review findings

## Report

Communicate to the user where you are at each step of the workflow:

1. **Setup Starting**: "Creating planner, builder, and reviewer agents for {TASK_DESCRIPTION}..."
2. **Setup Complete**: "Agents created: Planner '{PLANNER_AGENT_NAME}', builder '{BUILD_AGENT_NAME}', and reviewer '{REVIEW_AGENT_NAME}'"
3. **Plan Phase Starting**: "Commanding planner agent to analyze and design implementation..."
4. **Plan Working**: "Planner agent is analyzing the task and designing the implementation plan... (checking every {SLEEP_INTERVAL} seconds)"
5. **Plan Complete**: "Planning complete. Implementation plan saved to: [plan-file-path]. Key approach: [summary of technical approach]"
6. **Build Phase Starting**: "Commanding build agent to implement the solution based on the plan..."
7. **Build Working**: "Build agent is implementing the solution... (checking every {SLEEP_INTERVAL} seconds)"
8. **Build Complete**: "Implementation complete. Files modified: [list of files]. Key changes: [summary of what was built]"
9. **Review Phase Starting**: "Commanding review agent to validate the implementation..."
10. **Review Working**: "Review agent is analyzing changes and validating work... (checking every {SLEEP_INTERVAL} seconds)"
11. **Review Complete**: "Review complete. Verdict: [PASS/FAIL]. Report location: [review-report-path]. Issues found: [count by risk tier]"
12. **Final Summary**: "Three-phase workflow complete. All agents are available for inspection. [Final recommendation based on review verdict]"
