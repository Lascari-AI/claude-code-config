# Backend Documentation Index

## Overview

Complete technical documentation for the Orchestrator 3 Stream backend architecture, covering all modules, services, data flows, and design patterns.

**Created**: October 31, 2024
**Scope**: Backend FastAPI application (`apps/orchestrator_3_stream/backend/`)
**Framework**: FastAPI + asyncpg + Claude Agent SDK
**Database**: PostgreSQL (NeonDB)

---

## Documentation Files

### 1. **backend-structure-summary.md** (781 lines)
**Primary Architecture Document**

Comprehensive overview of the entire backend system including:
- Executive summary and architecture overview
- Data flow diagrams showing request/response patterns
- Detailed module descriptions (1-17 modules)
- Database schema documentation (6 core tables)
- State management and lifecycle documentation
- Module dependencies graph
- Key design patterns (7 patterns)
- Performance considerations
- Environment variables reference
- Testing strategy
- Error handling approach
- Integration checklist

**Key Sections**:
- High-level data flow diagram
- Module-by-module breakdown (config, logger, database, websocket, services, hooks)
- Request/Response flow examples
- State management lifecycle
- Database schema with all tables explained

**Best for**: Understanding overall architecture, how modules interact, data persistence model

---

### 2. **backend-architecture-diagram.md** (567 lines)
**Visual Architecture Representation**

Comprehensive Mermaid diagrams showing:
- Module relationship map (graph TB)
- Data flow for user message processing (sequence diagram)
- Component interaction for agent creation (graph LR)
- Database schema relationships (ER diagram)
- Request/Response processing pipeline (graph TD)
- Module dependency tree (graph TD)
- API endpoints overview (graph LR)
- Event broadcasting architecture (graph TD)
- State management lifecycle (stateDiagram)
- Configuration layers (graph TD)
- Error handling flow (graph TD)

**Mermaid Diagrams Included**:
1. Module Relationship Map (11 components)
2. Data Flow: User Message Processing (8-step sequence)
3. Component Interaction: Agent Creation (7 nodes)
4. Database Schema Relationships (ER with 6 tables)
5. Request/Response Pipeline (10-step flow)
6. Module Dependency Tree (hierarchy)
7. API Endpoints (organized by category)
8. Event Broadcasting Architecture (3-layer flow)
9. State Management Lifecycle (10 states)
10. Configuration Layers (3 layers + 6 dependencies)
11. Error Handling Flow (8-step process)

**Best for**: Visual learners, understanding data flow, state transitions, component relationships

---

### 3. **backend-modules-reference.md** (563 lines)
**Detailed Module Specifications**

Comprehensive reference guide including:
- Module Specification Table (16 rows × 6 columns)
  - File paths, line counts, purposes, responsibilities
  - Main classes/functions
  - Key dependencies
- Module Dependency Matrix (19×19 table)
- API Endpoints Reference (all 13 endpoints documented)
- Database Tables Overview (6 tables with full schema)
- Configuration Variables Reference (organized by category)
- Claude SDK Integration Points (options, hooks, tools)
- Error Handling Patterns
- Testing Strategy
- Best Practices (6 conventions)
- Performance Notes
- Security Considerations
- Integration Checklist

**Tables Included**:
1. Module Specification Table (16 modules × 6 attributes)
2. Module Dependency Matrix (19×19)
3. Health & Information API endpoints
4. Chat Management API endpoints
5. Data Retrieval API endpoints
6. Database table specifications (6 tables)
7. Configuration variables (organized by category)
8. Claude SDK integration details

**Best for**: Detailed specifications, API reference, database schema, configuration, integration checklist

---

## Quick Navigation

### For Different Audiences

#### **New Team Members**
1. Start with: **backend-structure-summary.md** - "Architecture Overview" section
2. Review: **backend-architecture-diagram.md** - "Module Relationship Map" and "Data Flow"
3. Reference: **backend-modules-reference.md** - "Module Specification Table"

#### **API Developers**
1. Review: **backend-modules-reference.md** - "API Endpoints Reference"
2. Reference: **backend-structure-summary.md** - "Request/Response Flow"
3. Debug: **backend-architecture-diagram.md** - "Request/Response Processing Pipeline"

