---
description: Gain a full understanding of the session system for spec/plan/build workflow
---

# Prime Session

Read all session files to understand the spec/plan/build workflow system.

## Read

.claude/skills/session/SKILL.md
.claude/commands/session/spec.md
.claude/commands/session/plan.md
.claude/skills/session/spec/templates/state.json
.claude/skills/session/spec/templates/spec.md
.claude/skills/session/plan/templates/plan.md

## Report

Summarize your understanding of the session system including:

1. **Purpose**: The spec → plan → build workflow philosophy
2. **Spec Mode**: How requirements are gathered through question-driven exploration
3. **Plan Mode**: How implementation plans are created from finalized specs
4. **Session Management**: How sessions are created, tracked, and resumed via $1/$2 arguments
5. **Directory Structure**: How SESSIONS_DIR and TEMPLATES_DIR organize session data
6. **State Tracking**: How state.json manages phase transitions and progress
7. **Templates**: The structure of spec.md, plan.md, and state.json templates
8. **Finalization Flow**: How specs and plans are finalized and handed off
