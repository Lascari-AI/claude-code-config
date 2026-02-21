# Implementation Plan

> **Session**: `2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-02-19
> **Updated**: 2026-02-19

---

## Overview

- **Checkpoints**: 5 (0 complete)
- **Total Tasks**: 32

## ⬜ Checkpoint 1: Tracer Bullet - Single Chat Round-Trip with Claude SDK

**Goal**: User sends one message on a session detail page, backend routes it through ClaudeSDKClient, response displays in a basic chat panel. Proves the full pipeline works end-to-end: frontend → FastAPI → Claude SDK → InteractiveMessage DB → chat panel rendering.

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/backend/src/main.py` | 📄 exists | FastAPI app with no chat routes |
| Before | `apps/core/backend/src/agent/session_agent.py` | 📄 exists | Example SDK agent script (CLI only) |
| Before | `apps/core/backend/src/database/models/` | 📄 exists | Session, Agent, AgentLog models (no interactive messages) |
| Before | `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx` | 📄 exists | Session detail page with phase tabs only |
| Before | `apps/core/frontend/src/db/schema.ts` | 📄 exists | Drizzle schema without interactive_messages |
| After | `apps/core/backend/src/database/models/interactive_message.py` | ✨ new | InteractiveMessage SQLModel for block-level chat storage |
| After | `apps/core/backend/src/routers/chat.py` | ✨ new | FastAPI chat router with send-message endpoint |
| After | `apps/core/backend/src/agent/spec_agent_service.py` | ✨ new | SpecAgentService wrapping ClaudeSDKClient for spec interviews |
| After | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | ✨ new | Minimal chat panel with input and message display |
| After | `apps/core/frontend/src/db/schema.ts` | 📝 modified | Drizzle schema with interactive_messages table added |

### Testing Strategy

**Approach**: Manual end-to-end test + type checking

**Verification Steps**:
- [ ] `Backend starts without errors (uvicorn)`
- [ ] `POST to /api/chat/send with session_slug and message returns agent response`
- [ ] `InteractiveMessage rows created in database for both user message and agent response`
- [ ] `Frontend chat panel renders the exchange`
- [ ] `TypeScript compiles without errors (npx tsc --noEmit)`

### ⬜ Task Group 1.1: Data Layer — InteractiveMessage model & table

**Objective**: Create the InteractiveMessage SQLModel for block-level chat storage with DTOs and CRUD functions. Table created via SQLModel.metadata.create_all on backend startup.

#### ⬜ Task 1.1.1: Create InteractiveMessage SQLModel

**File**: `apps/core/backend/src/database/models/interactive_message.py`

**Description**: Create the InteractiveMessage table model with block-level granularity for chat storage. Each row represents one block (TextBlock, ToolUseBlock, etc.) from either the user or the agent. Include InteractiveMessageCreate and InteractiveMessageSummary DTOs. MIRROR patterns from agent_log.py for imports, field definitions, and DTO structure.

**Context to Load**:
- `apps/core/backend/src/database/models/agent_log.py` (lines 1-200) - Reference model pattern: imports, field definitions, Column types, DTOs, relationships
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/spec.md` (lines 261-312) - Interactive chat table schema direction from spec

**Actions**:
- ⬜ **1.1.1.1**: CREATE FILE apps/core/backend/src/database/models/interactive_message.py — Module docstring, imports from datetime, UUID, sqlalchemy, sqlmodel. MIRROR import pattern from agent_log.py. (`apps/core/backend/src/database/models/interactive_message.py`)
- ⬜ **1.1.1.2**: CREATE CLASS InteractiveMessage(SQLModel, table=True) — __tablename__='interactive_messages'. Fields: id (UUID PK default uuid4), session_id (FK sessions, indexed), agent_id (FK agents, nullable, indexed), phase (varchar, indexed, 'spec'|'plan'), role (varchar, 'user'|'assistant'|'tool_use'|'tool_result'), block_type (varchar, 'text'|'tool_use'|'tool_result'|'thinking'), content (Text, nullable), tool_name (varchar, nullable, indexed), turn_index (int), block_index (int), timestamp (datetime, indexed, default utcnow). Relationships: session (Optional[Session]), agent (Optional[Agent]). (`apps/core/backend/src/database/models/interactive_message.py`)
- ⬜ **1.1.1.3**: CREATE TYPE InteractiveMessageCreate(SQLModel) — DTO with fields: session_id (UUID), agent_id (Optional UUID), phase (str), role (str), block_type (str), content (Optional str), tool_name (Optional str), turn_index (int), block_index (int). (`apps/core/backend/src/database/models/interactive_message.py`)
- ⬜ **1.1.1.4**: CREATE TYPE InteractiveMessageSummary(SQLModel) — Lightweight DTO: id (UUID), session_id (UUID), role (str), block_type (str), content (Optional str), tool_name (Optional str), turn_index (int), block_index (int), timestamp (datetime). (`apps/core/backend/src/database/models/interactive_message.py`)

#### ⬜ Task 1.1.2: Register InteractiveMessage in model exports

**File**: `apps/core/backend/src/database/models/__init__.py`

**Description**: Add imports for InteractiveMessage, InteractiveMessageCreate, InteractiveMessageSummary and add them to __all__ list. Follow existing import section pattern.

**Context to Load**:
- `apps/core/backend/src/database/models/__init__.py` (lines 1-94) - Existing import pattern and __all__ list structure

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.2.1**: UPDATE apps/core/backend/src/database/models/__init__.py — ADD import section: from .interactive_message import (InteractiveMessage, InteractiveMessageCreate, InteractiveMessageSummary). Place after AgentLog imports. (`apps/core/backend/src/database/models/__init__.py`)
- ⬜ **1.1.2.2**: UPDATE apps/core/backend/src/database/models/__init__.py — ADD 'InteractiveMessage', 'InteractiveMessageCreate', 'InteractiveMessageSummary' to __all__ list under a new '# InteractiveMessage' comment section. (`apps/core/backend/src/database/models/__init__.py`)

#### ⬜ Task 1.1.3: Register model in database connection for table creation

**File**: `apps/core/backend/src/database/connection.py`

**Description**: Add InteractiveMessage to the model imports in connection.py so SQLModel.metadata.create_all discovers and creates the table on backend startup.

**Context to Load**:
- `apps/core/backend/src/database/connection.py` (lines 28-36) - Existing model imports for table creation (noqa: F401 pattern)

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.3.1**: UPDATE apps/core/backend/src/database/connection.py — ADD 'InteractiveMessage,' to the imports from .models block (line ~30-35). Follow existing noqa: F401 comment pattern. (`apps/core/backend/src/database/connection.py`)

#### ⬜ Task 1.1.4: Add InteractiveMessage CRUD functions

**File**: `apps/core/backend/src/database/crud.py`

**Description**: Add create_interactive_message() and list_messages_for_session() functions following existing CRUD patterns with AsyncSession and DTOs.

**Context to Load**:
- `apps/core/backend/src/database/crud.py` (lines 607-690) - Existing CRUD pattern for AgentLog (create_agent_log, list_logs_for_session)

**Depends On**: Tasks 1.1.1, 1.1.2

**Actions**:
- ⬜ **1.1.4.1**: UPDATE apps/core/backend/src/database/crud.py — ADD imports for InteractiveMessage, InteractiveMessageCreate, InteractiveMessageSummary to the import block from .models. (`apps/core/backend/src/database/crud.py`)
- ⬜ **1.1.4.2**: CREATE FUNCTION create_interactive_message(db: AsyncSession, data: InteractiveMessageCreate) -> InteractiveMessage — MIRROR pattern from create_agent_log. Build InteractiveMessage from DTO fields, db.add, flush, refresh, return. (`apps/core/backend/src/database/crud.py`)
- ⬜ **1.1.4.3**: CREATE FUNCTION list_messages_for_session(db: AsyncSession, session_id: UUID, *, phase: str | None = None, limit: int = 1000) -> Sequence[InteractiveMessage] — Query interactive_messages WHERE session_id, optional phase filter, ORDER BY turn_index ASC, block_index ASC. (`apps/core/backend/src/database/crud.py`)

### ⬜ Task Group 1.2: Agent Service — SpecAgentService with ClaudeSDKClient

**Objective**: Create a service class that wraps ClaudeSDKClient for spec interview chat. Handles connecting to SDK, sending a message, receiving response blocks, and persisting them to the interactive_messages table.

#### ⬜ Task 1.2.1: Create SpecAgentService class

**File**: `apps/core/backend/src/agent/spec_agent_service.py`

**Description**: Service class wrapping ClaudeSDKClient for spec interview chat. Configures the client with session MCP tools, skill loading via setting_sources=['project'], allowed tools list. Provides connect() to initialize the client, send_message(prompt) to query and collect response blocks, and disconnect() to clean up. Persists response blocks to interactive_messages table via CRUD functions.

**Context to Load**:
- `apps/core/backend/src/agent/session_agent.py` (lines 1-135) - Existing SDK usage pattern: ClaudeAgentOptions, query(), message types (AssistantMessage, ResultMessage, SystemMessage)
- `apps/core/backend/src/mcp_tools/server.py` (lines 1-88) - MCP server configuration: get_session_mcp_server(), SERVER_NAME, tool registration pattern
- `apps/core/backend/src/database/crud.py` (lines 607-690) - create_interactive_message and list_messages_for_session CRUD functions (created in TG 1.1)
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/spec.md` (lines 106-117) - ClaudeSDKClient configuration requirements: setting_sources, allowed_tools, mcp_servers, hooks, cwd

