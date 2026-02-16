---
allowed-tools: Bash, Read, TodoWrite
description: Answer questions about websocket management in this codebase without coding
argument-hint: [question]
---

# Websocket Expert - Question Mode

Answer the user's question by analyzing websocket implementation, architecture, and patterns in this multi-agent orchestration system. This prompt is designed to provide information about websocket management without making any code changes.

## Variables

USER_QUESTION: $1
EXPERTISE_PATH: .claude/commands/experts/websocket/expertise.yaml

## Instructions

- IMPORTANT: This is a question-answering task only - DO NOT write, edit, or create any files
- Focus on websocket connection management, streaming, and real-time communication patterns
- If the question requires code changes, explain what would need to be done conceptually without implementing
- With your expert knowledge, validate the information from `EXPERTISE_PATH` against the codebase before answering your question.

## Workflow

- Read the `EXPERTISE_PATH` file to understand websocket architecture and patterns
- Review, validate, and confirm information from `EXPERTISE_PATH` against the codebase
- Respond based on the `Report` section below.

## Report

- Direct answer to the `USER_QUESTION`
- Supporting evidence from `EXPERTISE_PATH` and the codebase
- References to the exact files and lines of code that support the answer
- High-mid level conceptual explanations of the websocket architecture and patterns
- Include diagrams where appropriate to streamline communication