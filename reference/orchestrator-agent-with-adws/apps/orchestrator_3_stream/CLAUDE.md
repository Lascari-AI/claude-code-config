# Orchestrator 3 Stream - Agent Instructions

## Overview
Multi-agent orchestration system with PostgreSQL backend, Vue 3 frontend, and WebSocket streaming. Uses `.env` configuration for ports and comprehensive hourly-rotating logs.

## Key Architecture Decisions
- **Logging**: Hourly rotating log files (backend/logs/<datetime_HH>.log) + Rich console logging for Rich UI, classic logging for config
- **WebSocket**: Centralized manager (`websocket_manager.py`) for real-time event broadcasting
- **Configuration**: `.env` files for port management, classic Python logging for config loading
- **Frontend**: Vue 3 + TypeScript + Pinia store with test data
- **Backend**: FastAPI + asyncpg (PostgreSQL) + Claude Agent SDK

## Project Structure
```
apps/orchestrator_3_stream/
├── .env                          # Environment config (gitignored)
├── .env.sample                   # Sample environment template
├── start_be.sh                   # Backend launcher (port 8002)
├── start_fe.sh                   # Frontend launcher (port 5175)
├── backend/
│   ├── main.py                   # FastAPI server with WebSocket endpoint
│   ├── logs/                     # Hourly rotating log files
│   └── modules/
│       ├── config.py             # Environment variable loader (classic logging)
│       ├── logger.py             # Hourly rotating logger + Rich console
│       └── websocket_manager.py  # WebSocket connection manager & broadcasting
└── frontend/
    ├── src/
    │   ├── main.ts               # Vue app entry point
    │   ├── App.vue               # 3-column layout (agents, stream, chat)
    │   ├── types.d.ts            # TypeScript types (mirrors database models)
    │   ├── stores/
    │   │   └── orchestratorStore.ts  # Pinia state management
    │   ├── data/
    │   │   └── testData.ts       # Sample data for UI testing
    │   ├── components/
    │   │   ├── AgentList.vue     # Left sidebar: agent list
    │   │   ├── EventStream.vue   # Center: event log stream
    │   │   └── OrchestratorChat.vue  # Right sidebar: chat interface
    │   └── styles/
    │       └── global.css        # Dark theme with cyan/teal accents
    └── vite.config.ts            # Vite configuration
```

## File-by-File Summary

### Backend Files
- **main.py**: FastAPI server with WebSocket endpoint `/ws`, health check, CORS, uses config ports. Enhanced `/get_orchestrator` endpoint returns metadata, slash commands, and agent templates. Includes `discover_slash_commands()` function that scans `.claude/commands/` directory and caches results.
- **modules/config.py**: Loads `.env` vars for ports/DB/CORS, logs config on startup with classic logging
- **modules/logger.py**: OrchestratorLogger class with hourly file rotation + Rich console output
- **modules/websocket_manager.py**: WebSocketManager class for managing connections and broadcasting events
- **modules/agent_manager.py**: Manages agent lifecycle and broadcasts agent response blocks (TextBlock, ThinkingBlock, ToolUseBlock) via WebSocket
- **modules/hooks.py**: Captures Claude SDK events and broadcasts them as agent_log events via WebSocket
- **modules/database.py**: Database operations for orchestrator and agents. Added `update_orchestrator_metadata()` function for updating orchestrator metadata JSONB field using PostgreSQL merge operator.
- **modules/orchestrator_service.py**: Orchestrator service with Claude SDK integration. Enhanced to capture SystemMessage data on first interaction and store it in orchestrator metadata.
- **tests/**: Backend test scripts for database and WebSocket functionality

### Frontend Files

**Composables:**
- **src/composables/useHeaderBar.ts**: Manages header bar state including agent stats, cost tracking, CWD, and export functionality.
- **src/composables/useEventStreamFilter.ts**: Manages event stream filtering including main tabs (Combined/Errors/Performance), quick level filters, search with regex, and auto-scroll state.
- **src/composables/useAgentPulse.ts**: Manages pulsing animations for agents with debouncing; triggers on tool, hook, and thinking events to provide visual feedback of active agents.

**Components:**
- **src/components/AgentList.vue**: Purple-tinted left sidebar showing agent cards with status indicators. Includes smooth pulsing animations (triggered via useAgentPulse) that provide visual feedback when agents receive tool, hook, or thinking events.
- **src/components/EventStream.vue**: Center column displaying filtered event logs with auto-scroll; uses FilterControls component.
- **src/components/FilterControls.vue**: Reusable filter UI component with tabs, search, quick filters, and auto-follow toggle.
- **src/components/OrchestratorChat.vue**: Right sidebar chat interface with typing indicator and send functionality.
- **src/components/GlobalCommandInput.vue**: Command input overlay (Cmd+K) with system information panel displaying orchestrator session ID, CWD, slash commands (as cyan badges), and agent templates (as green badges). Fetches data from `/get_orchestrator` on mount.
- **src/components/event-rows/**: Specialized event row components (AgentLogRow, SystemLogRow, OrchestratorChatRow, ThinkingBlockRow, ToolUseBlockRow) with markdown rendering support.

**Other:**
- **src/types.d.ts**: TypeScript interfaces mirroring `apps/orchestrator_db/models.py` database schema. Added `SystemMessageInfo`, `SlashCommand`, `SubagentTemplate`, `SubagentFrontmatter`, and `GetOrchestratorResponse` interfaces for system info display.
- **src/data/testData.ts**: Sample agents, logs, chat messages for UI development.
- **src/stores/orchestratorStore.ts**: Pinia store with state, getters, actions for agents/events/chat. Integrated with useAgentPulse composable to trigger visual feedback animations on relevant WebSocket events.
- **src/styles/global.css**: Dark theme CSS with cyan/teal accents, status colors, utility classes.
- **src/utils/markdown.ts**: Markdown rendering utility with syntax highlighting and XSS protection via DOMPurify.
- **src/services/api.ts**: Axios instance with base URL and error handling interceptors.
- **src/services/chatService.ts**: HTTP and WebSocket communication service for orchestrator chat.

### Configuration Files
- **.env / .env.sample**: Port configuration (BE:8002, FE:5175), DB settings, CORS origins

## Instructions for Agents

**IMPORTANT**: When creating or modifying files, update this section with a 1-2 sentence summary of the file's purpose and key functionality. Keep it concise!

Example format:
```markdown
- **path/to/file.ext**: Brief description of what it does and why it exists.
```

**DO NOT** bloat this file with implementation details - just high-level purpose statements.

## If you're working on frontend, always validate your work with Playwright MCP

- If you're working on frontend, there's no point in making a frontend change without testing it.
- Use the playwright MCP Server or a @agent-playwright-validator agent to test your work.
- If you're missing the MCP server stop and ask the user for it.

## If you create summary, implementation, test files or documentation files, add them to the app_docs directory.

- If you create summary, implementation, test files or documentation files, add them to the app_docs directory.
- We don't want to pollute the root directory with these files.
- Test files should be in the tests directory, and should be made to run with either `uv run pytest` or some frontend test runner.

## If you create a tester script that you don't want added to our actual tests suite, add it to tmp_scripts directory.

- If you create a tester script that you don't want added to our actual tests suite, add it to tmp_scripts directory.
- We don't want to pollute the root directory with these files.

## IMPORTANT: Never silently fail, always raise an error and log it.

- Never create a try/except block that that skips over errors.
- If you try catch an error, always log it and raise it again.