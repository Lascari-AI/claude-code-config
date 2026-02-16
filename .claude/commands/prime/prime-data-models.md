---
description: Gain understanding of session data architecture - filesystem vs database ownership, sync strategies, and data models
---

# Prime Data Models

Read the session data architecture and actual database models to understand how data flows between filesystem and database.

## Read

# ACTUAL DATABASE MODELS (Source of Truth)
apps/core/session_db/models.py

# Frontend Drizzle schema (generated from Python models)
apps/core/frontend/src/db/schema.ts

# Architecture documentation
docs/.drafts/agent-architecture/85-session-data-architecture.md

# Session phases (for context on what gets stored)
docs/.drafts/agent-architecture/core-session-phases/20-spec.md
docs/.drafts/agent-architecture/core-session-phases/30-plan.md

# Example state.json (filesystem format)
.claude/skills/session/spec/templates/state.json

## Report

Summarize your understanding of:

1. **Data Ownership**: What lives in filesystem vs database and why
2. **Key Models**: Project, Session, Agent, AgentLog - their fields and relationships
3. **Sync Strategy**: How data moves between filesystem and database
4. **The Gap**: Current state vs desired state for session visibility
5. **state.json vs Session table**: Field mapping and source of truth
