# Swimlane UI Component Placement Report

**Generated:** 2024-12-22
**Scout Agent:** scout-report-suggest
**Status:** Complete Analysis & Recommendations

---

## Executive Summary

This report provides comprehensive recommendations for integrating a swimlane UI component into the Orchestrator 3 Stream application. After thorough analysis of the existing Vue 3 + TypeScript codebase, I recommend implementing the swimlane as a **toggle view in the center column**, replacing the EventStream when activated. This approach minimizes architectural disruption while providing maximum horizontal space for timeline visualization.

---

## 1. Code Location Recommendations

### 1.1 New Files to Create

#### Primary Component
```
frontend/src/components/AgentSwimlane.vue
```
- **Purpose:** Main swimlane container component
- **Pattern:** Follow EventStream.vue structure with similar props/emits interface
- **Responsibilities:**
  - Render timeline header
  - Iterate over agents and render SwimlaneRow for each
  - Handle zoom/pan interactions
  - Manage time range selection

#### Swimlane Sub-Components
```
frontend/src/components/swimlane/
├── SwimlaneRow.vue           # Individual agent lane (horizontal track)
├── SwimlaneEventCard.vue     # Event cards within each lane
└── SwimlaneTimeline.vue      # Time axis header/ruler
```

| Component | Purpose |
|-----------|---------|
| `SwimlaneRow.vue` | Horizontal lane for a single agent, positions events along timeline |
| `SwimlaneEventCard.vue` | Visual representation of an event (tool use, thinking, response) |
| `SwimlaneTimeline.vue` | Time axis with hour/minute markers, zoom controls |

#### Composable for State Management
```
frontend/src/composables/useSwimlane.ts
```
- **Purpose:** Swimlane-specific state management and filtering logic
- **Pattern:** Follow `useEventStreamFilter.ts` structure
- **Exports:**
  - `timeRange` - Current visible time window
  - `zoomLevel` - Timeline granularity (hour/minute/second)
  - `groupedEventsByAgent` - Events organized by agent ID
  - `calculateEventPosition()` - Position events on timeline

### 1.2 Existing Files to Modify

#### App.vue
**Path:** `frontend/src/App.vue`

**Changes Required:**
```vue
<!-- Add import -->
import AgentSwimlane from './components/AgentSwimlane.vue'

<!-- Modify template - conditional rendering -->
<EventStream
  v-if="store.viewMode === 'stream'"
  ref="eventStreamRef"
  class="app-content center"
  ...
/>
<AgentSwimlane
  v-else-if="store.viewMode === 'swimlane'"
  class="app-content center"
  :agents="store.agents"
  :events="store.filteredEventStream"
/>
```

**Rationale:** Minimal template change with conditional rendering based on store state.

#### orchestratorStore.ts
**Path:** `frontend/src/stores/orchestratorStore.ts`

**Changes Required:**
```typescript
// Add to STATE section (around line 65)
const viewMode = ref<'stream' | 'swimlane'>('stream')

// Add to ACTIONS section
function setViewMode(mode: 'stream' | 'swimlane') {
  viewMode.value = mode
}

function toggleViewMode() {
  viewMode.value = viewMode.value === 'stream' ? 'swimlane' : 'stream'
}

// Add to GETTERS section
const eventsByAgent = computed(() => {
  const grouped = new Map<string, EventStreamEntry[]>()
  eventStreamEntries.value.forEach(event => {
    if (event.agentId) {
      const existing = grouped.get(event.agentId) || []
      existing.push(event)
      grouped.set(event.agentId, existing)
    }
  })
  return grouped
})

// Add to return statement
return {
  // ... existing exports
  viewMode,
  setViewMode,
  toggleViewMode,
  eventsByAgent,
}
```

#### types.d.ts
**Path:** `frontend/src/types.d.ts`