**Depends On**: Tasks 1.1.4

**Actions**:
- ⬜ **1.2.1.1**: CREATE FILE apps/core/backend/src/agent/spec_agent_service.py — Module docstring, imports: ClaudeSDKClient and ClaudeAgentOptions from claude_agent_sdk, message types (AssistantMessage, ResultMessage, SystemMessage, ToolUseBlock, TextBlock), get_session_mcp_server and SERVER_NAME from mcp_tools, database CRUD functions and connection, Agent/AgentCreate models. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **1.2.1.2**: CREATE CLASS SpecAgentService — Init with session_slug (str), working_dir (str). Private fields: _client (Optional[ClaudeSDKClient] = None), _agent_id (Optional[UUID] = None), _sdk_session_id (Optional[str] = None), _session_id (Optional[UUID] = None). (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **1.2.1.3**: CREATE FUNCTION SpecAgentService.connect(self, session_id: UUID) -> None — Create ClaudeAgentOptions with: mcp_servers={SERVER_NAME: get_session_mcp_server()}, allowed_tools=['mcp__session_state__*', 'Read', 'Write', 'Edit', 'Glob', 'Grep', 'Skill', 'Bash'], setting_sources=['project'], cwd=self.working_dir, max_turns=10. Create Agent DB record via create_agent(AgentCreate(session_id, agent_type='spec', model='claude-sonnet-4-5-20250929')). Create ClaudeSDKClient, call connect(). Store _client, _agent_id, _session_id. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **1.2.1.4**: CREATE FUNCTION SpecAgentService.send_message(self, prompt: str, turn_index: int) -> list[dict] — Persist user message as InteractiveMessage (role='user', block_type='text', content=prompt). Call self._client.query(prompt). Iterate receive_response() to collect blocks. For each AssistantMessage: extract content blocks, for each TextBlock persist as InteractiveMessage (role='assistant', block_type='text'). For each ToolUseBlock persist as (role='tool_use', block_type='tool_use', tool_name=block.name). Return list of block dicts [{role, block_type, content, tool_name}] for API response. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **1.2.1.5**: CREATE FUNCTION SpecAgentService.disconnect(self) -> None — If _client is not None, disconnect the ClaudeSDKClient. Update Agent DB record status to 'complete'. Reset _client to None. (`apps/core/backend/src/agent/spec_agent_service.py`)

### ⬜ Task Group 1.3: API Router — Chat send endpoint

**Objective**: FastAPI router with POST /chat/send endpoint that accepts session slug + user message, routes through SpecAgentService, persists blocks, returns response. Register router in main.py.

#### ⬜ Task 1.3.1: Create chat router with Pydantic models

**File**: `apps/core/backend/src/routers/chat.py`

**Description**: FastAPI router with POST /chat/send endpoint. Accepts session_slug and message in request body. Creates or retrieves SpecAgentService for the session. Sends message through agent, returns response blocks. Includes Pydantic request/response models. For CP1 (tracer bullet), a new SpecAgentService is created per request (no instance caching yet — that comes in CP2).

**Context to Load**:
- `apps/core/backend/src/main.py` (lines 1-66) - FastAPI app structure, middleware config, existing endpoint pattern
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-100) - SpecAgentService interface: connect(), send_message(), disconnect()
- `apps/core/backend/src/database/crud.py` (lines 266-293) - get_session_by_slug pattern for session lookup

**Depends On**: Tasks 1.2.1

**Actions**:
- ⬜ **1.3.1.1**: CREATE FILE apps/core/backend/src/routers/chat.py — Imports: FastAPI APIRouter, HTTPException, Pydantic BaseModel, SpecAgentService, get_async_session from database.connection, get_session_by_slug from database.crud. (`apps/core/backend/src/routers/chat.py`)
- ⬜ **1.3.1.2**: CREATE TYPE ChatSendRequest(BaseModel) — Fields: session_slug (str), message (str). (`apps/core/backend/src/routers/chat.py`)
- ⬜ **1.3.1.3**: CREATE TYPE ChatSendResponse(BaseModel) — Fields: blocks (list[dict]), turn_index (int). (`apps/core/backend/src/routers/chat.py`)
- ⬜ **1.3.1.4**: CREATE FUNCTION POST /chat/send — Route handler: parse ChatSendRequest. Look up session by slug via get_session_by_slug (404 if not found). Derive working_dir from session. Create SpecAgentService(session_slug, working_dir). Call connect(session_id). Call send_message(request.message, turn_index=0). Call disconnect(). Return ChatSendResponse with blocks and turn_index. (`apps/core/backend/src/routers/chat.py`)

