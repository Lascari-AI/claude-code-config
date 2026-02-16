#!/bin/bash
# Start Nile Backend (FastAPI + Uvicorn)
# Runs on http://localhost:8000 with hot reload

cd "$(dirname "$0")/server"
uv run uvicorn src.main:app --port 8000 --reload