#### **Database Developers**
1. Study: **backend-modules-reference.md** - "Database Tables Overview"
2. Reference: **backend-architecture-diagram.md** - "Database Schema Relationships"
3. Understand: **backend-structure-summary.md** - "Database Schema" section

#### **Integration/DevOps**
1. Check: **backend-modules-reference.md** - "Integration Checklist"
2. Reference: **backend-modules-reference.md** - "Configuration Variables Reference"
3. Review: **backend-structure-summary.md** - "Environment Variables Reference"

#### **QA/Testers**
1. Review: **backend-structure-summary.md** - "Testing Strategy"
2. Reference: **backend-modules-reference.md** - "Database Tables Overview"
3. Study: **backend-architecture-diagram.md** - "Data Flow" diagrams

#### **Architects/Tech Leads**
1. Study: **backend-structure-summary.md** - entire document
2. Review: **backend-architecture-diagram.md** - all diagrams
3. Reference: **backend-modules-reference.md** - tables and specifications

---

## Module Quick Reference

### 16 Backend Modules Documented

| # | Module | Lines | Purpose | Quick Link |
|---|--------|-------|---------|-----------|
| 1 | main.py | 646 | FastAPI entry point | See "main.py" in summary |
| 2 | config.py | 197 | Environment & settings | See "Configuration" in reference |
| 3 | logger.py | 182 | Rich + file logging | See "Logging" in summary |
| 4 | database.py | 1600 | asyncpg + operations | See "Database" in reference |
| 5 | orch_database_models.py | 344 | Pydantic models | See "Database Models" in reference |
| 6 | websocket_manager.py | 257 | Connection management | See "WebSocket" in summary |
| 7 | orchestrator_service.py | 1009 | Business logic | See "Orchestrator Service" in summary |
| 8 | agent_manager.py | 1397 | Agent lifecycle | See "Agent Manager" in summary |
| 9 | hooks.py | 556 | Event hooks | See "Hooks" in summary |
| 10 | orchestrator_hooks.py | 168 | Orch-specific hooks | See "Orchestrator Hooks" in summary |
| 11 | command_agent_hooks.py | 629 | Agent command hooks | See "Command Agent Hooks" in summary |
| 12 | slash_command_parser.py | 267 | Command discovery | See "Slash Command Parser" in summary |
| 13 | subagent_loader.py | 220 | Template registry | See "Subagent Loader" in summary |
| 14 | subagent_models.py | 75 | Template types | See "Subagent Models" in summary |
| 15 | single_agent_prompt.py | 285 | Event summarization | See "Single Agent Prompt" in summary |
| 16 | file_tracker.py | 285 | File change detection | See "File Tracker" in summary |

---

## Key Architecture Concepts

### 1. **Singleton Pattern**
- Global WebSocket manager
- Global logger instance
- Global database connection pool
- Single active orchestrator

**Reference**: See "Key Design Patterns" in backend-structure-summary.md

### 2. **Service Layer Pattern**
- OrchestratorService abstracts Claude SDK
- AgentManager abstracts agent lifecycle
- Database module abstracts SQL

**Reference**: See "Service Layer Pattern" in backend-structure-summary.md

### 3. **Hook-Based Event Capture**
- Claude SDK hooks capture all events
- Events logged to database AND broadcast via WebSocket
- Async summarization in background

**Reference**: See "Event Broadcasting Architecture" diagram

### 4. **Streaming/Real-time Pattern**
- WebSocket broadcasts all events
- Text responses streamed in chunks
- Thinking blocks sent as they occur

**Reference**: See "Data Flow: User Message Processing" diagram

### 5. **Registry Pattern**
- SubagentRegistry caches templates
- SlashCommand parser caches discovered commands
- Prevents repeated file I/O

**Reference**: See "Subagent Loader" in backend-structure-summary.md

---

## Data Flow Diagrams

### User Message Flow
```
Frontend -> POST /send_chat -> FastAPI -> Service -> Claude SDK -> Events
   ↓
  DB insert -> WebSocket broadcast -> Frontend update
```