**Add after line 240 (after EventStreamEntry):**
```typescript
// ═══════════════════════════════════════════════════════════
// SWIMLANE TYPES
// ═══════════════════════════════════════════════════════════

export type ViewMode = 'stream' | 'swimlane'

export type ZoomLevel = 'hour' | 'minute' | 'second'

export interface SwimlaneConfig {
  timeRange: [Date, Date]
  zoomLevel: ZoomLevel
  showInactiveAgents: boolean
  laneHeight: number
}

export interface SwimlaneEvent extends EventStreamEntry {
  laneId: string           // Agent ID for lane assignment
  duration?: number        // Event duration in ms (for tool executions)
  position: {
    left: number           // Percentage from start
    width: number          // Percentage width (for duration-based events)
  }
}

export interface SwimlaneLane {
  agentId: string
  agentName: string
  agentColor: string
  events: SwimlaneEvent[]
  isActive: boolean
}
```

#### FilterControls.vue
**Path:** `frontend/src/components/FilterControls.vue`

**Add view mode toggle to template:**
```vue
<!-- Add in filter controls header area -->
<div class="view-mode-toggle">
  <button
    class="view-mode-btn"
    :class="{ active: store.viewMode === 'stream' }"
    @click="store.setViewMode('stream')"
  >
    <span class="view-icon">≡</span>
    Stream
  </button>
  <button
    class="view-mode-btn"
    :class="{ active: store.viewMode === 'swimlane' }"
    @click="store.setViewMode('swimlane')"
  >
    <span class="view-icon">═</span>
    Swimlane
  </button>
</div>
```

---

## 2. UI Location in the Interface

### 2.1 Recommended Placement: Toggle View in Center Column

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AppHeader                                       │
│  MULTI-AGENT ORCHESTRATION    [Active: 3] [Running: 1] [Logs: 42] [Cost: $] │
├────────────┬───────────────────────────────────────────────────┬────────────┤
│            │  [≡ Stream] [═ Swimlane] ← View Toggle            │            │
│            │  [Combined] [Errors] [Performance] [Search...]    │            │
│            ├───────────────────────────────────────────────────┤            │
│   AGENTS   │                                                   │  O-Agent   │
│            │   When Stream View:                               │            │
│  ┌───────┐ │   ┌─────────────────────────────────────────────┐ │  Cost: $X  │
│  │Agent-1│ │   │ 001 INFO  agent-1  Tool: Read file.ts      │ │  Context:  │
│  │ EXEC  │ │   │ 002 INFO  agent-2  Thinking: analyzing...  │ │   42k/200k │
│  └───────┘ │   │ 003 INFO  agent-1  Response: Found 3 issues│ │            │
│            │   └─────────────────────────────────────────────┘ │  ┌───────┐ │
│  ┌───────┐ │                                                   │  │ Chat  │ │
│  │Agent-2│ │   When Swimlane View:                             │  │ msgs  │ │
│  │ IDLE  │ │   ┌─────────────────────────────────────────────┐ │  │       │ │
│  └───────┘ │   │ Timeline: 10:00 ──────────── 10:15 ──────── │ │  └───────┘ │
│            │   ├─────────────────────────────────────────────┤ │            │
│  ┌───────┐ │   │ Agent-1 ═══●════●═══●══════════════════════ │ │            │
│  │Agent-3│ │   │ Agent-2 ════════●═════●════●═══════════════ │ │            │
│  │ WAIT  │ │   │ Agent-3 ═●════════════●════════●═══════════ │ │            │
│  └───────┘ │   └─────────────────────────────────────────────┘ │            │
└────────────┴───────────────────────────────────────────────────┴────────────┘
```

### 2.2 Grid Layout (Unchanged)

The existing CSS Grid layout remains intact:

```css
/* App.vue - No changes required to grid structure */
.app-main {
  display: grid;
  grid-template-columns: 280px 1fr 418px;  /* Left | Center | Right */
  overflow: hidden;
}