#### ⬜ Task 1.3.2: Register chat router in main.py

**File**: `apps/core/backend/src/main.py`

**Description**: Import chat router and register with app.include_router(). This makes the /chat/send endpoint available on the FastAPI application.

**Context to Load**:
- `apps/core/backend/src/main.py` (lines 1-66) - Current app structure — import section and endpoint registration

**Depends On**: Tasks 1.3.1

**Actions**:
- ⬜ **1.3.2.1**: UPDATE apps/core/backend/src/main.py — ADD import: from routers.chat import router as chat_router. (`apps/core/backend/src/main.py`)
- ⬜ **1.3.2.2**: UPDATE apps/core/backend/src/main.py — ADD app.include_router(chat_router, prefix='/chat', tags=['chat']) after the health check endpoint section. (`apps/core/backend/src/main.py`)

### ⬜ Task Group 1.4: Frontend — Minimal chat panel + API integration

**Objective**: Create basic ChatPanel component with text input and message display. Create chat API client that calls backend. Wire into session detail page alongside existing tabs.

#### ⬜ Task 1.4.1: Create chat API client

**File**: `apps/core/frontend/src/lib/chat-api.ts`

**Description**: TypeScript API client for the backend chat endpoint. Provides sendMessage(sessionSlug, message) that POSTs to the FastAPI backend /chat/send and returns response blocks. Includes ChatBlock response type definition. Backend URL defaults to localhost:8000 for development.

**Context to Load**:
- `apps/core/frontend/src/lib/sessions-api.ts` (lines 1-50) - Existing API client pattern: fetch usage, error handling, type definitions

**Actions**:
- ⬜ **1.4.1.1**: CREATE FILE apps/core/frontend/src/lib/chat-api.ts — Module docstring. VAR BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'. (`apps/core/frontend/src/lib/chat-api.ts`)
- ⬜ **1.4.1.2**: CREATE TYPE ChatBlock — { role: string; block_type: string; content: string | null; tool_name: string | null }. CREATE TYPE ChatSendResponse — { blocks: ChatBlock[]; turn_index: number }. (`apps/core/frontend/src/lib/chat-api.ts`)
- ⬜ **1.4.1.3**: CREATE FUNCTION sendMessage(sessionSlug: string, message: string): Promise<ChatSendResponse> — POST to `${BACKEND_URL}/chat/send` with JSON body { session_slug: sessionSlug, message }. Headers: Content-Type application/json. Check response.ok, throw on error. Parse and return JSON as ChatSendResponse. (`apps/core/frontend/src/lib/chat-api.ts`)

#### ⬜ Task 1.4.2: Create ChatPanel component

**File**: `apps/core/frontend/src/components/chat/ChatPanel.tsx`

**Description**: Minimal chat panel with text input, send button, and message list. Renders user messages and agent text responses as simple bubbles (user right-aligned, assistant left-aligned). Uses sendMessage API client. Manages local messages state. Shows loading indicator during agent response.

**Context to Load**:
- `apps/core/frontend/src/components/phases/SpecView.tsx` (lines 1-150) - Existing component pattern: 'use client', useState, useEffect, loading/error states, Card component usage
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-50) - sendMessage function interface and ChatBlock type

**Depends On**: Tasks 1.4.1

**Actions**:
- ⬜ **1.4.2.1**: CREATE FILE apps/core/frontend/src/components/chat/ChatPanel.tsx — 'use client' directive. Imports: useState from react, sendMessage and ChatBlock from '@/lib/chat-api', Button from '@/components/ui/button', Input from '@/components/ui/input', Card/CardContent from '@/components/ui/card', cn from '@/lib/utils'. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **1.4.2.2**: CREATE TYPE ChatMessage — Local state type: { role: 'user' | 'assistant'; content: string; timestamp: string }. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **1.4.2.3**: CREATE FUNCTION ChatPanel({ sessionSlug }: { sessionSlug: string }) — State: messages (ChatMessage[]), inputValue (string), isLoading (boolean), error (string | null). Render: scrollable message list area with user messages right-aligned (bg-primary text-white) and assistant messages left-aligned (bg-muted). Bottom: form with Input and Button ('Send'). On submit: add user message to state, set isLoading, call sendMessage(), extract text blocks from response, add as assistant messages, clear input. Handle errors with error state display. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **1.4.2.4**: CREATE FILE apps/core/frontend/src/components/chat/index.ts — export { ChatPanel } from './ChatPanel'. (`apps/core/frontend/src/components/chat/index.ts`)

#### ⬜ Task 1.4.3: Integrate ChatPanel into session detail page

**File**: `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`

**Description**: Add ChatPanel alongside the existing phase tabs on the session detail page. For CP1 (tracer bullet), render it below the tabs as a separate section. The three-column layout restructuring comes in CP3.

**Context to Load**:
- `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx` (lines 1-203) - Current session detail page layout — understand where to add ChatPanel

**Depends On**: Tasks 1.4.2

**Actions**:
- ⬜ **1.4.3.1**: UPDATE apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx — ADD import { ChatPanel } from '@/components/chat'. (`apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)
- ⬜ **1.4.3.2**: UPDATE apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx — ADD after the closing </Tabs> component: <section className='mt-8'><h2 className='text-lg font-semibold mb-4'>Spec Interview</h2><ChatPanel sessionSlug={sessionSlug} /></section>. (`apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)

---

## ⬜ Checkpoint 2: Multi-Turn Conversation with Persistence

