---
description: Gain deep understanding of Claude Agent SDK, multi-agent patterns, and orchestration systems
---

# Prime Thinking

Build comprehensive understanding of the LAI Claude Code Config agent architecture - what we're trying to build and how the pieces fit together.

## Read

### Agent Architecture (Draft - This is what we're building)
Read all files in `docs/.drafts/agent-architecture/*`:
- 00-overview.md - System-level view, agent taxonomy, session types
- 05-vision.md - Vision and goals
- 10-onboarding.md - Project onboarding and docbase setup
- 20-spec.md - SPEC phase: defining intent
- 30-plan.md - PLAN phase: designing implementation
- 40-build.md - BUILD phase: executing checkpoints
- 50-docs-update.md - DOCS phase: updating documentation
- 60-research.md - Research system
- 70-agent-definitions.md - Individual agent specifications
- 80-end-to-end-flow.md - Complete workflow examples

### Understanding Documents
Read all files in `reference/understandings/*`:
- orch-w-adws-understanding.md - Multi-agent orchestration patterns with AI Developer Workflows
- automaker-understanding.md - Claude Agent SDK integration patterns in autonomous development

## Be Aware Of

### Claude Agent SDK Documentation
Located at `ai_docs/claude_agent_sdk/`:
- sessions.md, hooks.md, python.md, custom-tools.md, skills.md, structured-outputs.md, subagents.md, slash-commands.md

This is the underlying SDK we'll use to build the architecture. Read these when you need implementation details.

### Orchestrator 3 Stream App Docs
Located at `reference/orchestrator-agent-with-adws/apps/orchestrator_3_stream/app_docs/`:
- Full-stack architecture documentation (Vue 3 + FastAPI + PostgreSQL)
- Backend and frontend structure summaries
- WebSocket event patterns
- Database schema design

This is a reference implementation of a multi-agent orchestrator. Useful for understanding how the SDK gets used in practice.

### Agents and Tools Documentation
Located at `ai_docs/agents_and_tools/`:
- Skills development best practices
- Cost tracking patterns
- Tool writing guidelines

## Report

After reading, provide a unified summary covering:

1. **Vision & Purpose** - What we're building and why (from foundation + agent architecture)
2. **Session Workflow** - The spec → plan → build → docs lifecycle
3. **Agent Taxonomy** - Orchestrator, docs agents, session agents, utility agents
4. **Open Questions** - What's still being figured out
5. **Implementation Patterns** - How the reference implementations (understanding docs) inform our approach
