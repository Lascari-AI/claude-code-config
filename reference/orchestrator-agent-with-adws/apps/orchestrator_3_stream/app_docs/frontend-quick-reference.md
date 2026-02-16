# Frontend Quick Reference Guide

## Key Frontend Nodes - Quick Reference

**Must-Know Components:**
- **App.vue**: Root 3-column grid layout managing agents, events, and chat sidebars
- **orchestratorStore.ts**: Central Pinia store managing agents, events, chat, WebSocket connection
- **AgentList.vue**: Left sidebar rendering agent cards with O(1) pulsing animations on events
- **EventStream.vue**: Center column displaying filtered/searchable log entries with auto-scroll
- **OrchestratorChat.vue**: Right sidebar chat interface with typing indicator and multiple message types

**Must-Know Composables:**
- **useAgentPulse**: O(1) Set-based composable managing pulsing animations for high-frequency events
- **useEventStreamFilter**: Provides multi-dimensional filtering, regex search, and filter state management
- **useHeaderBar**: Aggregates stats, cost tracking, and CWD computations for header display

**Must-Know Services:**
- **chatService.ts**: Manages WebSocket connection and HTTP chat (messages, history, streaming)
- **api.ts**: Centralized Axios instance with error handling and base URL configuration

---

## Quick Navigation

**Main Files to Know:**
- `src/App.vue` - Root layout (3-column grid)
- `src/stores/orchestratorStore.ts` - Central state (1004 lines)
- `src/components/` - UI components
- `src/services/chatService.ts` - WebSocket & HTTP
- `src/types.d.ts` - All TypeScript definitions

---

## Common Tasks

### Adding a New Component

1. Create file: `src/components/YourComponent.vue`
2. Use store: `const store = useOrchestratorStore()`
3. Emit events for parent communication
4. Import in parent component

Example:
```vue
<script setup lang="ts">
import { useOrchestratorStore } from '../stores/orchestratorStore'

const store = useOrchestratorStore()
</script>
```

### Adding a New Composable

1. Create: `src/composables/useYourComposable.ts`
2. Return object with state (refs/computed) and actions
3. Import in components that need it

Example:
```typescript
import { ref, computed } from 'vue'

export function useYourComposable() {
  const state = ref('value')

  const computedValue = computed(() => state.value.toUpperCase())

  function action() {
    state.value = 'new value'
  }

  return { state, computedValue, action }
}
```

### Adding an API Endpoint

1. Create method in `src/services/yourService.ts`
2. Use `apiClient` from `api.ts`
3. Define TypeScript types in `types.d.ts`
4. Call from store action

Example:
```typescript
// In services/yourService.ts
export async function fetchData() {
  const response = await apiClient.get<YourType>('/endpoint')
  return response.data
}

// In orchestratorStore.ts
async function loadYourData() {
  const data = await yourService.fetchData()
  // Update state
}
```

### Filtering Events

The `useEventStreamFilter` composable provides multi-level filtering:

```typescript
// In a component
import { useEventStreamFilter } from '../composables/useEventStreamFilter'

const filter = useEventStreamFilter(() => store.eventStreamEntries)

// Toggle filters
filter.toggleAgentFilter('AgentName')
filter.toggleQuickFilter('ERROR')
filter.toggleCategoryFilter('TOOL')

// Get filtered results
const filtered = filter.filteredEvents
```

### Triggering Agent Pulse

Pulse animations are triggered automatically on relevant events, but you can trigger manually:

```typescript
import { useAgentPulse } from '../composables/useAgentPulse'

const pulse = useAgentPulse()
pulse.triggerPulse(agentId)  // Start animation for agent
pulse.isAgentPulsing(agentId)  // Check if pulsing (O(1))
```

### Real-Time Updates via WebSocket

Store automatically handles WebSocket events. To add a new event handler:

```typescript
// In orchestratorStore.ts connectWebSocket()
onYourEvent: (message) => {
  // Process message
  // Update store state
}
```

Backend sends: `{type: 'your_event', data: {...}}`

---

## Store (orchestratorStore) Cheat Sheet

### Access State
```typescript
const store = useOrchestratorStore()
store.agents              // All agents
store.eventStreamEntries  // All log entries
store.chatMessages        // Chat history
store.selectedAgentId     // Currently selected agent
store.isConnected         // WebSocket status
```

### Get Computed Values
```typescript
store.activeAgents      // Non-archived agents
store.runningAgents     // Currently executing
store.selectedAgent     // Full agent object
store.filteredEventStream  // Filtered by current filter
store.stats             // Header statistics
```

### Common Actions
```typescript
// Chat
await store.sendUserMessage('Hello')
await store.loadChatHistory()

// Events
store.addEventStreamEntry(entry)
store.setEventStreamFilter('errors')
await store.fetchEventHistory({ limit: 100 })

// WebSocket
store.connectWebSocket()
store.disconnectWebSocket()

// Agents
await store.loadAgents()
store.selectAgent(agentId)
```

---

## Component Props & Events

### EventStream.vue
**Props:**
- `events: EventStreamEntry[]`
- `currentFilter: string`
- `autoScroll: boolean`

**Events:**
- `@set-filter="handleFilter"`

### OrchestratorChat.vue
**Props:**
- `messages: ChatMessage[]`
- `isConnected: boolean`
- `isTyping: boolean`
- `autoScroll: boolean`

**Events:**
- `@send="handleMessage"`

### AgentList.vue
**Props:**
- `agents: Agent[]`
- `selectedAgentId: string | null`

