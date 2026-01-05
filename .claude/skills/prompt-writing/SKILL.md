---
name: prompt-writing
description: Generate AI-consumable artifacts (prompts, workflows, commands, etc.). Triggers when writing prompts, system instructions, agent definitions, or anything sent to an AI for processing. Produces Markdown+XML for system prompts and Python for user prompt formatters.
---

# Purpose

Generate production-quality AI artifacts following a principled, story-driven approach.
Follow the `Instructions`, execute the `Workflow`, based on the `Cookbook`.

## Variables

SKILL_ROOT: .claude/skills/prompt-writing/

## Instructions

- Based on the user's request, follow the `Cookbook` to determine which workflow to execute.

## File Format

**All prompt artifacts are Markdown files (.md) that use XML tags for structure.**

- File extension: `.md` (NOT `.xml`)
- Internal structure: XML tags within markdown
- Why: Markdown provides flexibility; XML tags provide clear structural boundaries the model can parse

```
CORRECT:  my-agent.md     (markdown file with XML tags inside)
WRONG:    my-agent.xml    (actual XML file)
```

This approach gives you the best of both worlds—human-readable markdown with the structural clarity of XML tags.

## Workflow

1. Understand the user's request and what type of prompt artifact they need.
2. Follow the `Cookbook` to load the appropriate workflow.
3. Execute the workflow steps from the loaded file.

## Cookbook

### Static Instructions

- IF: Writing static instructions that define AI behavior (system prompts, commands, skills, agent definitions, workflow files, directives)
- THEN: Read and execute: `system_prompt/00-overview.md`
- EXAMPLES:
  - "Write a system prompt for a code reviewer"
  - "Create a Claude Code skill for committing changes"
  - "Build an agent that analyzes customer feedback"
  - "Define a workflow for data processing"
  - "Write a command that gets handed off to a background agent"
  - "Create a single-completion prompt for classification"

### User Prompt

- IF: Formatting dynamic context to send to an LLM (converting state/data into structured user prompt, Python formatters, runtime context assembly)
- THEN: Read and execute: `user_prompt/00-overview.md`
- EXAMPLES:
  - "Write a user prompt formatter for this agent"
  - "Create a Python function to format the context"
  - "Build the dynamic context assembly for this workflow"
  - "Format conversation history for the prompt"
  - "Structure the runtime data as XML for the user message"
