# Frontend Structure & Architecture Summary

## Overview

The orchestrator_3_stream frontend is a **Vue 3 + TypeScript + Pinia** single-page application that provides real-time visualization and management of multi-agent orchestration. It uses WebSocket for live event streaming and Axios for HTTP API communication with a FastAPI backend.

**Key Technologies:**
- Vue 3 (Composition API)
- TypeScript for type safety
- Pinia for state management
- Vite for build tooling
- Axios for HTTP communication
- WebSocket for real-time updates
- DOMPurify for XSS protection
- Highlight.js for code syntax highlighting
- Marked for markdown rendering

---

## Key Frontend Nodes - Quick Reference

**Components:**
- **App.vue**: Root 3-column grid layout managing agents, events, and chat sidebars
- **AppHeader.vue**: Displays real-time stats (active/running agents, logs, cost) and control buttons
- **AgentList.vue**: Left sidebar rendering agent cards with O(1) pulsing animations on events
- **EventStream.vue**: Center column displaying filtered/searchable log entries with auto-scroll
- **OrchestratorChat.vue**: Right sidebar chat interface with typing indicator and multiple message types
- **GlobalCommandInput.vue**: Cmd+K command palette overlay showing slash commands and agent templates
- **FilterControls.vue**: Multi-level filter UI combining agent, level, category, tool, and regex search filters

**Composables (Reusable Logic):**
- **useAgentPulse**: O(1) Set-based composable managing pulsing animations for high-frequency events
- **useEventStreamFilter**: Provides multi-dimensional filtering, regex search, and filter state management
- **useHeaderBar**: Aggregates stats, cost tracking, and CWD computations for header display
- **useKeyboardShortcuts**: Handles global keyboard events (Cmd+K / Ctrl+K)

**Services (API Communication):**
- **chatService.ts**: Manages WebSocket connection and HTTP chat (messages, history, streaming)
- **agentService.ts**: HTTP operations for agent management and list queries
- **eventService.ts**: HTTP queries for event history with filtering and pagination
- **api.ts**: Centralized Axios instance with error handling and base URL configuration

**Core Files:**
- **orchestratorStore.ts**: Central Pinia store managing agents, events, chat, WebSocket connection
- **types.d.ts**: 50+ TypeScript interfaces mirroring database models and UI types

---

## Directory Structure

```
frontend/
├── src/
│   ├── main.ts                          # Vue app entry point & Pinia setup
│   ├── App.vue                          # Root component (3-column layout)
│   ├── types.d.ts                       # TypeScript interface definitions
│   │
│   ├── components/                      # Vue components
│   │   ├── AppHeader.vue               # Top header with stats and controls
│   │   ├── AgentList.vue               # Left sidebar: agent list with pulsing
│   │   ├── EventStream.vue             # Center: live event log display
│   │   ├── OrchestratorChat.vue        # Right sidebar: chat interface
│   │   ├── FilterControls.vue          # Filter UI component
│   │   ├── GlobalCommandInput.vue      # Cmd+K command palette
│   │   ├── chat/                       # Chat-specific components
│   │   │   ├── ThinkingBubble.vue     # Displays orchestrator thinking blocks
│   │   │   └── ToolUseBubble.vue      # Displays tool use actions
│   │   └── event-rows/                 # Event row renderers
│   │       ├── AgentLogRow.vue
│   │       ├── SystemLogRow.vue
│   │       ├── OrchestratorChatRow.vue
│   │       ├── AgentToolUseBlockRow.vue
│   │       ├── FileChangesDisplay.vue
│   │       └── ToolUseBlockRow.vue
│   │
│   ├── stores/                          # Pinia state management
│   │   └── orchestratorStore.ts        # Main application state & actions
│   │
│   ├── composables/                    # Vue composables for logic reuse
│   │   ├── useAgentPulse.ts           # Manages pulsing animations (O(1) optimized)
│   │   ├── useEventStreamFilter.ts    # Event filtering & search logic
│   │   ├── useHeaderBar.ts            # Header stats & cost tracking
│   │   ├── useAgentColors.ts          # Agent color assignment utilities
│   │   └── useKeyboardShortcuts.ts    # Global keyboard handlers (Cmd+K)
│   │
│   ├── services/                       # HTTP/WebSocket communication
│   │   ├── api.ts                     # Axios instance with error handling
│   │   ├── chatService.ts             # Chat HTTP & WebSocket handlers
│   │   ├── agentService.ts            # Agent HTTP operations
│   │   ├── eventService.ts            # Event history HTTP queries
│   │   └── fileService.ts             # File tracking utilities
│   │
│   ├── utils/                          # Utility functions
│   │   ├── markdown.ts                # Markdown rendering with XSS protection
│   │   └── agentColors.ts             # Color palette utilities
│   │
│   ├── config/                         # Configuration constants
│   │   └── constants.ts               # API limits, defaults
│   │
│   ├── data/                           # Test/mock data
│   │   └── testData.ts                # Sample agents, logs, chat for UI dev
│   │
│   └── styles/
│       └── global.css                  # Dark theme with cyan/teal accents
│
├── vite.config.ts                      # Vite configuration
├── index.html                          # HTML entry point
├── package.json                        # Dependencies
└── tsconfig.json                       # TypeScript config
```

