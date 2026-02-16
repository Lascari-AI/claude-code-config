#!/bin/bash

# Frontend Start Script - Orchestrator 3 Stream
# Starts the Vite development server

# Load environment variables
if [ -f "$(dirname "$0")/.env" ]; then
    export $(cat "$(dirname "$0")/.env" | grep -v '^#' | xargs)
fi

# Use port from .env or default to 5175
FRONTEND_PORT=${FRONTEND_PORT:-5175}
FRONTEND_HOST=${FRONTEND_HOST:-127.0.0.1}

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
kill_port $FRONTEND_PORT

echo "🎨 Starting Frontend on http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo ""

cd "$(dirname "$0")/frontend"
npm run dev
