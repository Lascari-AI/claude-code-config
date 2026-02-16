# Frontend Documentation

This directory contains comprehensive documentation of the orchestrator_3_stream frontend architecture.

## Documentation Files

### 1. frontend-structure-summary.md (917 lines)
**Comprehensive architectural overview and component inventory**

Contents:
- ✅ Technology stack overview
- ✅ Complete directory structure with annotations
- ✅ 3-layer component architecture diagram (Mermaid)
- ✅ Pinia store design and state management (1004 lines of code)
- ✅ Component details (App, AppHeader, AgentList, EventStream, Chat)
- ✅ Composables analysis:
  - useAgentPulse (O(1) optimization for high-frequency events)
  - useEventStreamFilter (multi-level filtering & search)
  - useHeaderBar (stats and cost tracking)
  - useKeyboardShortcuts (global shortcuts)
- ✅ Services documentation (API, Chat, Agent, Event, File)
- ✅ Complete TypeScript type definitions
- ✅ Data flow and real-time update patterns
- ✅ Performance optimizations (Set-based lookups, GPU animations, batched reactivity)
- ✅ Styling and theming (CSS variables, dark theme)
- ✅ Build and development setup
- ✅ Extended architecture diagrams (3 Mermaid diagrams showing):
  - Detailed component dependencies
  - WebSocket event flow
  - State change sequences

**Use this for:** Understanding the overall architecture, component relationships, and design decisions.

---

### 2. frontend-quick-reference.md (267 lines)
**Developer quick reference guide with practical examples**

Contents:
- ✅ Quick navigation to main files
- ✅ Common tasks with code examples:
  - Adding new components
  - Creating composables
  - Adding API endpoints
  - Event filtering
  - WebSocket integration
- ✅ Store cheat sheet (what to access, actions to call)
- ✅ Component props and events reference
- ✅ Type quick reference with code examples
- ✅ CSS variables and styling patterns
- ✅ Environment variables setup
- ✅ Vue 3 reactive patterns (do's and don'ts)
- ✅ Debugging tips and console tricks
- ✅ Performance notes
- ✅ Testing with mock data
- ✅ Common issues and solutions table
- ✅ Keyboard shortcuts
- ✅ Build commands

**Use this for:** Quick lookups, copy-paste examples, and development workflows.

---

## At a Glance

### Technology Stack
- **Framework:** Vue 3 (Composition API)
- **Language:** TypeScript
- **State Management:** Pinia
- **Build Tool:** Vite
- **HTTP Client:** Axios
- **Real-time:** WebSocket
- **Security:** DOMPurify (XSS protection)
- **Code Highlighting:** Highlight.js
- **Markdown:** Marked

### Architecture
- **3-Column Layout:** Left (agents) | Center (events) | Right (chat)
- **Central State:** Pinia orchestratorStore (1004 lines)
- **WebSocket:** Real-time event streaming from backend
- **Component Hierarchy:** 15+ Vue components with composable logic
- **Performance:** O(1) agent lookups, virtual scrolling, GPU-accelerated animations

### Key Components
| Component | Lines | Purpose |
|-----------|-------|---------|
| App.vue | 220 | Root layout manager |
| AppHeader.vue | 223 | Stats and controls |
| AgentList.vue | 834 | Agent cards with pulsing |
| EventStream.vue | 380 | Live log display |
| OrchestratorChat.vue | 662 | Chat interface |
| GlobalCommandInput.vue | 710 | Command palette (Cmd+K) |
| FilterControls.vue | 352 | Multi-level filtering |
| orchestratorStore.ts | 1004 | Central state management |

### Key Services
- **chatService.ts** - WebSocket connection + HTTP chat
- **agentService.ts** - Agent management
- **eventService.ts** - Event history queries
- **fileService.ts** - File tracking utilities
- **api.ts** - Axios configuration