---

## Component Architecture Diagram

```mermaid
graph TB
    subgraph "Entry Point"
        main["main.ts<br/>Vue App + Pinia"]
    end

    subgraph "Root Layout"
        app["App.vue<br/>3-Column Layout"]
        appheader["AppHeader.vue<br/>Stats & Controls"]
    end

    subgraph "Left Sidebar - Agent Management"
        agentlist["AgentList.vue<br/>Agent Cards with Pulse"]
    end

    subgraph "Center Column - Event Stream"
        eventstream["EventStream.vue<br/>Log Display & Filtering"]
        filtercontrols["FilterControls.vue<br/>Tab/Search/Level Filters"]
        eventrows["Event Row Components<br/>AgentLogRow, SystemLogRow, etc."]
    end

    subgraph "Right Sidebar - Chat"
        orchchat["OrchestratorChat.vue<br/>Chat Messages & Input"]
        chatcomponents["Chat Bubbles<br/>ThinkingBubble, ToolUseBubble"]
    end

    subgraph "Global Overlays"
        globalcmd["GlobalCommandInput.vue<br/>Cmd+K Palette"]
    end

    subgraph "State Management"
        store["orchestratorStore<br/>Pinia Central Store"]
    end

    subgraph "Composables - Reusable Logic"
        agentpulse["useAgentPulse<br/>O(1) Pulse Animations"]
        filtercomposable["useEventStreamFilter<br/>Multi-Level Filtering"]
        headerbar["useHeaderBar<br/>Stats & Cost Tracking"]
        keyboard["useKeyboardShortcuts<br/>Global Shortcuts"]
        colors["useAgentColors<br/>Color Assignment"]
    end

    subgraph "Services - API Communication"
        api["api.ts<br/>Axios Instance"]
        chatservice["chatService.ts<br/>Chat HTTP & WebSocket"]
        agentservice["agentService.ts<br/>Agent Operations"]
        eventservice["eventService.ts<br/>Event History"]
        fileservice["fileService.ts<br/>File Tracking"]
    end

    subgraph "Backend APIs"
        http["HTTP Endpoints<br/>/list_agents, /get_events, etc."]
        websocket["WebSocket Connection<br/>ws://localhost:9403/ws"]
    end

    main --> app
    app --> appheader
    app --> agentlist
    app --> eventstream
    app --> orchchat
    app --> globalcmd

    eventstream --> filtercontrols
    eventstream --> eventrows
    orchchat --> chatcomponents

    appheader --> store
    agentlist --> store
    eventstream --> store
    orchchat --> store
    globalcmd --> store

    store --> agentpulse
    store --> filtercomposable
    store --> keyboard

    appheader --> headerbar
    eventstream --> filtercomposable

    store --> api
    store --> chatservice
    chatservice --> websocket

    eventstream --> eventservice
    agentlist --> agentservice
    orchchat --> chatservice

    api --> http
    chatservice --> http
    agentservice --> http
    eventservice --> http
    fileservice --> http
```

---

## State Management (Pinia Store)

### orchestratorStore.ts (1004 lines)

**Central state container** managing all application data and WebSocket connections.

