---
name: orch_one_shot_agent
description: Create and command an agent to accomplish a small task then delete the agent when the task is complete.
argument-hint: [task]
---

# Purpose

Create and command an agent to accomplish a small task then delete the agent when the task is complete.

## Variables

TASK: $1
SLEEP_INTERVAL: 10 seconds

## Instructions

- You can know a task is completed when you see a `agent_logs` from `check_agent_status` that has a `response` event_category followed by a `hook` with a `Stop` event_type.
- Run this workflow for ONLY this agent. This is not a pattern we want to use for other agents unless you're asked to do so.

## Workflow

- (Create) First run `create_agent` to create the agent based on the `TASK`
- (Command) Then run `command_agent` to command the agent to accomplish the `TASK`
- (Check) The agent will then work in the background. While it works use `Bash(sleep ${SLEEP_INTERVAL})` and every `SLEEP_INTERVAL` seconds run `check_agent_status` to check on the agent's progress.
  - If you're interrupted with an additional task, make sure you return to your sleep + check loop after you've completed the additional task.
- (Delete) Once the agent has fully completed it's task AND it's followed by a `hook` with a `Stop` event_type (very important), run `interrupt_agent` and then `delete_agent` to delete the agent.
- (Report) When you finish, report the work done by the agent to the user.

## Report

Communicate to the user where you are at each step of the workflow.