/* Responsive variants also unchanged */
.app-main.sidebar-collapsed {
  grid-template-columns: 48px 1fr 418px;
}
```

### 2.3 Swimlane Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Timeline Header                                                      │
│ ◀ │ 10:00    10:05    10:10    10:15    10:20    10:25    10:30 │ ▶ │
│   │    │        │        │        │        │        │        │     │
├───┴────┴────────┴────────┴────────┴────────┴────────┴────────┴─────┤
│ Agent-1 (scout-agent)     ┌──────────────────────────────────────┐ │
│ [EXECUTING]               │ ●Read  ●Grep  ●●●Analyze  ●Write     │ │
│                           └──────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│ Agent-2 (build-agent)     ┌──────────────────────────────────────┐ │
│ [IDLE]                    │      ●Edit  ●Edit  ●Edit             │ │
│                           └──────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│ Agent-3 (review-agent)    ┌──────────────────────────────────────┐ │
│ [WAITING]                 │ ●Read                    ●●Response  │ │
│                           └──────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘

Legend:
● = Event marker (hover for details)
─ = Timeline track
[STATUS] = Agent current status
```

---

## 3. Component Structure

### 3.1 AgentSwimlane.vue (Main Component)

```vue
<template>
  <div class="agent-swimlane">
    <!-- Timeline Controls -->
    <div class="swimlane-controls">
      <SwimlaneTimeline
        :time-range="timeRange"
        :zoom-level="zoomLevel"
        @zoom-change="handleZoomChange"
        @pan="handlePan"
      />
    </div>

    <!-- Swimlane Lanes -->
    <div class="swimlane-content" ref="contentRef">
      <div v-if="lanes.length === 0" class="empty-state">
        <p>No agent activity to display</p>
      </div>

      <SwimlaneRow
        v-for="lane in lanes"
        :key="lane.agentId"
        :lane="lane"
        :time-range="timeRange"
        :zoom-level="zoomLevel"
        @event-click="handleEventClick"
        @event-hover="handleEventHover"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useOrchestratorStore } from '../stores/orchestratorStore'
import { useSwimlane } from '../composables/useSwimlane'
import SwimlaneTimeline from './swimlane/SwimlaneTimeline.vue'
import SwimlaneRow from './swimlane/SwimlaneRow.vue'
import type { SwimlaneLane, ZoomLevel } from '../types'

const store = useOrchestratorStore()
const { timeRange, zoomLevel, lanes, setZoomLevel, panTimeline } = useSwimlane()

// Event handlers
const handleZoomChange = (level: ZoomLevel) => setZoomLevel(level)
const handlePan = (delta: number) => panTimeline(delta)
const handleEventClick = (event: any) => { /* Show event details */ }
const handleEventHover = (event: any) => { /* Show tooltip */ }
</script>
```

### 3.2 SwimlaneRow.vue (Lane Component)

```vue
<template>
  <div
    class="swimlane-row"
    :style="{ '--lane-color': lane.agentColor }"
  >
    <!-- Agent Info -->
    <div class="lane-header">
      <span class="agent-name">{{ lane.agentName }}</span>
      <span class="agent-status" :class="statusClass">
        {{ lane.isActive ? 'ACTIVE' : 'IDLE' }}
      </span>
    </div>

    <!-- Event Track -->
    <div class="lane-track">
      <SwimlaneEventCard
        v-for="event in lane.events"
        :key="event.id"
        :event="event"
        :style="eventStyle(event)"
        @click="$emit('event-click', event)"
        @mouseenter="$emit('event-hover', event)"
      />
    </div>
  </div>
</template>
```

### 3.3 useSwimlane.ts (Composable)