#### State Variables
| Variable | Type | Purpose |
|----------|------|---------|
| `agents` | `Agent[]` | All active orchestrator agents |
| `selectedAgentId` | `string \| null` | Currently selected agent |
| `orchestratorAgentId` | `string` | Main orchestrator UUID |
| `orchestratorAgent` | `OrchestratorAgent \| null` | Main orchestrator metadata |
| `eventStreamEntries` | `EventStreamEntry[]` | All log events (1000+ entries) |
| `eventStreamFilter` | `EventStreamFilter` | Current filter mode |
| `autoScroll` | `boolean` | Auto-scroll to new events |
| `chatMessages` | `ChatMessage[]` | Conversation history |
| `isTyping` | `boolean` | Typing indicator state |
| `isConnected` | `boolean` | WebSocket connection status |
| `commandInputVisible` | `boolean` | Global command palette visibility |
| `chatWidth` | `'sm' \| 'md' \| 'lg'` | Chat panel width |
| `fileTrackingEvents` | `Map<string, any>` | File changes by parent log ID |

#### Key Computed Properties
- **`activeAgents`** - Non-archived, non-complete agents
- **`runningAgents`** - Agents with `status === 'executing'`
- **`selectedAgent`** - Current selected agent object
- **`filteredEventStream`** - Events filtered by type (errors/hooks/responses)
- **`stats`** - Aggregated AppStats for header display

#### Key Actions
- **Initialization**: `initialize()` → loads orchestrator info, connects WebSocket, loads agents/chat/events
- **Chat**: `loadChatHistory()`, `sendUserMessage()`, `clearChat()`, `toggleChatWidth()`
- **WebSocket**: `connectWebSocket()`, `disconnectWebSocket()`, handles all incoming events
- **Event Stream**: `addAgentLogEvent()`, `addOrchestratorChatEvent()`, `fetchEventHistory()`
- **Agent Management**: `loadAgents()`, `selectAgent()`, `updateAgent()`, `removeAgent()`
- **Events**: `addEventStreamEntry()`, `setEventStreamFilter()`, `toggleAutoScroll()`, `exportEventStream()`

#### WebSocket Event Handlers
- `onAgentLog` → Creates EventStreamEntry for agent activities
- `onOrchestratorChat` → Adds chat message to both event stream and chat UI
- `onThinkingBlock` → Displays orchestrator internal reasoning
- `onToolUseBlock` → Shows tool invocations with parameters
- `onAgentCreated/Updated/Deleted` → Updates agent list
- `onAgentStatusChange` → Real-time agent status updates
- `onOrchestratorUpdated` → Updates cost and token counts

---

## Component Details

### App.vue (220 lines)
**Root component** implementing the 3-column grid layout.

**Structure:**
- Header area
- Main grid: Left sidebar (agents) | Center (event stream) | Right (chat)
- Global command input overlay

**Features:**
- Responsive grid layout with breakpoints (1024px, 1200px, 1400px, 1600px)
- Sidebar collapse animation
- Dynamic chat width (sm/md/lg)
- Component communication via events

**Key Props/Events:**
- Emits filter changes to EventStream
- Handles agent selection with auto-filtering
- Manages sidebar collapse state

---

### AppHeader.vue (223 lines)
**Top navigation bar** displaying real-time statistics and controls.

**Displays:**
- Application title "MULTI-AGENT ORCHESTRATION"
- Connection status (green pulsing dot when connected)
- Live stats: Active agents, Running agents, Event log count, Total cost
- Action buttons: CLEAR ALL, PROMPT (Cmd+K)

**Dependencies:**
- `useHeaderBar()` composable for stats
- `orchestratorStore` for connection status

---

### AgentList.vue (834 lines)
**Left sidebar** showing paginated agent cards with real-time status and pulsing animations.

**Features:**
- Agent cards with status indicators (idle/executing/waiting/blocked/complete)
- Live token and cost counters
- Smooth pulsing animations triggered on tool use, hooks, thinking blocks
- Agent collapse toggle
- Search/filter by agent name
- Archived agent toggle view

**Key Composables:**
- `useAgentPulse()` → Triggers pulse animations on relevant events
- `useAgentColors()` → Assigns consistent colors to agents

---

### EventStream.vue (380 lines)
**Center column** displaying scrollable log entries with filtering and search.

**Features:**
- Virtualized list rendering for performance (1000+ entries)
- Multiple filter types: tabs, agent filters, quick level filters, search
- Regex search support across all event fields
- Auto-scroll to new entries
- Line numbers for easy reference
- Syntax highlighting in code blocks