**Goal**: Enable full back-and-forth chat that persists across page loads. SDK session continuity via sdk_session_id, chat history loading, and multi-turn message rendering.

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/backend/src/routers/chat.py` | 📄 exists | Chat router with single send-message endpoint |
| Before | `apps/core/backend/src/agent/spec_agent_service.py` | 📄 exists | Basic SpecAgentService |
| Before | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📄 exists | Minimal chat panel |
| After | `apps/core/backend/src/routers/chat.py` | 📝 modified | Added GET /api/chat/history endpoint |
| After | `apps/core/backend/src/agent/spec_agent_service.py` | 📝 modified | Client lifecycle management, sdk_session_id persistence, multi-turn support |
| After | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📝 modified | Chat history loading, multi-turn rendering, scroll-to-bottom |
| After | `apps/core/frontend/src/lib/chat-api.ts` | ✨ new | Chat API client functions |

### Testing Strategy

**Approach**: Multi-turn conversation verification

**Verification Steps**:
- [ ] `Send multiple messages in sequence, agent maintains context`
- [ ] `Refresh page, chat history loads from database`
- [ ] `sdk_session_id stored in Agent model, reused across messages`
- [ ] `All blocks persisted with correct turn_index and block_index ordering`

### ⬜ Task Group 2.1: Backend — Client lifecycle & session management

**Objective**: Manage SpecAgentService instances across requests. Cache active clients per session. Store sdk_session_id in Agent model for conversation continuity. Handle client reuse for subsequent messages in the same session.

#### ⬜ Task 2.1.1: Add client registry for active SpecAgentService instances

**File**: `apps/core/backend/src/agent/spec_agent_service.py`

**Description**: Add a module-level dict for caching active clients by session_slug. Add get_or_create_service() and remove_service() helper functions. Update connect() to store sdk_session_id on the Agent model after SDK connect.

**Context to Load**:
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-100) - Current SpecAgentService implementation from CP1
- `apps/core/backend/src/database/models/agent.py` (lines 85-92) - Agent model sdk_session_id field for persistence
- `apps/core/backend/src/database/crud.py` (lines 550-580) - update_agent() function for updating Agent records

**Actions**:
- ⬜ **2.1.1.1**: ADD VAR _active_services: dict[str, SpecAgentService] = {} — Module-level client registry keyed by session_slug. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **2.1.1.2**: CREATE FUNCTION get_or_create_service(session_slug: str, working_dir: str, session_id: UUID) -> SpecAgentService — Check _active_services for existing client by session_slug. If found and _client is not None, return it. Otherwise create new SpecAgentService, call connect(session_id), store in _active_services, return. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **2.1.1.3**: CREATE FUNCTION remove_service(session_slug: str) -> None — Pop session_slug from _active_services. If service found, call disconnect(). (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **2.1.1.4**: UPDATE FUNCTION SpecAgentService.connect() — After SDK client.connect(), retrieve sdk_session_id from client session. Call update_agent(db, agent_id, AgentUpdate(sdk_session_id=sdk_session_id)). Store in self._sdk_session_id. (`apps/core/backend/src/agent/spec_agent_service.py`)

#### ⬜ Task 2.1.2: Update chat router for multi-turn support

**File**: `apps/core/backend/src/routers/chat.py`

**Description**: Replace per-request service creation with get_or_create_service(). Track turn_index by querying max turn_index from existing messages. Increment for each new send.

**Context to Load**:
- `apps/core/backend/src/routers/chat.py` (lines 1-60) - Current chat router from CP1
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-20) - get_or_create_service() function added in 2.1.1

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.1.2.1**: UPDATE FUNCTION POST /chat/send — REPLACE direct SpecAgentService creation with get_or_create_service(session_slug, working_dir, session_id). Query get_max_turn_index(db, session_id) for current max. Use max+1 as turn_index. Pass to send_message(). Remove disconnect() call (client stays alive for subsequent messages). Return incremented turn_index in response. (`apps/core/backend/src/routers/chat.py`)

### ⬜ Task Group 2.2: Backend — Chat history API

**Objective**: Add GET /chat/history endpoint that returns persisted messages for a session, ordered by turn_index/block_index. Support phase filtering.

#### ⬜ Task 2.2.1: Add chat history endpoint

**File**: `apps/core/backend/src/routers/chat.py`

**Description**: Add GET /chat/history/{session_slug} endpoint that returns all persisted interactive_messages for a session, ordered by turn_index then block_index. Support optional phase query param.

**Context to Load**:
- `apps/core/backend/src/routers/chat.py` (lines 1-60) - Existing router structure, session lookup pattern
- `apps/core/backend/src/database/crud.py` (lines 690-730) - list_messages_for_session() function

**Actions**:
- ⬜ **2.2.1.1**: CREATE TYPE ChatHistoryResponse(BaseModel) — Fields: messages (list[dict] with keys: role, block_type, content, tool_name, turn_index, block_index, timestamp), total (int). (`apps/core/backend/src/routers/chat.py`)
- ⬜ **2.2.1.2**: CREATE FUNCTION GET /chat/history/{session_slug} — Route handler with optional Query param phase (str | None). Validate session by slug. Call list_messages_for_session(db, session_id, phase=phase). Map InteractiveMessage objects to dicts. Return ChatHistoryResponse with messages and total count. (`apps/core/backend/src/routers/chat.py`)

#### ⬜ Task 2.2.2: Add CRUD function for max turn_index

**File**: `apps/core/backend/src/database/crud.py`

**Description**: Add get_max_turn_index(db, session_id) that returns the maximum turn_index from interactive_messages for a session, or -1 if no messages exist.

**Context to Load**:
- `apps/core/backend/src/database/crud.py` (lines 729-755) - count_logs_for_session pattern using sqlalchemy func

**Actions**:
- ⬜ **2.2.2.1**: CREATE FUNCTION get_max_turn_index(db: AsyncSession, session_id: UUID) -> int — from sqlalchemy import func. SELECT func.max(InteractiveMessage.turn_index) WHERE session_id. Return result or -1 if None. (`apps/core/backend/src/database/crud.py`)

### ⬜ Task Group 2.3: Frontend — Chat history loading & multi-turn UX

**Objective**: Load chat history on page mount. Support multi-turn conversation with proper scroll-to-bottom behavior. Maintain turn_index across sends.

#### ⬜ Task 2.3.1: Update chat API client for history

**File**: `apps/core/frontend/src/lib/chat-api.ts`

**Description**: Add getChatHistory(sessionSlug) function that fetches persisted messages from the backend history endpoint.

**Context to Load**:
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-50) - Existing chat-api client from CP1

**Actions**:
- ⬜ **2.3.1.1**: CREATE FUNCTION getChatHistory(sessionSlug: string, phase?: string): Promise<{ messages: ChatBlock[]; total: number }> — GET ${BACKEND_URL}/chat/history/${sessionSlug} with optional ?phase= param. Parse and return JSON. (`apps/core/frontend/src/lib/chat-api.ts`)

#### ⬜ Task 2.3.2: Update ChatPanel for history loading and multi-turn

**File**: `apps/core/frontend/src/components/chat/ChatPanel.tsx`

**Description**: On mount, load chat history from backend and populate messages state. Track turn_index locally (incrementing from last loaded turn). Add useRef for scroll container with auto-scroll to bottom on new messages.

**Context to Load**:
- `apps/core/frontend/src/components/chat/ChatPanel.tsx` (lines 1-100) - Current ChatPanel implementation from CP1
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-60) - getChatHistory function added in 2.3.1

**Depends On**: Tasks 2.3.1

**Actions**:
- ⬜ **2.3.2.1**: ADD useEffect for initial chat history loading — On mount (sessionSlug dependency), call getChatHistory(sessionSlug). Map response messages to ChatMessage[] and set as initial messages state. Derive initial turnIndex from max turn_index in loaded history (+1 for next send). (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **2.3.2.2**: ADD useRef<HTMLDivElement>(null) as scrollEndRef — Attach to an empty div at the bottom of the messages container. ADD useEffect that calls scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' }) whenever messages array changes. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **2.3.2.3**: UPDATE send handler — ADD turnIndex to component state (useState<number>(0)). After getChatHistory, set turnIndex from max. On send: use current turnIndex, increment after successful response. Append all assistant response blocks from response.blocks to messages array. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)

---

## ⬜ Checkpoint 3: Session Creation Flow + Three-Column Layout

**Goal**: New Session button creates session directory + state.json and immediately starts spec interview. Session detail page restructured into three-column layout: sidebar | artifact tabs | chat panel.

**Prerequisites**: Checkpoints 2

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx` | 📄 exists | Session detail page with full-width phase tabs |
| Before | `apps/core/frontend/src/components/layout/AppShell.tsx` | 📄 exists | Two-column layout (sidebar + main) |
| After | `apps/core/backend/src/routers/sessions.py` | ✨ new | Session creation endpoint |
| After | `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx` | 📝 modified | Three-column layout with chat panel |
| After | `apps/core/frontend/src/app/projects/[slug]/page.tsx` | 📝 modified | New Session button added |

