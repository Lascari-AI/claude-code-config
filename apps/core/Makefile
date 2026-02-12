# LAI Session Manager - Development Commands
#
# Usage:
#   make help     - Show available commands
#   make up       - Start all services
#   make down     - Stop all services
#   make logs     - View logs from all services

.PHONY: help up down stop restart logs logs-backend logs-frontend logs-db \
        build rebuild shell-backend shell-frontend shell-db db-shell \
        db-reset db-migrate clean status ps

# Default target
.DEFAULT_GOAL := help

# ═══════════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════════

help: ## Show this help message
	@echo "LAI Session Manager - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER COMPOSE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

up: ## Start all services (database, backend, frontend)
	docker compose up -d
	@echo ""
	@echo "Services starting..."
	@echo "  Frontend: http://localhost:3456"
	@echo "  Backend:  http://localhost:8765"
	@echo "  API Docs: http://localhost:8765/docs"
	@echo "  Database: localhost:54320"
	@echo ""
	@echo "Run 'make logs' to view logs"

down: ## Stop all services
	docker compose down

stop: ## Stop services without removing containers
	docker compose stop

restart: ## Restart all services
	docker compose restart

status: ## Show status of all services
	docker compose ps

ps: status ## Alias for status

# ═══════════════════════════════════════════════════════════════════════════════
# LOGS
# ═══════════════════════════════════════════════════════════════════════════════

logs: ## View logs from all services (follow mode)
	docker compose logs -f

logs-backend: ## View backend logs only
	docker compose logs -f backend

logs-frontend: ## View frontend logs only
	docker compose logs -f frontend

logs-db: ## View database logs only
	docker compose logs -f db

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD
# ═══════════════════════════════════════════════════════════════════════════════

build: ## Build all Docker images
	docker compose build

rebuild: ## Rebuild all images from scratch (no cache)
	docker compose build --no-cache

build-backend: ## Build backend image only
	docker compose build backend

build-frontend: ## Build frontend image only
	docker compose build frontend

# ═══════════════════════════════════════════════════════════════════════════════
# SHELL ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

shell-backend: ## Open shell in backend container
	docker compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker compose exec frontend /bin/sh

shell-db: ## Open shell in database container
	docker compose exec db /bin/bash

db-shell: ## Connect to PostgreSQL with psql
	docker compose exec db psql -U postgres -d session_db

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

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
# DEVELOPMENT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

install-backend: ## Install backend dependencies locally (using uv)
	uv sync

install-frontend: ## Install frontend dependencies locally
	cd frontend && npm install

dev-backend: ## Run backend locally (without Docker)
	uv run uvicorn backend.main:app --reload --port 8000

dev-frontend: ## Run frontend locally (without Docker)
	cd frontend && npm run dev

# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

test-backend: ## Run backend tests
	docker compose exec backend uv run pytest

lint-frontend: ## Run frontend linter
	docker compose exec frontend npm run lint