**Props:**
- `events` - EventStreamEntry[] to display
- `currentFilter` - Active filter string
- `autoScroll` - Enable/disable auto-scroll

**Events:**
- `set-filter` - Emitted when filter changes

---

### OrchestratorChat.vue (662 lines)
**Right sidebar** chat interface for user-orchestrator communication.

**Features:**
- Message display with sender differentiation (user/orchestrator)
- Support for multiple message types: text, thinking blocks, tool use
- Typing indicator during orchestrator responses
- Input field with send button
- Auto-scroll to latest message
- Thinking and Tool Use bubble components

**Props:**
- `messages` - ChatMessage[] history
- `isConnected` - WebSocket connection status
- `isTyping` - Show typing indicator
- `autoScroll` - Enable/disable auto-scroll

**Events:**
- `send` - Emitted when user sends message

---

### FilterControls.vue (352 lines)
**Reusable filter UI component** displayed in EventStream.

**Sections:**
1. **Main Tabs** - Combined Stream view selector
2. **Quick Filters** - By log level (DBG, INF, WARN, ERR, OK)
3. **Category Filters** - RESPONSE, TOOL, THINKING, HOOK
4. **Agent Filters** - Dynamic list from event agents
5. **Tool Filters** - Specific tools used by agents
6. **Search Bar** - Regex or text search
7. **Auto-scroll Toggle** - Follow new entries

**Emitted Events:**
- `toggle-*-filter` - Various filter toggles
- `set-search` - Search query updates

---

### GlobalCommandInput.vue (710 lines)
**Command palette overlay** (Cmd+K / Ctrl+K).

**Displays:**
- System information panel (session ID, CWD, model info)
- Slash commands as cyan badges (from backend discovery)
- Agent templates as green badges (for spawning subagents)
- Search/filter commands
- Keyboard shortcuts help

**Data Sources:**
- Backend `/get_orchestrator` endpoint provides slash commands & templates

---

### Event Row Components

Located in `src/components/event-rows/`:

| Component | Purpose |
|-----------|---------|
| **AgentLogRow.vue** | Displays agent events with markdown content and file tracking |
| **SystemLogRow.vue** | System-level logs with level badge coloring |
| **OrchestratorChatRow.vue** | Chat messages with participant info |
| **ToolUseBlockRow.vue** | Tool invocations with parameters and results |
| **AgentToolUseBlockRow.vue** | Agent-specific tool usage display |
| **FileChangesDisplay.vue** | File modifications tracked by agents (diffs, summaries) |

**Common Features:**
- Markdown rendering with syntax highlighting
- DOMPurify XSS protection
- Timestamp display
- Agent/source identification
- Copy-to-clipboard buttons

---

## Composables (Reusable Logic)

### useAgentPulse.ts (120 lines)
**High-performance pulse animation manager** with aggressive debouncing.

**Key Features:**
- O(1) agent lookup using `Set<string>`
- Plain object for timer storage (faster than Map)
- Aggressive debouncing (400ms) prevents animation thrashing
- Batch Vue reactivity updates

**Exports:**
```typescript
triggerPulse(agentId)           // Start pulse animation
isAgentPulsing(agentId)         // Check if pulsing (O(1))
getAgentPulseClass(agentId)     // Get CSS class
clearAllPulses()                // Cleanup on disconnect
getPulsingAgents()              // Get all pulsing agents
isPulsing                       // Reactive Set for template bindings
```

**Performance:** Handles 1000+ simultaneous pulses with minimal CPU/GPU overhead.

---

### useEventStreamFilter.ts (362 lines)
**Comprehensive event filtering and search logic.**

**Filter Types:**
1. **Main Tabs** - "Combined Stream" (extensible)
2. **Agent Filters** - By agent name (dynamic from events)
3. **Category Filters** - RESPONSE, TOOL, THINKING, HOOK
4. **Tool Filters** - Specific tools used
5. **Quick Filters** - Log levels (DEBUG, INFO, WARNING, ERROR, SUCCESS)
6. **Search** - Regex or text search across multiple fields:
   - Content, event type, agent name
   - Summary, task slug, session ID
   - ADW fields, file paths
   - Orchestrator chat messages