### Testing Strategy

**Approach**: End-to-end session creation and layout verification

**Verification Steps**:
- [ ] `Click New Session, verify session directory + state.json created`
- [ ] `Agent starts spec interview automatically, first question appears in chat`
- [ ] `Three-column layout renders: sidebar, artifact center, chat right`
- [ ] `New session appears in sidebar immediately`

### ⬜ Task Group 3.1: Backend — Session creation endpoint

**Objective**: API endpoint to create a new session (filesystem directory + state.json + database record) and return the new session info.

#### ⬜ Task 3.1.1: Create session creation endpoint

**File**: `apps/core/backend/src/routers/sessions.py`

**Description**: FastAPI router with POST /sessions/create endpoint. Creates session directory under agents/sessions/, writes initial state.json, creates DB record via sync, and returns the new session info. Also register this router in main.py.

**Context to Load**:
- `apps/core/backend/src/state_manager/state_manager.py` (lines 1-50) - SessionStateManager pattern for creating state.json
- `apps/core/frontend/src/lib/session-sync.ts` (lines 84-161) - mapStateToSession — how state.json maps to DB record (reference for fields needed)
- `apps/core/backend/src/routers/chat.py` (lines 1-30) - Existing router pattern from CP1
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/state.json` (lines 1-30) - Example state.json structure for reference

**Actions**:
- ⬜ **3.1.1.1**: CREATE FILE apps/core/backend/src/routers/sessions.py — Imports: FastAPI APIRouter, HTTPException, BaseModel, Path, json, datetime, random, string. Database imports. (`apps/core/backend/src/routers/sessions.py`)
- ⬜ **3.1.1.2**: CREATE TYPE SessionCreateRequest(BaseModel) — Fields: project_path (str, the absolute path to the project root), topic (Optional[str] = None). (`apps/core/backend/src/routers/sessions.py`)
- ⬜ **3.1.1.3**: CREATE FUNCTION POST /sessions/create — Generate session_slug: YYYY-MM-DD_{slugified_topic or 'session'}_{6-char-random}. Create directory at {project_path}/agents/sessions/{slug}/. Write initial state.json with: session_id=slug, current_phase='spec', status='active', created_at/updated_at=now, phase_history with spec_started_at=now. Create DB session record via create_session(). Return { session_slug, session_id (UUID), session_dir }. (`apps/core/backend/src/routers/sessions.py`)
- ⬜ **3.1.1.4**: UPDATE apps/core/backend/src/main.py — ADD import: from routers.sessions import router as sessions_router. ADD app.include_router(sessions_router, prefix='/sessions', tags=['sessions']). (`apps/core/backend/src/main.py`)

### ⬜ Task Group 3.2: Frontend — New Session button & creation flow

**Objective**: 'New Session' button on project page that creates a session and navigates to the session detail page.

#### ⬜ Task 3.2.1: Add sessions API client function for creation

**File**: `apps/core/frontend/src/lib/sessions-api.ts`

**Description**: Add createSession() function that calls the backend session creation endpoint. Uses BACKEND_URL from chat-api pattern.

**Context to Load**:
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-10) - BACKEND_URL pattern for calling FastAPI backend
- `apps/core/frontend/src/lib/sessions-api.ts` (lines 1-50) - Existing sessions API client structure

**Actions**:
- ⬜ **3.2.1.1**: CREATE FUNCTION createSession(projectPath: string, topic?: string): Promise<{ session_slug: string; session_id: string; session_dir: string }> — POST to ${BACKEND_URL}/sessions/create with JSON body { project_path: projectPath, topic }. Parse and return response. (`apps/core/frontend/src/lib/sessions-api.ts`)

#### ⬜ Task 3.2.2: Add New Session button to project page

**File**: `apps/core/frontend/src/app/projects/[slug]/page.tsx`

**Description**: Add 'New Session' button in the project header area. On click, call createSession with project path and navigate to the new session detail page.

**Context to Load**:
- `apps/core/frontend/src/app/projects/[slug]/page.tsx` (lines 1-100) - Current project page layout — where to place the button
- `apps/core/frontend/src/lib/sessions-api.ts` (lines 1-30) - createSession function from 3.2.1

**Depends On**: Tasks 3.2.1

**Actions**:
- ⬜ **3.2.2.1**: ADD 'New Session' Button — In the project header/actions area. Import Button, Plus icon. Render <Button onClick={handleNewSession}><Plus /> New Session</Button>. (`apps/core/frontend/src/app/projects/[slug]/page.tsx`)
- ⬜ **3.2.2.2**: CREATE FUNCTION handleNewSession — Use window.prompt or a simple input for optional topic. Call createSession(project.path, topic). On success, router.push(`/projects/${projectSlug}/sessions/${result.session_slug}`). Handle errors with alert or error state. (`apps/core/frontend/src/app/projects/[slug]/page.tsx`)

### ⬜ Task Group 3.3: Frontend — Three-column layout restructuring

**Objective**: Restructure session detail page into three-column layout: AppShell sidebar (left, existing) | artifact tabs (center) | chat panel (right). All three always visible.

#### ⬜ Task 3.3.1: Restructure session detail page to three-column layout

**File**: `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`

**Description**: Replace current single-column layout with a flex container splitting artifact tabs (center, ~60%) and chat panel (right, ~40%). The AppShell sidebar is already handled in the layout. Make chat panel sticky for scroll independence. Remove the temporary section wrapper from CP1.

**Context to Load**:
- `apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx` (lines 1-203) - Current session detail page — understand full layout structure
- `apps/core/frontend/src/components/layout/AppShell.tsx` (lines 112-254) - AppShell provides sidebar (w-80) and main content area. Session page renders inside main.
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/spec.md` (lines 176-200) - Three-column layout spec: sidebar | artifact tabs | chat panel