```typescript
import { ref, computed } from 'vue'
import { useOrchestratorStore } from '../stores/orchestratorStore'
import { getAgentBorderColor } from '../utils/agentColors'
import type { SwimlaneLane, SwimlaneEvent, ZoomLevel } from '../types'

export function useSwimlane() {
  const store = useOrchestratorStore()

  // State
  const zoomLevel = ref<ZoomLevel>('minute')
  const timeRange = ref<[Date, Date]>([
    new Date(Date.now() - 30 * 60 * 1000), // 30 mins ago
    new Date()
  ])

  // Computed: Group events by agent into lanes
  const lanes = computed<SwimlaneLane[]>(() => {
    return store.agents.map(agent => ({
      agentId: agent.id,
      agentName: agent.name,
      agentColor: getAgentBorderColor(agent.name, agent.id),
      isActive: agent.status === 'executing',
      events: store.eventStreamEntries
        .filter(e => e.agentId === agent.id)
        .filter(e => isWithinTimeRange(e.timestamp))
        .map(e => ({
          ...e,
          laneId: agent.id,
          position: calculatePosition(e.timestamp)
        }))
    }))
  })

  // Calculate event position as percentage
  function calculatePosition(timestamp: Date | string): { left: number; width: number } {
    const time = new Date(timestamp).getTime()
    const [start, end] = timeRange.value.map(d => d.getTime())
    const range = end - start
    const left = ((time - start) / range) * 100
    return { left: Math.max(0, Math.min(100, left)), width: 1 }
  }

  // Actions
  function setZoomLevel(level: ZoomLevel) {
    zoomLevel.value = level
  }

  function panTimeline(deltaMs: number) {
    timeRange.value = [
      new Date(timeRange.value[0].getTime() + deltaMs),
      new Date(timeRange.value[1].getTime() + deltaMs)
    ]
  }

  return {
    zoomLevel,
    timeRange,
    lanes,
    setZoomLevel,
    panTimeline
  }
}
```

---

## 4. Rationale

### 4.1 Why Toggle View in Center Column?

| Factor | Benefit |
|--------|---------|
| **Minimal Architecture Disruption** | Existing 3-column CSS Grid layout unchanged; only swaps component in center |
| **Full Width for Visualization** | Center column uses `1fr` (flexible) - maximizes horizontal space for timeline |
| **Leverages Existing Patterns** | FilterControls already has tab-style UI; view toggle follows established pattern |
| **Data Compatibility** | Both views consume same `eventStreamEntries` from store |
| **User Experience** | Users can switch views without losing AgentList or Chat context |

### 4.2 Why NOT Other Approaches?

| Alternative | Reason Against |
|-------------|----------------|
| **Fourth Column** | Grid becomes cramped; 4 columns don't fit well on screens < 1400px |
| **Horizontal Split (Top/Bottom)** | Compresses both views vertically; swimlane needs height for multiple agent lanes |
| **Full-Screen Overlay** | Loses context of AgentList and Chat; modal UX is disruptive |
| **Replace AgentList** | AgentList provides critical agent selection functionality |
| **Collapsible Panel** | Added complexity; split resizing difficult to implement well |

### 4.3 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     orchestratorStore                            │
│  ┌──────────────────────┐    ┌──────────────────────┐           │
│  │ eventStreamEntries   │    │ agents               │           │
│  │ (all events)         │    │ (agent metadata)     │           │
│  └──────────┬───────────┘    └──────────┬───────────┘           │
│             │                           │                        │
│             └───────────┬───────────────┘                        │
│                         │                                        │
│                         ▼                                        │
│             ┌───────────────────────┐                            │
│             │ eventsByAgent         │ ← NEW computed getter      │
│             │ (Map<agentId, events>)│                            │
│             └───────────┬───────────┘                            │
└─────────────────────────┼────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
  ┌───────────────┐               ┌───────────────┐
  │ EventStream   │               │ AgentSwimlane │
  │ (list view)   │               │ (lanes view)  │
  └───────────────┘               └───────┬───────┘
                                          │
                                          ▼
                                  ┌───────────────┐
                                  │ useSwimlane   │
                                  │ (composable)  │
                                  │ - timeRange   │
                                  │ - zoomLevel   │
                                  │ - lanes       │
                                  └───────────────┘