**Exports:**
- State refs: `currentFilter`, `activeAgentFilters`, `searchQuery`, `autoScroll`
- Computed: `filteredEvents` (applies all filters)
- Helpers: `toggleQuickFilter()`, `toggleAgentFilter()`, etc.

---

### useHeaderBar.ts (217 lines)
**Header statistics and cost tracking composable.**

**Computed Properties:**
- `activeAgentCount` - Non-archived agents
- `runningAgentCount` - Currently executing
- `logCount` - Event stream size
- `orchestratorCost` - Main orchestrator spend
- `totalAgentCost` - All subagents spend
- `totalCombinedCost` - Total spend
- `costBreakdown` - Detailed breakdown object
- `cwd` - Current working directory

**Actions:**
- `fetchCwd()` - Load CWD from backend `/get_headers`
- `clearEventStream()` - Delegate to store
- `exportEventStream()` - Delegate to store

---

### useKeyboardShortcuts.ts
**Global keyboard event handlers.**

**Shortcuts:**
- **Cmd+K / Ctrl+K** - Toggle command palette

---

### useAgentColors.ts
**Consistent color assignment for agents.**

Generates stable colors from agent names/IDs for UI consistency.

---

## Services (API Communication)

### api.ts (42 lines)
**Axios instance with centralized configuration.**

**Configuration:**
- Base URL: `http://127.0.0.1:9403` (from `VITE_API_BASE_URL`)
- Timeout: 30 seconds
- Content-Type: application/json

**Error Interceptor:**
- Logs API errors to console
- Provides detailed error context (status, response data)

---

### chatService.ts (150+ lines)
**HTTP and WebSocket communication for chat and orchestrator interaction.**

**HTTP Methods:**
- `getOrchestratorInfo()` → GET `/get_orchestrator`
- `loadChatHistory(orchestratorAgentId, limit)` → POST `/load_chat`
- `sendMessage(message, orchestratorAgentId)` → POST `/send_chat`

**WebSocket Handler:**
- `connectWebSocket(url, callbacks)` → Establishes connection
- Routes by message type to appropriate callbacks:
  - `chat_stream`, `chat_typing`, `agent_log`
  - `orchestrator_chat`, `thinking_block`, `tool_use_block`
  - `agent_created`, `agent_updated`, `agent_deleted`
  - `agent_status_changed`, `agent_summary_update`
  - `orchestrator_updated`, `error`

---

### agentService.ts (16 lines)
**Agent management HTTP operations.**

**Methods:**
- `loadAgents()` → GET `/list_agents` returns all active agents

---

### eventService.ts (42 lines)
**Event history querying.**

**Methods:**
- `getEvents(params)` → GET `/get_events` with filters:
  - `agent_id` - Filter by agent
  - `task_slug` - Filter by task
  - `event_types` - "all" or comma-separated types
  - `limit` - Result limit (default 300)
  - `offset` - Pagination offset

**Response:** `{status, events: UnifiedEvent[], count}`

---

### fileService.ts
**File tracking and diff utilities.**

Handles file changes, reads, diffs, and summaries.

---

## Type Definitions (types.d.ts)

Comprehensive TypeScript interfaces mirroring backend database models:

### Core Types
- **`Agent`** - Subagent with tokens, cost, status
- **`OrchestratorAgent`** - Main orchestrator metadata
- **`AgentLog`** - Event log entry from agents
- **`SystemLog`** - System-level logging
- **`OrchestratorChat`** - Chat message

### UI Types
- **`EventStreamEntry`** - Unified event format for display
- **`ChatMessage`** - Union of TextChatMessage | ThinkingChatMessage | ToolUseChatMessage
- **`AppStats`** - Header statistics aggregation

### API Response Types
- **`GetOrchestratorResponse`** - Orchestrator info + slash commands + templates
- **`LoadChatResponse`** - Chat history with message array
- **`SendChatResponse`** - Send confirmation

---

## Styling & Theme

### global.css
**Dark theme** with cyan/teal accent colors.

**CSS Variables:**
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary` - Background colors
- `--text-primary`, `--text-secondary`, `--text-muted` - Text colors
- `--accent-primary` - Cyan accent
- `--status-*` - Status indicator colors
- `--spacing-*` - Consistent spacing
- `--border-color` - Border styling
- `--font-mono` - Monospace font for code

**Utility Classes:**
- `.agent-pulsing` - Pulsing animation (GPU-accelerated)
- `.status-badge` - Status indicator styling
- `.event-row` - Event entry styling

---

## Data Flow & Real-Time Updates

```
Backend Events (WebSocket)
    ↓