**Actions**:
- ⬜ **3.3.1.1**: REFACTOR session detail page layout — Wrap the Tabs component and ChatPanel in a flex row container: <div className='flex gap-6'>. Tabs wrapper gets className='flex-1 min-w-0' (takes remaining space). ChatPanel wrapper gets className='w-[400px] shrink-0 sticky top-24 self-start max-h-[calc(100vh-8rem)] overflow-hidden'. (`apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)
- ⬜ **3.3.1.2**: REMOVE the temporary <section className='mt-8'> wrapper around ChatPanel — This was added in CP1 task 1.4.3.2. ChatPanel now lives directly in the flex layout. (`apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)
- ⬜ **3.3.1.3**: ADD sticky positioning to ChatPanel container — The ChatPanel's outer div should be position: sticky with top offset matching the header height. Add border-l border-border/50 for visual separation from artifact area. (`apps/core/frontend/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)

---

## ⬜ Checkpoint 4: Artifact Polling + Block-Type Rendering

**Goal**: Artifact view polls for spec.md changes using content hashing, only re-renders when content changes. Chat panel renders blocks by type: text as bubbles, tool_use/tool_result as collapsible activity indicators, thinking blocks hidden.

**Prerequisites**: Checkpoints 3

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/frontend/src/components/phases/SpecView.tsx` | 📄 exists | One-shot spec.md fetch |
| Before | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📄 exists | Basic message rendering |
| After | `apps/core/frontend/src/app/api/sessions/[slug]/spec/route.ts` | 📝 modified | Added content hash in response |
| After | `apps/core/frontend/src/components/phases/SpecView.tsx` | 📝 modified | Polling with hash comparison |
| After | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📝 modified | Block-type-aware rendering |
| After | `apps/core/frontend/src/components/chat/MessageBubble.tsx` | ✨ new | Text block rendering |
| After | `apps/core/frontend/src/components/chat/ToolActivity.tsx` | ✨ new | Collapsible tool use/result indicators |

### Testing Strategy

**Approach**: Polling verification and visual block rendering

**Verification Steps**:
- [ ] `Agent updates spec.md during conversation, artifact view refreshes automatically`
- [ ] `No re-render when content hash unchanged`
- [ ] `TextBlocks render as chat bubbles with proper styling`
- [ ] `ToolUseBlocks render as collapsible activity indicators`
- [ ] `ThinkingBlocks are hidden from chat panel`

### ⬜ Task Group 4.1: Backend — Artifact hash endpoint

**Objective**: Add content hash to spec artifact response so frontend can poll efficiently with hash comparison.

#### ⬜ Task 4.1.1: Add content hash to spec endpoint

**File**: `apps/core/frontend/src/app/api/sessions/[slug]/spec/route.ts`

**Description**: Add a content_hash field (SHA256 of spec content) to the spec endpoint response. Frontend uses this to detect content changes without full re-parsing.

**Context to Load**:
- `apps/core/frontend/src/app/api/sessions/[slug]/spec/route.ts` (lines 1-50) - Current spec endpoint implementation — understand response shape and file reading logic

**Actions**:
- ⬜ **4.1.1.1**: UPDATE GET /api/sessions/[slug]/spec — Import { createHash } from 'crypto'. After reading spec.md content, compute hash: createHash('sha256').update(content).digest('hex'). Add content_hash field to JSON response alongside content and exists. (`apps/core/frontend/src/app/api/sessions/[slug]/spec/route.ts`)

### ⬜ Task Group 4.2: Frontend — Artifact polling with hash comparison

**Objective**: SpecView polls for spec.md changes at regular intervals and only re-renders when content hash changes.

#### ⬜ Task 4.2.1: Add polling to SpecView

**File**: `apps/core/frontend/src/components/phases/SpecView.tsx`

**Description**: Add polling interval (5 seconds) that re-fetches spec content. Compare content_hash from response against last known hash. Only update content state if hash changed. Use useRef for hash tracking, useEffect with setInterval for polling.

**Context to Load**:
- `apps/core/frontend/src/components/phases/SpecView.tsx` (lines 1-150) - Current SpecView — one-shot fetch on mount, no polling
- `apps/core/frontend/src/lib/sessions-api.ts` (lines 127-152) - getSessionSpec function and SpecContent type

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.2.1.1**: UPDATE SpecContent interface in sessions-api.ts — ADD content_hash?: string field to SpecContent interface. (`apps/core/frontend/src/lib/sessions-api.ts`)
- ⬜ **4.2.1.2**: ADD useRef<string | null>(null) as lastHashRef — Track last known content hash in SpecView component. (`apps/core/frontend/src/components/phases/SpecView.tsx`)
- ⬜ **4.2.1.3**: ADD useEffect with setInterval(5000) for polling — On each tick: call getSessionSpec(sessionSlug). If response.content_hash differs from lastHashRef.current, update content state and set lastHashRef.current = response.content_hash. On initial load, also set lastHashRef. Clear interval on unmount via cleanup return. (`apps/core/frontend/src/components/phases/SpecView.tsx`)

### ⬜ Task Group 4.3: Frontend — Block-type-aware chat rendering

**Objective**: Chat panel renders blocks by type: text as bubbles, tool_use/tool_result as collapsible activity indicators, thinking blocks hidden.

#### ⬜ Task 4.3.1: Create MessageBubble component

**File**: `apps/core/frontend/src/components/chat/MessageBubble.tsx`

**Description**: Renders a single text block as a styled chat bubble. User messages right-aligned with primary color, assistant messages left-aligned with muted background. Supports markdown rendering for assistant messages.

**Context to Load**:
- `apps/core/frontend/src/components/chat/ChatPanel.tsx` (lines 1-30) - Current inline message rendering to understand what to extract
- `apps/core/frontend/src/lib/utils.ts` (lines 1-20) - cn() utility for className merging

**Actions**:
- ⬜ **4.3.1.1**: CREATE FILE apps/core/frontend/src/components/chat/MessageBubble.tsx — Props: { role: 'user' | 'assistant'; content: string }. User messages: ml-auto bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%]. Assistant messages: mr-auto bg-muted rounded-2xl rounded-bl-sm px-4 py-2 max-w-[80%]. Render content as text (or ReactMarkdown for assistant). (`apps/core/frontend/src/components/chat/MessageBubble.tsx`)

#### ⬜ Task 4.3.2: Create ToolActivity component

**File**: `apps/core/frontend/src/components/chat/ToolActivity.tsx`

**Description**: Renders tool_use and tool_result blocks as collapsible activity indicators. Shows tool name with an icon, initially collapsed. Click to expand and show content/details.

**Context to Load**:
- `apps/core/frontend/src/components/agents/EventItem.tsx` (lines 1-50) - Existing event rendering pattern for reference

**Actions**:
- ⬜ **4.3.2.1**: CREATE FILE apps/core/frontend/src/components/chat/ToolActivity.tsx — Props: { toolName: string; content: string | null; blockType: 'tool_use' | 'tool_result' }. Render as a small, muted row with wrench/gear icon + tool name. useState for isExpanded. On click toggle expanded. When expanded show content in a pre/code block. Style: text-xs text-muted-foreground border-l-2 border-muted pl-3 py-1. (`apps/core/frontend/src/components/chat/ToolActivity.tsx`)

#### ⬜ Task 4.3.3: Update ChatPanel for block-type rendering

**File**: `apps/core/frontend/src/components/chat/ChatPanel.tsx`

**Description**: Replace simple message rendering with block-type-aware rendering. Text blocks use MessageBubble, tool blocks use ToolActivity, thinking blocks are hidden. Update message state type to include block_type and tool_name.

**Context to Load**:
- `apps/core/frontend/src/components/chat/ChatPanel.tsx` (lines 1-100) - Current ChatPanel with basic rendering
- `apps/core/frontend/src/components/chat/MessageBubble.tsx` (lines 1-30) - MessageBubble component interface
- `apps/core/frontend/src/components/chat/ToolActivity.tsx` (lines 1-30) - ToolActivity component interface

**Depends On**: Tasks 4.3.1, 4.3.2

**Actions**:
- ⬜ **4.3.3.1**: UPDATE ChatMessage type — ADD block_type: 'text' | 'tool_use' | 'tool_result' | 'thinking' field. ADD tool_name: string | null field. DEFAULT block_type to 'text' for user messages. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **4.3.3.2**: UPDATE message rendering in ChatPanel — REPLACE inline message divs with block-type switch: if block_type === 'text' render <MessageBubble role={msg.role} content={msg.content} />. If block_type === 'tool_use' or 'tool_result' render <ToolActivity toolName={msg.tool_name} content={msg.content} blockType={msg.block_type} />. If block_type === 'thinking' return null (hidden). (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **4.3.3.3**: UPDATE exports in apps/core/frontend/src/components/chat/index.ts — ADD export { MessageBubble } from './MessageBubble'. ADD export { ToolActivity } from './ToolActivity'. (`apps/core/frontend/src/components/chat/index.ts`)

---

## ⬜ Checkpoint 5: AskUserQuestion UI + AgentLog Hooks + Phase Transition

**Goal**: AskUserQuestion renders as structured select/multi-select UI with Other option. PreToolUse/PostToolUse hooks write to AgentLog for observability. Continue to Plan button appears on spec finalization. SDK session resume enables mid-session return.

**Prerequisites**: Checkpoints 4

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/backend/src/agent/spec_agent_service.py` | 📄 exists | SpecAgentService without hooks or AskUserQuestion handling |
| Before | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📄 exists | Chat panel without AskUserQuestion rendering |
| After | `apps/core/backend/src/agent/spec_agent_service.py` | 📝 modified | Added hooks, AskUserQuestion interception, session resume |
| After | `apps/core/frontend/src/components/chat/AskUserQuestion.tsx` | ✨ new | Structured select/multi-select UI component |
| After | `apps/core/frontend/src/components/chat/ChatPanel.tsx` | 📝 modified | AskUserQuestion detection and rendering, Continue to Plan button |

