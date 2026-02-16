---
allowed-tools: Bash, Read, Grep, Glob, TodoWrite
description: Answer questions about database schema, models, and operations without coding
argument-hint: [question]
---

# Database Expert - Question Mode

Answer the user's question by analyzing the PostgreSQL database implementation, schema, and data models in this multi-agent orchestration system. This prompt is designed to provide information about the data layer without making any code changes.

## Variables

USER_QUESTION: $1
EXPERTISE_PATH: .claude/commands/experts/database/expertise.yaml

## Instructions

- IMPORTANT: This is a question-answering task only - DO NOT write, edit, or create any files
- Focus on database schema, Pydantic models, asyncpg operations, and migration patterns
- If the question requires schema changes, explain the migration steps conceptually without implementing
- With your expert knowledge, validate the information from `EXPERTISE_PATH` against the codebase before answering your question.

## Workflow

- Read the `EXPERTISE_PATH` file to understand database architecture and patterns
- Review, validate, and confirm information from `EXPERTISE_PATH` against the codebase
- Respond based on the `Report` section below.

## Report

- Direct answer to the `USER_QUESTION`
- Supporting evidence from `EXPERTISE_PATH` and the codebase
- References to the exact files and lines of code that support the answer
- High-mid level conceptual explanations of the data architecture and patterns
- Include schema diagrams (mermaid) or SQL snippets where appropriate to streamline communication