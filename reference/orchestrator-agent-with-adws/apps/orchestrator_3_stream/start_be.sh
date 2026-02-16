#!/bin/bash

# Backend Start Script - Orchestrator 3 Stream
# Starts the FastAPI server with uvicorn
#
# Usage:
#   ./start_be.sh [--cwd <working_dir>] [--session <session_id>]
#
# Arguments:
#   --cwd <path>        Optional working directory (defaults to .env ORCHESTRATOR_WORKING_DIR, then app root)
#   --session <id>      Optional session ID to resume (defaults to .env ORCHESTRATOR_SESSION_ID, then creates new)
#
# Examples:
#   ./start_be.sh --session bbf5ac77-0170-4718-86ae-0b919f575600
#   ./start_be.sh --cwd /path/to/project --session sess_123
#   ./start_be.sh --cwd /path/to/project

# Load environment variables
if [ -f "$(dirname "$0")/.env" ]; then
    export $(cat "$(dirname "$0")/.env" | grep -v '^#' | xargs)
fi

# Use port from .env or default to 9403
BACKEND_PORT=${BACKEND_PORT:-9403}
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}

# Parse command line arguments
CLI_WORKING_DIR=""
CLI_SESSION_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --cwd)
            CLI_WORKING_DIR="$2"
            shift 2
            ;;
        --session)
            CLI_SESSION_ID="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--cwd <working_dir>] [--session <session_id>]"
            exit 1
            ;;
    esac
done

# Handle working directory argument
# Priority: CLI arg (--cwd) -> .env var -> application root
if [ -n "$CLI_WORKING_DIR" ]; then
    WORKING_DIR="$CLI_WORKING_DIR"
    echo "📁 Using CLI working directory: $WORKING_DIR"
elif [ -n "$ORCHESTRATOR_WORKING_DIR" ]; then
    WORKING_DIR="$ORCHESTRATOR_WORKING_DIR"
    echo "📁 Using .env working directory: $WORKING_DIR"
else
    # Default to application root (2 levels up from script location)
    WORKING_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
    echo "📁 Using application root: $WORKING_DIR"
fi

# Handle session ID argument
# Priority: CLI arg (--session) -> .env var -> none (creates new session)
SESSION_ARGS=""
if [ -n "$CLI_SESSION_ID" ]; then
    SESSION_ID="$CLI_SESSION_ID"
    SESSION_ARGS="--session $SESSION_ID"
    echo "🔄 Resuming session: $SESSION_ID"
elif [ -n "$ORCHESTRATOR_SESSION_ID" ]; then
    SESSION_ID="$ORCHESTRATOR_SESSION_ID"
    SESSION_ARGS="--session $SESSION_ID"
    echo "🔄 Resuming .env session: $SESSION_ID"
else
    echo "✨ Starting new session"
fi

# Function to kill process using a port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)

    if [ ! -z "$pid" ]; then
        echo "⚠️  Port $port is in use by process $pid"
        echo "🔪 Killing process $pid..."
        kill -9 $pid
        sleep 1
        echo "✅ Port $port cleared"
        echo ""
    fi
}

# Clear the port if it's in use
kill_port $BACKEND_PORT

echo "🚀 Starting Backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
echo ""

cd "$(dirname "$0")/backend"
uv run python main.py --cwd "$WORKING_DIR" $SESSION_ARGS