chatService.connectWebSocket()
    ↓
orchestratorStore handlers
    ├→ addAgentLogEvent()
    ├→ addOrchestratorChatEvent()
    ├→ addThinkingBlockEvent()
    ├→ addToolUseBlockEvent()
    ├→ handleAgentStatusChange()
    └→ handleOrchestratorUpdated()
    ↓
Pinia store updates (agents, eventStreamEntries, chatMessages)
    ↓
Components reactively update
    ├→ AgentList (pulse animations)
    ├→ EventStream (new log entries)
    └→ OrchestratorChat (incoming messages)
```

---

## Performance Optimizations

1. **useAgentPulse**: O(1) Set-based lookups for high-frequency events
2. **Event Filtering**: Computed properties prevent re-filtering on every render
3. **Virtual Scrolling**: EventStream supports 1000+ entries without lag
4. **Batch Reactivity**: Array spread patterns trigger Vue reactivity once
5. **Debounced Pulse**: 400ms debounce prevents animation thrashing
6. **GPU-Accelerated Animation**: CSS `transform` and `will-change`

---

## Environment Variables

Located in `.env` (not committed):

```bash
VITE_API_BASE_URL=http://127.0.0.1:9403
VITE_WEBSOCKET_URL=ws://127.0.0.1:9403/ws
```

---

## Build & Development

**Build Tool:** Vite
- Lightning-fast HMR (Hot Module Replacement)
- TypeScript support via esbuild
- Vue 3 SFC compilation

**Development Server:** `npm run dev` (port 5175)
**Production Build:** `npm run build`
**Preview:** `npm run preview`

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Pinia (not Context API)** | Centralized state prevents prop drilling in deep tree |
| **Composables** | Logic reuse without component coupling |
| **WebSocket** | Real-time updates without polling overhead |
| **Set data structures** | O(1) agent pulse lookups for high-frequency events |
| **Array spread for reactivity** | Explicit Vue 3 reactive updates (no implicit mutations) |
| **TypeScript interfaces** | Type safety prevents runtime errors |
| **DOMPurify** | XSS protection for user/agent-generated content |

---

## Testing & Validation

- Use **Playwright MCP** for frontend automation testing
- Test data in `src/data/testData.ts` for UI development
- Components support both real and mock WebSocket data

---

## File Size Summary

| File | Lines | Purpose |
|------|-------|---------|
| orchestratorStore.ts | 1004 | Central state management |
| AgentList.vue | 834 | Agent card display |
| OrchestratorChat.vue | 662 | Chat interface |
| GlobalCommandInput.vue | 710 | Command palette |
| useEventStreamFilter.ts | 362 | Filtering logic |
| EventStream.vue | 380 | Event log display |
| chatService.ts | 150+ | API communication |
| types.d.ts | 358+ | Type definitions |

---

## Summary

The frontend architecture is a **high-performance, real-time monitoring dashboard** built on Vue 3 with centralized Pinia state management. It handles 1000+ simultaneous events with O(1) performance optimizations, supports multi-dimensional filtering and search, and provides a smooth user experience through GPU-accelerated animations and responsive design.

Key strengths:
- ✅ Type-safe throughout
- ✅ Modular component structure
- ✅ Reusable composable logic
- ✅ Real-time WebSocket integration
- ✅ Performance-optimized for high-frequency events
- ✅ Comprehensive filtering and search
- ✅ Accessible and responsive design

---

## Extended Architecture Diagram - Detailed Dependencies

```mermaid
graph TB
    subgraph "Application Boot"
        A["main.ts<br/>createApp + Pinia"]
    end

    subgraph "Root Component"
        B["App.vue<br/>3-Column Grid<br/>Layout Manager"]
    end

    subgraph "Header Layer"
        C["AppHeader.vue<br/>Stats Display"]
        C1["useHeaderBar<br/>Composable"]
    end

    subgraph "Left Sidebar - Agents"
        D["AgentList.vue<br/>Agent Cards<br/>Pagination"]
        D1["useAgentPulse<br/>Composable"]
        D2["useAgentColors<br/>Utilities"]
    end

    subgraph "Center Column - Events"
        E["EventStream.vue<br/>Virtualized List<br/>Auto-scroll"]
        E1["FilterControls.vue<br/>Multi-level Filters"]
        E2["useEventStreamFilter<br/>Composable"]
        E3["Event Row Components<br/>AgentLogRow<br/>SystemLogRow<br/>OrchestratorChatRow<br/>ToolUseBlockRow<br/>FileChangesDisplay"]
        E4["markdown.ts<br/>Markdown Renderer<br/>+ DOMPurify"]
    end

    subgraph "Right Sidebar - Chat"
        F["OrchestratorChat.vue<br/>Message Display<br/>Typing Indicator"]
        F1["ThinkingBubble.vue<br/>Display Thinking"]
        F2["ToolUseBubble.vue<br/>Display Tool Use"]
    end

    subgraph "Global Overlays"
        G["GlobalCommandInput.vue<br/>Cmd+K Palette<br/>Slash Commands<br/>Templates"]
    end

    subgraph "Keyboard Handling"
        G1["useKeyboardShortcuts<br/>Global Shortcuts"]
    end

    subgraph "Central State - Pinia Store"
        H["orchestratorStore<br/>1004 lines<br/><br/>State:<br/>• agents[]<br/>• eventStreamEntries[]<br/>• chatMessages[]<br/>• isConnected<br/>• selectedAgent<br/><br/>Getters:<br/>• activeAgents<br/>• runningAgents<br/>• filteredEventStream<br/>• stats<br/><br/>Actions:<br/>• initialize()<br/>• loadAgents()<br/>• loadChatHistory()<br/>• fetchEventHistory()<br/>• connectWebSocket()<br/>• handle*Events()"]
    end

    subgraph "Services - HTTP Layer"
        I1["api.ts<br/>Axios Instance<br/>baseURL: 9403<br/>Error Interceptor"]
        I2["chatService.ts<br/>HTTP: getOrchestratorInfo<br/>loadChatHistory<br/>sendMessage<br/>WebSocket: connectWebSocket<br/>Routes events by type"]
        I3["agentService.ts<br/>HTTP: loadAgents"]
        I4["eventService.ts<br/>HTTP: getEvents<br/>Filtering & Pagination"]
        I5["fileService.ts<br/>File Tracking<br/>Diff Utilities"]
    end

    subgraph "Backend APIs - FastAPI"
        J1["HTTP REST Endpoints<br/>GET /list_agents<br/>POST /send_chat<br/>POST /load_chat<br/>GET /get_orchestrator<br/>GET /get_events<br/>GET /get_headers"]
        J2["WebSocket Endpoint<br/>ws://localhost:9403/ws<br/><br/>Events:<br/>• agent_log<br/>• orchestrator_chat<br/>• thinking_block<br/>• tool_use_block<br/>• agent_created/updated<br/>• agent_status_changed<br/>• orchestrator_updated"]
    end

    subgraph "Type System"
        K["types.d.ts<br/>358+ lines<br/><br/>Core:<br/>• Agent<br/>• OrchestratorAgent<br/>• AgentLog<br/>• SystemLog<br/>• OrchestratorChat<br/><br/>UI:<br/>• EventStreamEntry<br/>• ChatMessage<br/>• AppStats<br/><br/>API:<br/>• GetOrchestratorResponse<br/>• LoadChatResponse"]
    end

    subgraph "Configuration"
        L["config/constants.ts<br/>DEFAULT_EVENT_HISTORY_LIMIT=300<br/>DEFAULT_CHAT_HISTORY_LIMIT=300"]
        L1["Test Data<br/>testData.ts<br/>Mock agents, logs, messages"]
    end

    subgraph "Styling"
        M["global.css<br/>Dark theme<br/>Cyan/teal accents<br/>CSS variables"]
    end

    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> G1

    C --> C1
    D --> D1
    D --> D2
    D --> E3

    E --> E1
    E1 --> E2
    E --> E3
    E3 --> E4

    F --> F1
    F --> F2

    C --> H
    D --> H
    E --> H
    E2 --> H
    F --> H
    G --> H
    G1 --> H

    C1 --> H
    D1 --> H
    D2 --> H

    H --> I1
    H --> I2
    H --> I4

    D --> I3
    E --> I4
    F --> I2
    E3 --> I5

    I1 --> J1
    I2 --> J1
    I2 --> J2
    I3 --> J1
    I4 --> J1

    E3 --> K
    I2 --> K
    H --> K
    B --> K
    
    E --> L
    H --> L
    H --> L1
    B --> M
    E3 --> M

    style H fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style J2 fill:#4ecdc4,stroke:#1a9b8e,color:#fff
    style E2 fill:#95e1d3,stroke:#38ada9,color:#333
    style D1 fill:#95e1d3,stroke:#38ada9,color:#333