```

---

## 5. Styling Guidelines

### 5.1 CSS Variables to Use (from global.css)

```css
/* Already available - use these for consistency */
--bg-primary: #0a0a0a;      /* Swimlane background */
--bg-secondary: #1a1a1a;    /* Lane background */
--bg-tertiary: #2a2a2a;     /* Event card background */
--accent-primary: #06b6d4;  /* Timeline highlights */
--border-color: #333333;    /* Lane separators */
--text-primary: #ffffff;    /* Agent names */
--text-muted: #6b7280;      /* Timestamps */
--font-mono: 'JetBrains Mono', ...;  /* Timeline numbers */
```

### 5.2 Agent Colors

Reuse existing color utility:
```typescript
import { getAgentBorderColor } from '../utils/agentColors'

// Returns consistent color per agent
const laneColor = getAgentBorderColor(agent.name, agent.id)
```

### 5.3 Event Type Styling

```css
/* Event cards by type - follow existing patterns */
.event-tool { background: rgba(251, 146, 60, 0.2); border-color: #fb923c; }
.event-thinking { background: rgba(168, 85, 247, 0.2); border-color: #a855f7; }
.event-response { background: rgba(34, 197, 94, 0.2); border-color: #22c55e; }
.event-hook { background: rgba(6, 182, 212, 0.2); border-color: #06b6d4; }
```

---

## 6. Responsive Design Considerations

### 6.1 Breakpoint Handling

```css
/* Desktop (default) - Full swimlane with controls */
.agent-swimlane {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Tablet (< 1200px) - Simplified controls */
@media (max-width: 1200px) {
  .swimlane-controls { gap: 0.5rem; }
  .lane-header { width: 120px; }
}

/* Mobile (< 650px) - Stack vertically or hide */
@media (max-width: 650px) {
  /* Option A: Force stream view on mobile */
  .view-mode-toggle .swimlane-btn { display: none; }

  /* Option B: Simplified swimlane with vertical scroll */
  .swimlane-row {
    flex-direction: column;
    min-height: 80px;
  }
}
```

### 6.2 Touch Interactions

- Event cards should have minimum 44x44px touch target
- Pinch-to-zoom for timeline (optional enhancement)
- Horizontal swipe for timeline panning

---

## 7. Implementation Priority

### Phase 1: Core Structure (MVP)
1. Create `AgentSwimlane.vue` with basic layout
2. Add `viewMode` state to store
3. Add view toggle to FilterControls
4. Implement `useSwimlane.ts` composable

### Phase 2: Lane Visualization
1. Create `SwimlaneRow.vue` component
2. Create `SwimlaneEventCard.vue` component
3. Implement event positioning logic
4. Apply agent colors to lanes

### Phase 3: Timeline & Interactions
1. Create `SwimlaneTimeline.vue` component
2. Implement zoom levels (hour/minute/second)
3. Add pan/scroll functionality
4. Add event hover tooltips

### Phase 4: Polish
1. Responsive design for all breakpoints
2. Animation for event additions
3. Event click to show details panel
4. Keyboard navigation support

---

## 8. File Summary

| Action | Path | Description |
|--------|------|-------------|
| CREATE | `components/AgentSwimlane.vue` | Main swimlane container |
| CREATE | `components/swimlane/SwimlaneRow.vue` | Agent lane component |
| CREATE | `components/swimlane/SwimlaneEventCard.vue` | Event visualization |
| CREATE | `components/swimlane/SwimlaneTimeline.vue` | Time axis header |
| CREATE | `composables/useSwimlane.ts` | Swimlane state/logic |
| MODIFY | `App.vue` | Add conditional rendering |
| MODIFY | `stores/orchestratorStore.ts` | Add viewMode state |
| MODIFY | `types.d.ts` | Add swimlane types |
| MODIFY | `components/FilterControls.vue` | Add view toggle |

---

**Report Complete**
Priority Level: Medium
Estimated Implementation: 3-5 development sessions