### Testing Strategy

**Approach**: Interactive feature verification

**Verification Steps**:
- [ ] `AskUserQuestion renders as select UI with options and Other field`
- [ ] `User selection sent back as tool result, agent continues`
- [ ] `AgentLog entries created for all tool calls during conversation`
- [ ] `Continue to Plan button appears when spec is finalized`
- [ ] `Leave session and return, conversation resumes via sdk_session_id`

### ⬜ Task Group 5.1: Backend — AskUserQuestion interception

**Objective**: Detect AskUserQuestion tool calls in agent response, pause execution, return structured question to frontend, accept user's answer and route back to SDK.

#### ⬜ Task 5.1.1: Add AskUserQuestion handling to SpecAgentService

**File**: `apps/core/backend/src/agent/spec_agent_service.py`

**Description**: When processing response blocks, detect ToolUseBlock with name='AskUserQuestion'. Capture the input (questions, options) and return it to the caller as a pending question. Add send_tool_result() method for routing the user's answer back to the SDK.

**Context to Load**:
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-150) - Current SpecAgentService with send_message and block processing
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/spec.md` (lines 272-294) - AskUserQuestion spec: detection, rendering, response format

**Actions**:
- ⬜ **5.1.1.1**: UPDATE FUNCTION send_message() — When iterating response blocks, check for ToolUseBlock where block.name == 'AskUserQuestion'. If found: persist as interactive_message with block_type='tool_use' and tool_name='AskUserQuestion'. Extract question data from block.input. Return dict with pending_question={tool_use_id: block.id, questions: block.input['questions']} and the blocks collected so far. Stop processing further blocks. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **5.1.1.2**: CREATE FUNCTION send_tool_result(self, tool_use_id: str, result: dict) -> list[dict] — Create a tool result message with the user's answer formatted as {answers: {question: selected_option}}. Send to SDK via client. Continue processing response blocks from receive_response(). Persist new blocks to interactive_messages. Return block dicts. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **5.1.1.3**: ADD TYPE PendingQuestion — Dict structure: { tool_use_id: str, questions: list[{question: str, header: str, options: list[{label: str, description: str}], multiSelect: bool}] }. (`apps/core/backend/src/agent/spec_agent_service.py`)

### ⬜ Task Group 5.2: Backend — AgentLog hooks

**Objective**: Wire PreToolUse/PostToolUse hooks into SpecAgentService that write to AgentLog table for observability.

#### ⬜ Task 5.2.1: Add hook callbacks to SpecAgentService

**File**: `apps/core/backend/src/agent/spec_agent_service.py`

**Description**: Add PreToolUse and PostToolUse hook functions that create AgentLog entries. Wire hooks into ClaudeAgentOptions configuration.

**Context to Load**:
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-50) - connect() method where ClaudeAgentOptions is configured
- `apps/core/backend/src/database/models/agent_log.py` (lines 1-100) - AgentLog model and AgentLogCreate DTO structure
- `apps/core/backend/src/database/crud.py` (lines 607-641) - create_agent_log() function

**Actions**:
- ⬜ **5.2.1.1**: CREATE FUNCTION _pre_tool_hook(self, tool_name: str, tool_input: dict) — Create AgentLogCreate with agent_id=self._agent_id, session_id=self._session_id, event_category='hook', event_type='PreToolUse', tool_name=tool_name, tool_input=tool_input. Call create_agent_log() via database session. (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **5.2.1.2**: CREATE FUNCTION _post_tool_hook(self, tool_name: str, tool_output: str, duration_ms: int) — Create AgentLogCreate with event_category='hook', event_type='PostToolUse', tool_name=tool_name, tool_output=tool_output, duration_ms=duration_ms. Call create_agent_log(). (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **5.2.1.3**: UPDATE connect() — Add hooks parameter to ClaudeAgentOptions with pre_tool_use=self._pre_tool_hook and post_tool_use=self._post_tool_hook. (`apps/core/backend/src/agent/spec_agent_service.py`)

### ⬜ Task Group 5.3: Backend — Session resume

**Objective**: Support resuming an SDK session when user returns to an in-progress spec conversation.

#### ⬜ Task 5.3.1: Add resume support to SpecAgentService

**File**: `apps/core/backend/src/agent/spec_agent_service.py`

**Description**: When get_or_create_service() is called for a session that has an existing Agent with sdk_session_id, create the ClaudeSDKClient with resume=sdk_session_id parameter. This enables picking up exactly where the conversation left off.

**Context to Load**:
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-80) - get_or_create_service() and connect() methods
- `apps/core/backend/src/database/models/agent.py` (lines 85-92) - Agent model sdk_session_id field
- `apps/core/backend/src/database/crud.py` (lines 487-515) - list_agents_for_session() for finding existing spec agent

**Actions**:
- ⬜ **5.3.1.1**: UPDATE FUNCTION get_or_create_service() — Before creating a new service, query list_agents_for_session(db, session_id, agent_type='spec', status='executing' or 'waiting'). If found and agent.sdk_session_id is not None, pass resume_session_id=agent.sdk_session_id to service.connect(). (`apps/core/backend/src/agent/spec_agent_service.py`)
- ⬜ **5.3.1.2**: UPDATE FUNCTION SpecAgentService.connect() — Accept optional resume_session_id: str | None = None parameter. If provided, pass resume=resume_session_id to ClaudeSDKClient constructor. Reuse existing Agent record instead of creating new one. (`apps/core/backend/src/agent/spec_agent_service.py`)

### ⬜ Task Group 5.4: Frontend — AskUserQuestion UI + chat router updates + phase transition

**Objective**: Structured AskUserQuestion rendering in chat panel. Chat answer endpoint. Continue to Plan button on spec finalization.

#### ⬜ Task 5.4.1: Update chat router for AskUserQuestion flow

**File**: `apps/core/backend/src/routers/chat.py`

**Description**: Update POST /chat/send response to include pending_question when AskUserQuestion is detected. Add POST /chat/answer endpoint for submitting user answers to pending questions.

**Context to Load**:
- `apps/core/backend/src/routers/chat.py` (lines 1-80) - Current chat router with send and history endpoints
- `apps/core/backend/src/agent/spec_agent_service.py` (lines 1-50) - send_tool_result() method added in 5.1.1

**Depends On**: Tasks 5.1.1

**Actions**:
- ⬜ **5.4.1.1**: UPDATE ChatSendResponse — ADD Optional field: pending_question (Optional[dict] with tool_use_id, questions list). DEFAULT None. (`apps/core/backend/src/routers/chat.py`)
- ⬜ **5.4.1.2**: CREATE TYPE ChatAnswerRequest(BaseModel) — Fields: session_slug (str), tool_use_id (str), answers (dict[str, str]). (`apps/core/backend/src/routers/chat.py`)
- ⬜ **5.4.1.3**: CREATE FUNCTION POST /chat/answer — Route handler: get_or_create_service for session. Call service.send_tool_result(tool_use_id, answers). Return ChatSendResponse with new blocks (may contain another pending_question). (`apps/core/backend/src/routers/chat.py`)

#### ⬜ Task 5.4.2: Create AskUserQuestion component

**File**: `apps/core/frontend/src/components/chat/AskUserQuestion.tsx`

**Description**: Renders structured question UI from AskUserQuestion tool call. Single-select as selectable chips, multi-select as checkboxes. Always includes 'Other' free-text option. On submit, formats answer and calls onAnswer callback.

**Context to Load**:
- `agents/sessions/2026-02-19_connect-spec-plan-build-to-frontend-sess_enr0i6/spec.md` (lines 272-294) - AskUserQuestion spec: rendering rules, answer format
- `apps/core/frontend/src/components/ui/button.tsx` (lines 1-30) - Button component variants for option rendering

**Actions**:
- ⬜ **5.4.2.1**: CREATE FILE apps/core/frontend/src/components/chat/AskUserQuestion.tsx — Props: { question: string; header: string; options: Array<{label: string; description: string}>; multiSelect: boolean; onAnswer: (answer: string) => void }. State: selectedOptions (string[] for multi, string for single), otherText (string), showOther (boolean). Render: header as label, options as clickable chips/cards with selected state styling (outline vs filled), 'Other' option with text input, Submit button. On submit: format selected option(s) as comma-separated string (or otherText), call onAnswer. (`apps/core/frontend/src/components/chat/AskUserQuestion.tsx`)

#### ⬜ Task 5.4.3: Update ChatPanel for AskUserQuestion and phase transition

**File**: `apps/core/frontend/src/components/chat/ChatPanel.tsx`

**Description**: When response contains pending_question, render AskUserQuestion component instead of text input. On answer, call /chat/answer endpoint. Add 'Continue to Plan' button when spec phase is finalized.

**Context to Load**:
- `apps/core/frontend/src/components/chat/ChatPanel.tsx` (lines 1-120) - Current ChatPanel with send handler and message rendering
- `apps/core/frontend/src/components/chat/AskUserQuestion.tsx` (lines 1-50) - AskUserQuestion component interface
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-70) - sendAnswer function (added in 5.4.4)

**Depends On**: Tasks 5.4.2, 5.4.4

**Actions**:
- ⬜ **5.4.3.1**: ADD pendingQuestion state — useState<{tool_use_id: string, questions: any[]} | null>(null). After sendMessage response, check if response.pending_question exists. If so, set pendingQuestion state. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **5.4.3.2**: ADD AskUserQuestion rendering — When pendingQuestion is not null, render AskUserQuestion component in the input area (replacing the text input). For each question in pendingQuestion.questions, render an AskUserQuestion. OnAnswer callback: call sendAnswer(sessionSlug, pendingQuestion.tool_use_id, {question: answer}). Clear pendingQuestion. Add response blocks to messages. Check for new pending_question in response. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)
- ⬜ **5.4.3.3**: ADD Continue to Plan button — Accept session prop or poll session state. When session.current_phase changes from 'spec' to 'plan' (or spec is finalized), show a prominent 'Continue to Plan' button at the bottom of the chat panel. On click: navigate to ?phase=plan tab or call phase transition API. (`apps/core/frontend/src/components/chat/ChatPanel.tsx`)

#### ⬜ Task 5.4.4: Update chat API client for answer endpoint

**File**: `apps/core/frontend/src/lib/chat-api.ts`

**Description**: Add sendAnswer() function for submitting AskUserQuestion answers to the backend.

**Context to Load**:
- `apps/core/frontend/src/lib/chat-api.ts` (lines 1-60) - Existing chat API client

**Actions**:
- ⬜ **5.4.4.1**: CREATE FUNCTION sendAnswer(sessionSlug: string, toolUseId: string, answers: Record<string, string>): Promise<ChatSendResponse> — POST to ${BACKEND_URL}/chat/answer with JSON body { session_slug: sessionSlug, tool_use_id: toolUseId, answers }. Parse and return as ChatSendResponse. (`apps/core/frontend/src/lib/chat-api.ts`)

---

---
*Auto-generated from plan.json on 2026-02-19 12:59*