```

---

## Component Dependency Matrix

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| **App.vue** | orchestratorStore, useKeyboardShortcuts | Root layout & event routing |
| **AppHeader.vue** | useHeaderBar, orchestratorStore | Statistics display |
| **AgentList.vue** | orchestratorStore, useAgentPulse, useAgentColors | Agent visualization |
| **EventStream.vue** | orchestratorStore, useEventStreamFilter, Event Rows | Event log display |
| **OrchestratorChat.vue** | orchestratorStore, chat bubbles | Chat interface |
| **GlobalCommandInput.vue** | orchestratorStore, chatService | Command palette |
| **Event Row Components** | markdown.ts, DOMPurify | Event rendering |
| **orchestratorStore** | chatService, agentService, eventService | Central state |
| **chatService.ts** | api.ts, types | WebSocket & HTTP |
| **agentService.ts** | api.ts | Agent operations |
| **eventService.ts** | api.ts | Event queries |
| **useAgentPulse** | (standalone) | Animation management |
| **useEventStreamFilter** | (standalone) | Filter logic |
| **useHeaderBar** | orchestratorStore, types | Header state |

---

## State Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Component
    participant Store as orchestratorStore
    participant Service as Services
    participant Backend

    User->>Component: User Action (send chat)
    Component->>Store: sendUserMessage(content)
    Store->>Service: chatService.sendMessage()
    Service->>Backend: POST /send_chat
    Backend->>Backend: Process Message
    Backend->>Service: WebSocket: orchestrator_chat
    Service->>Store: onOrchestratorChat callback
    Store->>Store: addOrchestratorChatEvent()
    Store->>Component: Update chatMessages
    Component->>User: Render new message

    Backend->>Service: WebSocket: agent_log
    Service->>Store: onAgentLog callback
    Store->>Store: addAgentLogEvent()
    Store->>Store: triggerAgentPulse()
    Store->>Component: Update eventStreamEntries
    Component->>User: Render event + pulse animation
```

