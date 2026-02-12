# Apps Directory

This directory contains applications for the LAI Claude Code Config system.

## Structure

```
apps/
├── core/                    # Core orchestration infrastructure
│   ├── backend/             # FastAPI REST API
│   ├── frontend/            # Next.js web UI
│   ├── session_db/          # Database models and operations
│   └── orchestrator/        # (future) Agent orchestration service
│
└── {symlinked-projects}/    # External projects managed by the system
```

## Core Apps

The `core/` directory contains the infrastructure that powers the orchestration system:

- **backend**: FastAPI REST API for projects, sessions, and agents
- **frontend**: Next.js 14+ web UI with App Router, Tailwind CSS, shadcn/ui
- **session_db**: SQLModel-based PostgreSQL database for tracking sessions, agents, and execution events

## Running the Stack

```bash
# Start the backend API (from apps/core/backend)
uvicorn main:app --reload --port 8000

# Start the frontend (from apps/core/frontend)
npm run dev
```

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
