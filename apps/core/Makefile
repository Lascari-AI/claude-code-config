# LAI Session Manager - Development Commands
#
# Recommended development workflow (3 terminals):
#   Terminal 1: make db          # Start database
#   Terminal 2: make dev-backend # Run backend with hot reload
#   Terminal 3: make dev-frontend # Run frontend with hot reload
#
# Or use Docker for everything: make up

.PHONY: help dev db dev-backend dev-frontend install up down stop restart \
        logs logs-db build rebuild shell-db db-shell db-reset db-backup \
        db-restore clean prune test-backend lint-frontend status ps

# Default target
.DEFAULT_GOAL := help

# ═══════════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════════

help: ## Show this help message
	@echo "LAI Session Manager - Development Commands"
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║  RECOMMENDED: Local dev with 3 terminals                         ║"
	@echo "║                                                                   ║"
	@echo "║  Terminal 1: make db           (database in Docker)              ║"
	@echo "║  Terminal 2: make dev-backend  (FastAPI with hot reload)         ║"
	@echo "║  Terminal 3: make dev-frontend (Next.js with hot reload)         ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "URLs:"
	@echo "  Frontend: http://localhost:3456"
	@echo "  Backend:  http://localhost:8765"
	@echo "  API Docs: http://localhost:8765/docs"
	@echo ""
	@echo "All commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL DEVELOPMENT (RECOMMENDED)
# ═══════════════════════════════════════════════════════════════════════════════

dev: ## Show local development instructions
	@echo ""
	@echo "Local Development Setup (3 terminals):"
	@echo ""
	@echo "  Terminal 1 - Database:"
	@echo "    cd apps/core && make db"
	@echo ""
	@echo "  Terminal 2 - Backend (FastAPI):"
	@echo "    cd apps/core && make dev-backend"
	@echo ""
	@echo "  Terminal 3 - Frontend (Next.js):"
	@echo "    cd apps/core && make dev-frontend"
	@echo ""
	@echo "First time? Run 'make install' to install dependencies."
	@echo ""

db: ## Start database only (Docker) - run in Terminal 1
	docker compose up db
	@echo ""
	@echo "Database running at localhost:54320"

dev-backend: ## Run backend locally with hot reload - run in Terminal 2
	@echo "Starting FastAPI backend on http://localhost:8765"
	@echo "API docs at http://localhost:8765/docs"
	@echo ""
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8765

dev-frontend: ## Run frontend locally with hot reload - run in Terminal 3
	@echo "Starting Next.js frontend on http://localhost:3456"
	@echo ""
	cd frontend && npm run dev -- --port 3456

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	uv sync
	@echo ""
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "Done! Run 'make dev' to see development instructions."

# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER COMPOSE (ALTERNATIVE)
# ═══════════════════════════════════════════════════════════════════════════════

up: ## Start all services in Docker (alternative to local dev)
	docker compose up -d
	@echo ""
	@echo "All services starting in Docker..."
	@echo "  Frontend: http://localhost:3456"
	@echo "  Backend:  http://localhost:8765"
	@echo "  API Docs: http://localhost:8765/docs"
	@echo "  Database: localhost:54320"
	@echo ""
	@echo "Run 'make logs' to view logs"
	@echo ""
	@echo "TIP: For better hot reload, use local dev instead:"
	@echo "     make dev"

down: ## Stop all Docker services
	docker compose down

stop: ## Stop Docker services without removing containers
	docker compose stop

restart: ## Restart all Docker services
	docker compose restart

status: ## Show status of Docker services
	docker compose ps

ps: status ## Alias for status

# ═══════════════════════════════════════════════════════════════════════════════
# LOGS (Docker mode)
# ═══════════════════════════════════════════════════════════════════════════════

logs: ## View logs from all Docker services
	docker compose logs -f

logs-db: ## View database logs only
	docker compose logs -f db

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD (Docker)
# ═══════════════════════════════════════════════════════════════════════════════

build: ## Build all Docker images
	docker compose build

rebuild: ## Rebuild all Docker images from scratch
	docker compose build --no-cache

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

shell-db: ## Open shell in database container
	docker compose exec db /bin/bash

db-shell: ## Connect to PostgreSQL with psql
	docker compose exec db psql -U postgres -d session_db

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS session_db;"
	docker compose exec db psql -U postgres -c "CREATE DATABASE session_db;"
	docker compose exec db psql -U postgres -d session_db -f /docker-entrypoint-initdb.d/init.sql
	@echo "Database reset complete. Restart backend to recreate tables."

db-backup: ## Backup database to backup.sql
	docker compose exec db pg_dump -U postgres session_db > backup.sql
	@echo "Database backed up to backup.sql"

db-restore: ## Restore database from backup.sql
	@test -f backup.sql || (echo "backup.sql not found" && exit 1)
	docker compose exec -T db psql -U postgres session_db < backup.sql
	@echo "Database restored from backup.sql"

# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

clean: ## Stop services and remove volumes (WARNING: destroys data)
	@echo "WARNING: This will delete all data including the database!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker compose down -v
	@echo "All containers and volumes removed"

prune: ## Remove unused Docker resources
	docker system prune -f

# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

test-backend: ## Run backend tests
	uv run pytest

lint-frontend: ## Run frontend linter
	cd frontend && npm run lint