**Full Sequence**: See "Data Flow: User Message Processing" in backend-architecture-diagram.md

### Agent Creation Flow
```
User command -> Management tool -> AgentManager -> Create DB record
   ↓
Create Claude SDK client -> Store client -> Broadcast event -> Frontend
```

**Full Diagram**: See "Component Interaction: Agent Creation" in backend-architecture-diagram.md

### Event Broadcasting
```
Claude SDK hook -> Database log -> WebSocket broadcast -> All clients
                ↓
            Background summarization
```

**Full Architecture**: See "Event Broadcasting Architecture" in backend-architecture-diagram.md

---

## API Endpoints Quick Reference

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| GET | `/health` | Health check | `{status, service, websocket_connections}` |
| GET | `/get_orchestrator` | Metadata + tools + templates | Full orchestrator data |
| GET | `/get_headers` | Working directory | `{cwd}` |
| POST | `/send_chat` | Process user message | `{status, message}` |
| POST | `/load_chat` | Load chat history | `{messages, turn_count}` |
| GET | `/get_events` | Unified event log | `{events, count}` |
| GET | `/list_agents` | List active agents | `{agents}` |
| POST | `/api/open-file` | Open in IDE | `{status, message}` |
| WS | `/ws` | Real-time streaming | Event stream |

**Full Reference**: See "API Endpoints Reference" in backend-modules-reference.md

---

## Database Schema Overview

### Core Tables (6)

| Table | Purpose | Key Fields | Operations |
|-------|---------|-----------|-----------|
| orchestrator_agents | Singleton orchestrator | id, session_id, status, costs, metadata | CRUD, session management |
| agents | Managed agents | id, orchestrator_agent_id, name, status, costs | CRUD, cost tracking |
| agent_logs | Event log | id, agent_id, event_type, payload, summary | Insert, query, summarize |
| orchestrator_chat | 3-way chat | id, sender_type, receiver_type, message | Insert, query, summarize |
| prompts | Prompt history | id, agent_id, prompt_text, summary | Insert, query, summarize |
| system_logs | System events | id, level, message, metadata | Insert, query |

**Full Schema**: See "Database Tables Overview" in backend-modules-reference.md

---

## Configuration Reference

### Essential Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db

# Server Ports
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9403
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175

# Models
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
DEFAULT_AGENT_MODEL=claude-sonnet-4-5-20250929

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs

# Working Directory (or use --cwd flag)
ORCHESTRATOR_WORKING_DIR=/path/to/project
```

**Complete Reference**: See "Configuration Variables Reference" in backend-modules-reference.md

---

## Testing Information

### Test Location
- Directory: `backend/tests/`
- Runner: `uv run pytest`
- Strategy: Real database connections (no mocks)

### Test Files
- `test_database.py` - Database operations
- `test_websocket_raw.py` - WebSocket functionality
- `test_agent_events.py` - Agent event capture
- `test_display.py` - Display/logging tests

### Key Principle
**Never mock the database** - Use ephemeral test data that's cleaned up after each test.

**Full Details**: See "Testing Strategy" in backend-structure-summary.md

---

## Performance & Security

### Performance Considerations
- Connection pooling: 5-20 connections
- Async queries: Non-blocking with asyncpg
- JSONB: Efficient metadata storage
- Hourly log rotation: Prevents huge files
- Background tasks: No blocking in main loop

**Full Details**: See "Performance Considerations" in backend-structure-summary.md

### Security Practices
- SQL injection prevention: Parameterized queries
- Environment variables: All secrets via env
- CORS configuration: Environment-based
- File operations: Path validation

**Full Details**: See "Security Considerations" in backend-modules-reference.md

---

## Troubleshooting Quick Links

### Issue: API endpoint returns 500 error
1. Check logs: `backend/logs/YYYY-MM-DD_HH.log`
2. See: "Error Handling" section in backend-structure-summary.md
3. Check: "Error Handling Patterns" in backend-modules-reference.md

### Issue: WebSocket events not appearing on frontend
1. Check: "Event Broadcasting Architecture" diagram
2. Verify: WebSocket manager is broadcasting
3. See: "Module Dependency Matrix" to trace dependencies

### Issue: Database connection failing
1. Check: DATABASE_URL in .env
2. See: "Configuration Variables" in backend-modules-reference.md
3. Verify: Connection pool settings

### Issue: Agent not executing
1. Check: Agent status in database
2. See: "Agent Manager" section in backend-structure-summary.md
3. Review: "Component Interaction: Agent Creation" diagram

### Issue: Costs not updating
1. Check: update_orchestrator_costs() calls
2. See: "Database" module in backend-modules-reference.md
3. Verify: Hook events are being captured

---

## Dependency Map

```
main.py (entry point)
├── config (settings)
├── logger (logging)
├── database (data access)
├── websocket_manager (real-time)
└── orchestrator_service (business logic)
    ├── agent_manager (agent lifecycle)
    ├── orchestrator_hooks (event capture)
    ├── subagent_loader (templates)
    └── Claude SDK (AI execution)
