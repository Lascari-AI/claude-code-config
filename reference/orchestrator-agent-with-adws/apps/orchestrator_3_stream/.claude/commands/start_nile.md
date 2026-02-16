---
allowed-tools: Bash
description: Start Nile backend (port 8000) and frontend (port 5173) in background processes
---

# Purpose

Start both Nile server and client in background processes for local development.

## Instructions

- Start the FastAPI backend on port 8000 using uv
- Start the Vue frontend on port 5173 using npm
- Run both as background processes so they persist
- Report the running processes to the user

## Workflow

1. Start backend: `cd apps/nile/server && uv run uvicorn src.main:app --port 8000` (background)
2. Start frontend: `cd apps/nile/client && npm run dev` (background)
3. Report both processes are running with access URL
4. Open chrome against the frontend URL

## Report

Confirm both services started with: Backend at http://localhost:8000, Frontend at http://localhost:5173
