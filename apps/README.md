# Apps Directory

This directory contains applications for the LAI Claude Code Config system.

## Structure

```
apps/
├── core/                    # Core orchestration infrastructure
│   ├── session_db/          # Database models and operations
│   ├── api/                  # (future) FastAPI backend
│   └── orchestrator/         # (future) Agent orchestration service
│
└── {symlinked-projects}/    # External projects managed by the system
```

## Core Apps

The `core/` directory contains the infrastructure that powers the orchestration system:

- **session_db**: SQLModel-based PostgreSQL database for tracking sessions, agents, and execution events

## External Projects

Other projects can be symlinked into this directory to be managed by the orchestration system:

```bash
# Example: Add a project to be managed
ln -s /path/to/my-project apps/my-project
```

The orchestrator will discover and manage symlinked projects, allowing:
- Session workflows (spec → plan → build → docs)
- Agent execution tracking
- Cross-project context sharing