```

**Full Tree**: See "Module Dependency Tree" in backend-architecture-diagram.md

---

## Integration Checklist

Before deploying the backend:

- [ ] PostgreSQL database initialized and accessible
- [ ] DATABASE_URL environment variable set
- [ ] ANTHROPIC_API_KEY environment variable set
- [ ] Backend port (9403) available and configured
- [ ] Frontend port (5175) configured if needed
- [ ] CORS_ORIGINS configured for frontend
- [ ] Log directory writable (backend/logs/)
- [ ] .claude/agents/ directory exists
- [ ] .claude/commands/ directory exists
- [ ] System prompt file at configured path
- [ ] All configuration variables from .env.sample set

**Full Checklist**: See "Integration Checklist" in backend-modules-reference.md

---

## Document Statistics

| Document | Lines | Tables | Diagrams | Sections |
|----------|-------|--------|----------|----------|
| backend-structure-summary.md | 781 | 1 | 1 | 20+ |
| backend-architecture-diagram.md | 567 | 0 | 11 | 11 |
| backend-modules-reference.md | 563 | 25+ | 0 | 18+ |
| **Total** | **1,911** | **26+** | **11** | **50+** |

---

## How to Use This Documentation

### Reading Guide

1. **First Time**: Start with backend-structure-summary.md Executive Overview
2. **Visual Learner**: Review backend-architecture-diagram.md Mermaid diagrams
3. **Deep Dive**: Study backend-modules-reference.md Module Specification Table
4. **Reference**: Use specific sections as needed for implementation

### Document Organization

- **Summary**: Big picture, architecture, flows, patterns
- **Diagrams**: Visual representation, relationships, sequences
- **Reference**: Detailed specifications, tables, checklists

### Search Strategy

- **"How does X work?"** → Use backend-architecture-diagram.md flow diagrams
- **"Where is feature Y?"** → Use backend-modules-reference.md module table
- **"What parameters for Z?"** → Use backend-modules-reference.md API/Config tables
- **"How are components connected?"** → Use backend-architecture-diagram.md dependency trees

---

## Related Documentation

This documentation covers the backend. For complete system understanding, also review:

- **Frontend**: `app_docs/frontend-structure-summary.md`
- **Database**: Schema files in `apps/orchestrator_db/`
- **Project Rules**: `/CLAUDE.md` in project root
- **App Instructions**: `apps/orchestrator_3_stream/CLAUDE.md`

---

## Version Information

- **Created**: October 31, 2024
- **Backend Framework**: FastAPI
- **Database**: PostgreSQL (asyncpg)
- **AI Integration**: Claude Agent SDK
- **Documentation Format**: Markdown + Mermaid diagrams

---

## Next Steps

1. **For Implementation**: Follow Quick Navigation section above
2. **For Questions**: Reference appropriate document section
3. **For Integration**: Follow Integration Checklist
4. **For Debugging**: Use Troubleshooting Quick Links

---

**Documentation Status**: ✅ Complete
**Last Updated**: October 31, 2024
**Maintainer**: Backend QA Specialist