---

## WebSocket Event Processing Flow

```mermaid
graph LR
    WS["WebSocket Message<br/>From Backend"]
    
    WS -->|type: agent_log| H1["orchestratorStore<br/>addAgentLogEvent"]
    WS -->|type: orchestrator_chat| H2["orchestratorStore<br/>addOrchestratorChatEvent"]
    WS -->|type: thinking_block| H3["orchestratorStore<br/>addThinkingBlockEvent"]
    WS -->|type: tool_use_block| H4["orchestratorStore<br/>addToolUseBlockEvent"]
    WS -->|type: agent_created| H5["orchestratorStore<br/>handleAgentCreated"]
    WS -->|type: agent_updated| H6["orchestratorStore<br/>handleAgentUpdated"]
    WS -->|type: agent_status_changed| H7["orchestratorStore<br/>handleAgentStatusChange"]
    WS -->|type: orchestrator_updated| H8["orchestratorStore<br/>handleOrchestratorUpdated"]

    H1 -->|Update| ES["eventStreamEntries"]
    H2 -->|Update| ES
    H2 -->|Update| CM["chatMessages"]
    H3 -->|Update| CM
    H4 -->|Update| CM
    H5 -->|Update| AG["agents[]"]
    H6 -->|Update| AG
    H7 -->|Update| AG
    H8 -->|Update| OA["orchestratorAgent"]

    H1 -->|Pulse| AP["useAgentPulse<br/>triggerPulse"]
    H3 -->|Pulse| AP
    H4 -->|Pulse| AP

    ES --> EV["EventStream.vue<br/>Re-renders"]
    CM --> OC["OrchestratorChat.vue<br/>Re-renders"]
    AG --> AL["AgentList.vue<br/>Re-renders + Pulse"]
    OA --> AH["AppHeader.vue<br/>Re-renders Stats"]
    AP --> AL
```

