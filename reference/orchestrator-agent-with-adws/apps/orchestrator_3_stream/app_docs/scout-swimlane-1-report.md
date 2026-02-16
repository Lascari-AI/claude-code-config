# Swimlane UI Component Placement - Scout Report

**Report Date:** December 22, 2024
**Scout Agent:** scout-report-suggest
**Priority Level:** Medium

---

## Executive Summary

This report analyzes the Orchestrator 3 Stream codebase to recommend optimal placement for a new swimlane UI component. After thorough examination of the existing architecture, I recommend **Option 2: Tab-based view within the center column** as the primary approach, with **Option 1: 4-column layout** as an alternative for complex use cases.

The existing architecture follows a well-structured Vue 3 pattern with a clear 3-column CSS Grid layout defined in `App.vue`. The component organization is modular with dedicated directories for components, composables, stores, and services.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Code Location Recommendations](#2-code-location-recommendations)
3. [UI Location Options](#3-ui-location-options)
4. [Recommended Approach](#4-recommended-approach)
5. [Component Structure](#5-component-structure)
6. [Type Definitions](#6-type-definitions)
7. [Implementation Checklist](#7-implementation-checklist)
8. [Rationale](#8-rationale)

---

## 1. Current Architecture Analysis

### Layout Structure

The application uses a CSS Grid-based 3-column layout defined in `App.vue`:

```vue
<!-- App.vue Lines 5-37 -->
<main class="app-main">
  <AgentList class="app-sidebar left" />      <!-- 280px -->
  <EventStream class="app-content center" />   <!-- 1fr (flexible) -->
  <OrchestratorChat class="app-sidebar right" /> <!-- 418px -->
</main>
```

```css
/* App.vue Lines 117-123 */
.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 418px;
  overflow: hidden;
  transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Component Organization

```
apps/orchestrator_3_stream/frontend/src/
├── App.vue                          # Main layout container
├── main.ts                          # Vue app entry point
├── types.d.ts                       # TypeScript interfaces
├── components/
│   ├── AgentList.vue                # LEFT column - Agent cards
│   ├── EventStream.vue              # CENTER column - Event log
│   ├── OrchestratorChat.vue         # RIGHT column - Chat interface
│   ├── AppHeader.vue                # Top header with stats
│   ├── FilterControls.vue           # Filter UI component
│   ├── GlobalCommandInput.vue       # Modal overlay (Cmd+K)
│   ├── chat/                        # Chat sub-components
│   │   ├── ThinkingBubble.vue
│   │   └── ToolUseBubble.vue
│   └── event-rows/                  # Event row renderers
│       ├── AgentLogRow.vue
│       ├── AgentToolUseBlockRow.vue
│       ├── FileChangesDisplay.vue
│       ├── OrchestratorChatRow.vue
│       ├── SystemLogRow.vue
│       └── ToolUseBlockRow.vue
├── composables/
│   ├── useAgentColors.ts
│   ├── useAgentPulse.ts
│   ├── useAutocomplete.ts
│   ├── useEventStreamFilter.ts
│   ├── useHeaderBar.ts
│   └── useKeyboardShortcuts.ts
├── stores/
│   └── orchestratorStore.ts         # Pinia state management
├── services/
│   ├── api.ts
│   ├── agentService.ts
│   ├── autocompleteService.ts
│   ├── chatService.ts
│   └── eventService.ts
├── styles/
│   └── global.css                   # CSS variables and base styles
├── config/
│   └── constants.ts
├── data/
│   └── testData.ts
└── utils/
    ├── agentColors.ts
    └── markdown.ts
```

### Data Flow Pattern

- **Store** (`orchestratorStore.ts`) manages all application state
- **WebSocket** receives real-time events: `agent_log`, `orchestrator_chat`, `thinking_block`, `tool_use_block`
- **Components** subscribe to store getters via Pinia
- **Agent data** includes: `id`, `name`, `status`, `model`, `input_tokens`, `output_tokens`, `total_cost`, `metadata`

---

## 2. Code Location Recommendations

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `src/components/Swimlane.vue` | Main swimlane container component |
| `src/components/swimlane/SwimlaneRow.vue` | Individual horizontal lane per agent |
| `src/components/swimlane/SwimlaneCard.vue` | Task/event cards within lanes |
| `src/components/swimlane/SwimlaneHeader.vue` | Column headers (time/phase markers) |
| `src/composables/useSwimlane.ts` | Swimlane data transformation and logic |

### Files to Modify

| File Path | Changes Required |
|-----------|------------------|
| `src/App.vue` | Add Swimlane import, update layout or add view toggle |
| `src/types.d.ts` | Add `SwimlaneItem`, `SwimlaneRow`, `SwimlaneConfig` interfaces |
| `src/stores/orchestratorStore.ts` | Add swimlane view state and computed getters |
| `src/styles/global.css` | Add swimlane-specific CSS variables (optional) |

### Recommended Directory Structure

```
src/components/
├── Swimlane.vue                    # Main container
├── swimlane/                       # NEW DIRECTORY
│   ├── SwimlaneHeader.vue          # Time/phase column headers
│   ├── SwimlaneRow.vue             # Horizontal lane per agent
│   └── SwimlaneCard.vue            # Individual task/event cards
├── AgentList.vue                   # Existing - left column
├── EventStream.vue                 # Existing - center column
├── OrchestratorChat.vue            # Existing - right column
└── ...
```

---

## 3. UI Location Options

### Option 1: 4-Column Layout (New Dedicated Column)

**Placement:** Add swimlane as a dedicated 4th column between EventStream and OrchestratorChat.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APP HEADER                                      │
├──────────┬──────────────────┬──────────────────────┬────────────────────────┤
│  AGENTS  │   EVENT STREAM   │      SWIMLANE        │    O-AGENT CHAT        │
│  (280px) │     (1fr)        │      (400px)         │      (418px)           │
├──────────┼──────────────────┼──────────────────────┼────────────────────────┤
│          │                  │  Agent1 ████░░░░░░░  │                        │
│  Agent1  │  [Log entries]   │  Agent2 ░░████░░░░░  │   User: message        │
│  Agent2  │                  │  Agent3 ░░░░░░████░  │   Orch: response       │
│  Agent3  │                  │                      │                        │
└──────────┴──────────────────┴──────────────────────┴────────────────────────┘
```

**App.vue Changes:**
```vue
<template>
  <div class="app-container">
    <AppHeader />
    <main class="app-main">
      <AgentList class="app-sidebar left" />
      <EventStream class="app-content center" />
      <Swimlane class="app-swimlane" />           <!-- NEW -->
      <OrchestratorChat class="app-sidebar right" />
    </main>
  </div>
</template>
```

**CSS Changes:**
```css
.app-main {
  grid-template-columns: 280px 1fr 400px 418px;  /* 4 columns */
}

/* Responsive adjustments */
@media (max-width: 1600px) {
  .app-main {
    grid-template-columns: 260px 1fr 350px 385px;
  }
}

@media (max-width: 1400px) {
  .app-main {
    grid-template-columns: 240px 1fr 300px 350px;
  }
}

/* Hide swimlane on smaller screens */
@media (max-width: 1200px) {
  .app-swimlane {
    display: none;
  }
  .app-main {
    grid-template-columns: 240px 1fr 352px;
  }
}
```

---

### Option 2: Tab-Based View (Center Column) - RECOMMENDED

**Placement:** Add a tab switcher at the top of the center column, allowing users to toggle between "Event Stream" and "Swimlane" views.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APP HEADER                                    │
├──────────┬─────────────────────────────────────┬────────────────────┤
│          │  [Events] [Swimlane] ← Tab Switcher │                    │
│  AGENTS  │─────────────────────────────────────│   O-AGENT CHAT     │
│  (Left)  │                                     │     (Right)        │
│          │   SWIMLANE VIEW                     │                    │
│  Agent1  │   ┌─────────────────────────────┐   │   User: ...        │
│  Agent2  │   │ Agent1 ████░░░░░░░░░░░░░░░░ │   │   Orch: ...        │
│  Agent3  │   │ Agent2 ░░░░████████░░░░░░░░ │   │                    │
│          │   │ Agent3 ░░░░░░░░░░░░████████ │   │                    │
│          │   └─────────────────────────────┘   │                    │
└──────────┴─────────────────────────────────────┴────────────────────┘
```

**App.vue Changes:**
```vue
<template>
  <div class="app-container">
    <AppHeader />
    <main class="app-main">
      <AgentList class="app-sidebar left" />

      <!-- Center panel with view toggle -->
      <div class="app-content center">
        <div class="center-view-tabs">
          <button
            :class="{ active: store.centerPanelView === 'events' }"
            @click="store.setCenterPanelView('events')"
          >
            Events
          </button>
          <button
            :class="{ active: store.centerPanelView === 'swimlane' }"
            @click="store.setCenterPanelView('swimlane')"
          >
            Swimlane
          </button>
        </div>

        <EventStream v-if="store.centerPanelView === 'events'" />
        <Swimlane v-else-if="store.centerPanelView === 'swimlane'" />
      </div>

      <OrchestratorChat class="app-sidebar right" />
    </main>
  </div>
</template>
```

**Store Changes (`orchestratorStore.ts`):**
```typescript
// Add to state
const centerPanelView = ref<'events' | 'swimlane'>('events')

// Add action
function setCenterPanelView(view: 'events' | 'swimlane') {
  centerPanelView.value = view
}

// Export in return statement
return {
  // ... existing exports
  centerPanelView,
  setCenterPanelView,
}
```

---

### Option 3: Horizontal Section (Below Header)

**Placement:** Add a collapsible horizontal swimlane section between AppHeader and the 3-column main area.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APP HEADER                                    │
├─────────────────────────────────────────────────────────────────────┤
│  SWIMLANE (collapsible, 150-200px height)                           │
│  Agent1 ████░░░░░░░  Agent2 ░░████░░░░  Agent3 ░░░░████░░           │
├──────────┬─────────────────────────────────────┬────────────────────┤
│  AGENTS  │         EVENT STREAM                │   O-AGENT CHAT     │
└──────────┴─────────────────────────────────────┴────────────────────┘
```

**Not Recommended** - Reduces vertical space and creates horizontal scrolling friction.

---

## 4. Recommended Approach

**Primary Recommendation: Option 2 (Tab-Based View)**

This approach:
- Preserves existing 3-column layout
- Doesn't reduce space for any existing component
- Provides cleaner user experience with focused views
- Easier responsive design handling
- Lower implementation complexity
- Follows existing patterns (FilterControls already uses tabs)

**When to Choose Option 1 (4-Column):**
- Users need swimlane AND event stream visible simultaneously
- Swimlane serves as a navigation/selection tool for events
- Orchestrator manages 10+ agents requiring constant visibility
- Large monitor deployments (1920px+ width)

---

## 5. Component Structure

### Swimlane.vue (Main Container)

```vue
<template>
  <div class="swimlane-container">
    <SwimlaneHeader :phases="phases" />
    <div class="swimlane-body">
      <SwimlaneRow
        v-for="row in swimlaneData"
        :key="row.id"
        :row="row"
        @card-click="handleCardClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SwimlaneHeader from './swimlane/SwimlaneHeader.vue'
import SwimlaneRow from './swimlane/SwimlaneRow.vue'
import { useSwimlane } from '../composables/useSwimlane'

const { swimlaneData, phases } = useSwimlane()

const handleCardClick = (cardId: string) => {
  // Handle card selection/detail view
}
</script>
```

### SwimlaneRow.vue

```vue
<template>
  <div class="swimlane-row" :style="{ borderColor: rowColor }">
    <div class="row-label">
      <span class="row-name">{{ row.label }}</span>
      <span class="row-status" :class="row.status">{{ row.status }}</span>
    </div>
    <div class="row-track">
      <SwimlaneCard
        v-for="item in row.items"
        :key="item.id"
        :item="item"
        :style="getCardPosition(item)"
        @click="$emit('card-click', item.id)"
      />
    </div>
  </div>
</template>
```

### SwimlaneCard.vue

```vue
<template>
  <div
    class="swimlane-card"
    :class="[item.status, { selected: isSelected }]"
    :title="item.label"
  >
    <span class="card-label">{{ truncatedLabel }}</span>
    <span class="card-duration" v-if="item.duration">{{ item.duration }}</span>
  </div>
</template>
```

### useSwimlane.ts (Composable)

```typescript
import { computed } from 'vue'
import { useOrchestratorStore } from '../stores/orchestratorStore'
import type { SwimlaneRow, SwimlaneItem } from '../types'

export function useSwimlane() {
  const store = useOrchestratorStore()

  // Transform agents and events into swimlane format
  const swimlaneData = computed<SwimlaneRow[]>(() => {
    return store.agents.map(agent => ({
      id: agent.id,
      label: agent.name,
      status: agent.status || 'idle',
      color: getAgentColor(agent),
      items: getAgentSwimlaneItems(agent.id)
    }))
  })

  // Extract phases/time markers for header
  const phases = computed(() => {
    // Calculate time-based or phase-based columns
    return ['Start', 'Processing', 'Complete']
  })

  function getAgentSwimlaneItems(agentId: string): SwimlaneItem[] {
    return store.eventStreamEntries
      .filter(e => e.agentId === agentId)
      .map(e => ({
        id: e.id,
        agentId: e.agentId,
        label: e.content || e.eventType || 'Event',
        status: mapEventToStatus(e),
        startTime: e.timestamp.toString(),
        metadata: e.metadata
      }))
  }

  function mapEventToStatus(event: any): SwimlaneItem['status'] {
    // Map event types to swimlane status
    if (event.eventType?.includes('Error')) return 'blocked'
    if (event.eventType?.includes('Complete')) return 'complete'
    if (event.eventCategory === 'hook') return 'in_progress'
    return 'pending'
  }

  return {
    swimlaneData,
    phases
  }
}
```

---

## 6. Type Definitions

Add to `src/types.d.ts`:

```typescript
// ═══════════════════════════════════════════════════════════
// SWIMLANE TYPES
// ═══════════════════════════════════════════════════════════

export type SwimlaneItemStatus = 'pending' | 'in_progress' | 'complete' | 'blocked'

export interface SwimlaneItem {
  id: string
  agentId: string
  label: string
  status: SwimlaneItemStatus
  startTime: string
  endTime?: string
  duration?: string
  metadata?: Record<string, any>
}

export interface SwimlaneRow {
  id: string
  label: string              // Agent name or phase name
  status: AgentStatus | null
  color?: string             // Agent border color
  items: SwimlaneItem[]
}

export interface SwimlaneConfig {
  showTimeAxis: boolean
  groupBy: 'agent' | 'phase' | 'status'
  timeRange?: {
    start: Date
    end: Date
  }
}

export type CenterPanelView = 'events' | 'swimlane'
```

---

## 7. Implementation Checklist

### Phase 1: Foundation
- [ ] Add type definitions to `types.d.ts`
- [ ] Create `useSwimlane.ts` composable
- [ ] Add `centerPanelView` state to store (for Option 2)

### Phase 2: Components
- [ ] Create `src/components/swimlane/` directory
- [ ] Build `SwimlaneCard.vue` component
- [ ] Build `SwimlaneRow.vue` component
- [ ] Build `SwimlaneHeader.vue` component
- [ ] Build main `Swimlane.vue` container

### Phase 3: Integration
- [ ] Modify `App.vue` to include swimlane (Option 1 or 2)
- [ ] Add view toggle UI (Option 2)
- [ ] Update responsive breakpoints
- [ ] Add CSS variables for swimlane theming

### Phase 4: Polish
- [ ] Add animations for card transitions
- [ ] Implement card click interactions
- [ ] Add keyboard navigation
- [ ] Test with 10+ agents

### Phase 5: Validation
- [ ] Run Playwright tests for UI interactions
- [ ] Test responsive behavior at all breakpoints
- [ ] Validate WebSocket event updates render correctly

---

## 8. Rationale

### Why Option 2 (Tab-Based) is Recommended

| Factor | Analysis |
|--------|----------|
| **Screen Real Estate** | Preserves existing 3-column layout; doesn't reduce space for any existing component |
| **User Experience** | Users can focus on one view at a time; cleaner interface without visual overload |
| **Responsive Design** | Easier to handle on smaller screens; tab simply toggles content without layout changes |
| **Implementation Effort** | Lower complexity; minimal changes to `App.vue` grid layout |
| **Consistency** | Follows existing patterns - `FilterControls.vue` already uses tabs for mode switching |
| **Performance** | Only one view renders at a time; better memory usage |

### When Option 1 (4-Column) is Better

- Users need to see swimlane **and** event stream simultaneously
- The swimlane serves as a **navigation/selection** tool that highlights events
- The orchestrator manages **10+ agents** requiring constant workflow visibility
- Target deployment is **large monitors** (1920px+ width)

### Why Option 3 (Horizontal) is Not Recommended

- Vertical space is more valuable in monitoring/dashboard UIs
- Horizontal scrolling creates usability friction
- Conflicts with the established vertical-column paradigm
- More complex responsive handling

---

## Summary

| Metric | Value |
|--------|-------|
| **Recommended Approach** | Option 2: Tab-Based View |
| **New Files** | 5 (Swimlane.vue, 3 sub-components, 1 composable) |
| **Modified Files** | 3-4 (App.vue, types.d.ts, orchestratorStore.ts, optionally global.css) |
| **Estimated Effort** | Medium |
| **Priority** | Medium |

---

*Report generated by scout-report-suggest agent*
