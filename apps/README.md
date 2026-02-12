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

### Quick Start (Docker)

The easiest way to run the full stack is with Docker Compose:

```bash
cd apps/core

# Start all services (database, backend, frontend)
make up

# View logs
make logs

# Stop services
make down
```

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:54320

### Available Make Commands

```bash
make help           # Show all available commands

# Service Management
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make status         # Show service status

# Logs
make logs           # View all logs (follow mode)
make logs-backend   # View backend logs only
make logs-frontend  # View frontend logs only
make logs-db        # View database logs only

# Database
make db-shell       # Connect to PostgreSQL with psql
make db-reset       # Reset database (WARNING: destroys data)
make db-backup      # Backup database to backup.sql
make db-restore     # Restore from backup.sql

# Build
make build          # Build all Docker images
make rebuild        # Rebuild without cache

# Cleanup
make clean          # Stop and remove everything (WARNING: destroys data)
```

### Running Without Docker

If you prefer to run services locally:

```bash
# 1. Start PostgreSQL (your local instance on port 5432, or use Docker for just the DB)
docker compose up -d db

# 2. Set up environment
cp apps/core/.env.sample apps/core/.env
# Edit .env if using different database settings

# 3. Start the backend
cd apps/core/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 4. Start the frontend (in another terminal)
cd apps/core/frontend
npm install
npm run dev
```

### Development with Hot Reload

Both Docker and local development support hot reload:

- **Backend**: Changes to Python files in `backend/` or `session_db/` automatically restart the server
- **Frontend**: Changes to files in `frontend/src/` trigger Fast Refresh in the browser

### Environment Variables

Copy the sample environment file and customize as needed:

```bash
cp apps/core/.env.sample apps/core/.env
```

Key variables:
- `SESSION_DB_URL`: PostgreSQL connection string (default uses Docker DB on port 54320)
- `NEXT_PUBLIC_API_URL`: Backend API URL for frontend (default: http://localhost:8000)

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