**Events:**
- `@select-agent="handleSelect"`
- `@add-agent="handleAdd"`
- `@collapse-change="handleCollapse"`

---

## Type Quick Reference

### Core Objects

**Agent**
```typescript
{
  id: string
  name: string
  status: 'idle' | 'executing' | 'waiting' | 'blocked' | 'complete'
  total_cost: number
  input_tokens: number
  output_tokens: number
  metadata: Record<string, any>
}
```

**EventStreamEntry**
```typescript
{
  id: string
  lineNumber: number
  sourceType: 'agent_log' | 'system_log' | 'orchestrator_chat'
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS'
  content: string
  timestamp: Date | string
  agentName?: string
  metadata?: Record<string, any>
}
```

**ChatMessage (Union)**
```typescript
TextChatMessage {
  type: 'text'
  content: string
  sender: 'user' | 'orchestrator'
}

ThinkingChatMessage {
  type: 'thinking'
  thinking: string
  sender: 'orchestrator'
}

ToolUseChatMessage {
  type: 'tool_use'
  toolName: string
  toolInput: Record<string, any>
  sender: 'orchestrator'
}
```

---

## Styling

Use CSS variables defined in `global.css`:

```css
/* Colors */
var(--bg-primary)          /* Dark background */
var(--text-primary)        /* Main text */
var(--accent-primary)      /* Cyan accent */
var(--status-success)      /* Green status */
var(--status-error)        /* Red status */

/* Spacing */
var(--spacing-xs)          /* 4px */
var(--spacing-sm)          /* 8px */
var(--spacing-md)          /* 12px */
var(--spacing-lg)          /* 16px */
var(--spacing-xl)          /* 20px */

/* Fonts */
var(--font-mono)           /* Monospace */
```

Agent pulse animation:
```css
.agent-pulsing {
  animation: pulse-glow 0.335s ease-out;
}
```

---

## Environment Variables

Located in `.env` (not committed):

```bash
VITE_API_BASE_URL=http://127.0.0.1:9403
VITE_WEBSOCKET_URL=ws://127.0.0.1:9403/ws
```

Access in code:
```typescript
import.meta.env.VITE_API_BASE_URL
import.meta.env.VITE_WEBSOCKET_URL
```

---

## Common Patterns

### Reactive Array Updates (Vue 3)
```typescript
// ❌ Don't mutate directly
state.value.push(item)

// ✅ Do: Replace array
state.value = [...state.value, item]
```

### Reactive Map Updates
```typescript
// ❌ Don't mutate Map
map.set(key, value)

// ✅ Do: Replace Map to trigger reactivity
const newMap = new Map(map)
newMap.set(key, value)
map = newMap
```

### Computed vs Watch
```typescript
// Use computed for derived state
const activeCount = computed(() =>
  agents.value.filter(a => a.status === 'executing').length
)

// Use watch for side effects
watch(() => store.isConnected, (connected) => {
  if (connected) setupWebSocket()
})
```

---

## Debugging Tips

### Store State in Console
```javascript
// Get store instance
const store = useOrchestratorStore()
console.log(store.$state)

// Watch changes
store.$subscribe((mutation, state) => {
  console.log('State changed:', mutation)
})
```

### WebSocket Events
```typescript
// Added in chatService.ts for debugging
ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  console.log('WebSocket event:', message.type, message)
  // ... route by type
}
```

### Component State
```vue
<script setup>
const store = useOrchestratorStore()
console.log('Store state:', store.$state)
</script>

<template>
  <!-- Inspect in Vue DevTools -->
  {{ store.agents }}
</template>
```

---

## Performance Notes

- **useAgentPulse**: O(1) Set-based lookups
- **eventStreamEntries**: Supports 1000+ entries efficiently
- **filteredEventStream**: Computed property (memoized)
- **WebSocket debouncing**: 400ms debounce on pulse events
- **Batch updates**: Array spread prevents excessive re-renders

---

## Testing with Mock Data

Use data from `src/data/testData.ts` for UI development:

```typescript
import { mockAgents, mockLogs, mockMessages } from '../data/testData'

// In store or component
agents.value = mockAgents
eventStreamEntries.value = mockLogs
chatMessages.value = mockMessages
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Component doesn't update | Check if using array spread vs mutation |
| WebSocket not connecting | Verify VITE_WEBSOCKET_URL in .env |
| Pulse animations jumpy | Already optimized in useAgentPulse |
| Filter not working | Check eventName vs agentName field |
| Type errors | Update types.d.ts to match backend |
| Performance slow | Check EventStream virtualization |

---

## Key Keyboard Shortcuts

- **Cmd+K / Ctrl+K** - Open command palette
- **Cmd+L** (potential) - Clear event stream

Handled in `useKeyboardShortcuts.ts`

---

## Build Commands

```bash
# Development
npm run dev          # Start dev server (port 5175)

# Production
npm run build        # Build for production
npm run preview      # Preview production build

# Type checking
npx tsc --noEmit    # Check TypeScript errors
```

---

## File Size Reference

| File | Lines | Type |
|------|-------|------|
| orchestratorStore.ts | 1004 | Pinia store |
| AgentList.vue | 834 | Component |
| OrchestratorChat.vue | 662 | Component |
| GlobalCommandInput.vue | 710 | Component |
| useEventStreamFilter.ts | 362 | Composable |
| types.d.ts | 358+ | Types |

---

## Next Steps

1. Read `frontend-structure-summary.md` for deep dives
2. Explore component files to understand UI patterns
3. Study `orchestratorStore.ts` for state management
4. Check `chatService.ts` for API communication
5. Review `useAgentPulse.ts` for performance optimization