### Key Composables
- **useAgentPulse** - O(1) animation state (Set-based)
- **useEventStreamFilter** - Multi-level filtering logic
- **useHeaderBar** - Stats aggregation
- **useKeyboardShortcuts** - Global keyboard handlers
- **useAgentColors** - Color assignment utilities

---

## File Organization

```
app_docs/
├── README.md (you are here)
├── frontend-structure-summary.md (917 lines)
└── frontend-quick-reference.md (267 lines)
```

---

## How to Use This Documentation

### For New Developers
1. Start with **frontend-quick-reference.md** - get oriented
2. Read **frontend-structure-summary.md** Overview section
3. Explore the component architecture diagram
4. Refer to the Directory Structure section

### For Adding Features
1. Check **frontend-quick-reference.md** Common Tasks section
2. Find similar component in **frontend-structure-summary.md** Component Details
3. Reference types in types.d.ts
4. Use store actions and WebSocket handlers as templates

### For Debugging
1. Check **frontend-quick-reference.md** Debugging Tips
2. Look up component in **frontend-structure-summary.md**
3. Reference the data flow diagrams
4. Check common issues table

### For Performance Work
1. Review **frontend-structure-summary.md** Performance Optimizations section
2. Study **useAgentPulse.ts** for Set-based patterns
3. Check batch reactivity patterns
4. Review GPU-accelerated animations

---

## Key Statistics

- **Total TypeScript/Vue Lines:** ~4,500+ lines of frontend code
- **Components:** 15+ Vue components
- **Composables:** 5+ reusable composables
- **Type Definitions:** 50+ TypeScript interfaces
- **Supported Events:** 10+ WebSocket event types
- **Performance:** Handles 1000+ log entries with <100ms filter time
- **Pulse Animations:** O(1) agent lookup optimization

---

## Important Architectural Patterns

### 1. Centralized State with Pinia
```typescript
// All components use the same orchestratorStore
const store = useOrchestratorStore()
```

### 2. Composable Logic Reuse
```typescript
// Logic extracted into composables, not components
const filter = useEventStreamFilter(() => store.eventStreamEntries)
const pulse = useAgentPulse()
```

### 3. WebSocket Event Routing
```typescript
// Backend events automatically routed to handlers
onOrchestratorChat, onAgentLog, onThinkingBlock, etc.
```

### 4. Reactive Array Updates
```typescript
// Vue 3 requires array replacement for reactivity
state.value = [...state.value, newItem]
```

### 5. TypeScript Throughout
```typescript
// Every component, service, and interface is typed
// No `any` types - full type safety
```

---

## Backend Integration Points

### HTTP Endpoints Used
- `GET /list_agents` - Load all agents
- `POST /send_chat` - Send chat message
- `POST /load_chat` - Load chat history
- `GET /get_orchestrator` - Get orchestrator info
- `GET /get_events` - Query event history
- `GET /get_headers` - Get CWD and system info

### WebSocket Events Handled
- `agent_log` - Agent activities
- `orchestrator_chat` - Chat messages
- `thinking_block` - Orchestrator thinking
- `tool_use_block` - Tool invocations
- `agent_created/updated/deleted` - Agent lifecycle
- `agent_status_changed` - Status updates
- `orchestrator_updated` - Cost/token updates

---

## Development Workflow

1. **Start dev server:** `npm run dev`
2. **Edit components** in `src/components/`
3. **Update store** in `src/stores/orchestratorStore.ts`
4. **Add services** in `src/services/`
5. **Create composables** in `src/composables/`
6. **Update types** in `src/types.d.ts`
7. **Test with Playwright** for integration testing

---

## Related Documentation

See also:
- `/orchestrator_3_stream/CLAUDE.md` - Project instructions
- `/orchestrator_3_stream/backend/` - Backend API documentation
- `/orchestrator_db/` - Database models and migrations

---

## Questions?

Refer to the detailed documentation files for comprehensive information on any topic. The architecture is designed to be maintainable and extensible.
