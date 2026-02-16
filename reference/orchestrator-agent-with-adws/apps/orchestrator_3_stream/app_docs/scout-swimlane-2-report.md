# Swimlane UI Component Placement Report

**Scout Report Date:** 2025-12-22
**Scope:** Orchestrator 3 Stream Frontend
**Objective:** Recommend optimal placement for a new swimlane UI component

---

## Executive Summary

After thoroughly analyzing the Orchestrator 3 Stream codebase, I recommend implementing the swimlane component as a **tabbed view within the center column**, alongside the existing EventStream. This approach minimizes layout disruption while providing a powerful visualization of agent hierarchy and parallel execution.

The current architecture uses a 3-column CSS Grid layout:
- **Left (280px)**: AgentList - agent cards with status
- **Center (1fr)**: EventStream - chronological event log
- **Right (418px)**: OrchestratorChat - chat interface

A swimlane visualization fits naturally as an alternative view in the center column, sharing the same data sources but presenting timeline-based horizontal lanes instead of a vertical log.

---

## 1. Code Location Recommendations

### 1.1 New Files to Create

| File Path | Purpose | Lines (Est.) |
|-----------|---------|--------------|
| `frontend/src/components/AgentSwimlane.vue` | Main swimlane container component | 200-300 |
| `frontend/src/components/swimlane/SwimlaneRow.vue` | Individual agent lane (horizontal bar) | 100-150 |
| `frontend/src/components/swimlane/SwimlaneEvent.vue` | Event markers on timeline (tool use, thinking, etc.) | 80-120 |
| `frontend/src/components/swimlane/SwimlaneTimeline.vue` | Time axis and grid lines | 100-150 |
| `frontend/src/components/swimlane/SwimlaneControls.vue` | Zoom, filter, and playback controls | 150-200 |
| `frontend/src/composables/useSwimlane.ts` | Swimlane state management, timeline calculations, zoom logic | 200-250 |

### 1.2 Files to Modify

| File Path | Modification Required | Impact |
|-----------|----------------------|--------|
| `frontend/src/App.vue` | Add view mode toggle (stream/swimlane) and conditional rendering | Medium |
| `frontend/src/types.d.ts` | Add `SwimlaneEvent`, `SwimlaneLane` interfaces; extend `Agent` with `parent_agent_id` | Low |
| `frontend/src/stores/orchestratorStore.ts` | Add swimlane visibility state, computed `agentHierarchy` getter | Medium |
| `frontend/src/styles/global.css` | Add swimlane CSS variables for consistent theming | Low |

### 1.3 Recommended Directory Structure

```
frontend/src/
├── components/
│   ├── AgentSwimlane.vue           ← NEW: Main swimlane container
│   ├── swimlane/                   ← NEW DIRECTORY
│   │   ├── SwimlaneRow.vue         ← Individual agent lane
│   │   ├── SwimlaneEvent.vue       ← Event marker component
│   │   ├── SwimlaneTimeline.vue    ← Time axis with grid
│   │   └── SwimlaneControls.vue    ← Toolbar with zoom/filter
│   ├── AgentList.vue               (existing - left sidebar)
│   ├── EventStream.vue             (existing - center column)
│   ├── OrchestratorChat.vue        (existing - right sidebar)
│   ├── FilterControls.vue          (existing - reusable pattern)
│   └── event-rows/                 (existing - event row components)
├── composables/
│   ├── useSwimlane.ts              ← NEW: Swimlane logic
│   ├── useEventStreamFilter.ts     (existing - can extend patterns)
│   ├── useAgentPulse.ts            (existing - reuse for animations)
│   └── useAgentColors.ts           (existing - reuse for lane colors)
├── stores/
│   └── orchestratorStore.ts        (modify - add swimlane state)
├── types.d.ts                      (modify - add swimlane types)
└── styles/
    └── global.css                  (modify - add swimlane variables)
```

---

## 2. UI Location Recommendation

### 2.1 Primary Recommendation: Tabbed Center Column

The swimlane should be implemented as an alternative view in the center column, toggled via tabs at the top of the content area.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APP HEADER                                      │
│  MULTI-AGENT ORCHESTRATION | Active: 3 | Running: 2 | Logs: 847 | Cost: $X  │
├───────────┬───────────────────────────────────────────────────┬─────────────┤
│           │  [Event Stream] [Swimlane]  ← TAB TOGGLE BUTTONS  │             │
│           ├───────────────────────────────────────────────────┤             │
│  AGENT    │                                                   │ ORCHESTRATOR│
│  LIST     │         CENTER COLUMN CONTENT                     │ CHAT        │
│           │    (Shows EventStream OR AgentSwimlane            │             │
│  (Left    │     based on selected tab)                        │  (Right     │
│  Sidebar) │                                                   │  Sidebar)   │
│           │                                                   │             │
│  280px    │              1fr (flexible width)                 │  418px      │
└───────────┴───────────────────────────────────────────────────┴─────────────┘
```

### 2.2 Swimlane View Layout (When Active)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Event Stream] [Swimlane●]                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ CONTROLS: [Zoom: ─────○─────] [Time: Last 5min ▼] [Filter: All Agents ▼]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIMELINE:    0:00      0:30      1:00      1:30      2:00      2:30        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Orchestrator ████████████████████████████████████████████████████████████  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ├─ scout-agent-1   ████████●◆░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│ ├─ scout-agent-2   ████████████●●◆░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│ └─ build-agent         ░░░░░░░░████████████●●●◆████████░░░░░░░░░░░░░░░░░  │
│     └─ test-runner                     ░░░░░░░░████████████●●██████████░  │
├─────────────────────────────────────────────────────────────────────────────┤
│ LEGEND: ████ Active  ░░░░ Idle/Waiting  ● Tool Use  ◆ Thinking  ✓ Complete │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Alternative Placements Considered

| Option | Placement | Pros | Cons | Verdict |
|--------|-----------|------|------|---------|
| **A (Recommended)** | Tabbed center column | No layout changes, easy toggle, preserves 3-column UX | Can't view both simultaneously | ✅ Best balance |
| **B** | Collapsible row above main grid | Full horizontal width, shows hierarchy clearly | More complex layout, takes vertical space | ⚠️ Viable alternative |
| **C** | Replace AgentList entirely | Shows hierarchy better than card list | Loses quick agent access sidebar | ❌ Too disruptive |
| **D** | Modal/overlay | Maximum space, non-intrusive | Breaks workflow, feels disconnected | ❌ Poor UX |
| **E** | Split center column (stream + swimlane) | See both views | Each view too cramped | ❌ Space constrained |

---

## 3. Component Architecture

### 3.1 Component Hierarchy

```
App.vue
├── AppHeader.vue
├── AgentList.vue (left)
├── [CENTER COLUMN - Modified]
│   ├── ViewToggle (new inline element)
│   ├── EventStream.vue (existing, shown when mode='stream')
│   └── AgentSwimlane.vue (new, shown when mode='swimlane')
│       ├── SwimlaneControls.vue
│       ├── SwimlaneTimeline.vue
│       └── SwimlaneRow.vue (v-for each agent)
│           └── SwimlaneEvent.vue (v-for each event)
├── OrchestratorChat.vue (right)
└── GlobalCommandInput.vue
```

### 3.2 Data Flow

```
orchestratorStore.ts
    │
    ├── agents: Agent[]
    ├── eventStreamEntries: EventStreamEntry[]
    ├── viewMode: 'stream' | 'swimlane'  ← NEW
    └── swimlaneState: {...}  ← NEW
           │
           ▼
    useSwimlane.ts (composable)
           │
           ├── swimlaneLanes: computed → SwimlaneLane[]
           ├── timeRange: computed → { start, end }
           ├── zoomLevel: ref
           └── filteredAgents: computed
           │
           ▼
    AgentSwimlane.vue
           │
           ├── SwimlaneControls.vue (zoom, filter inputs)
           ├── SwimlaneTimeline.vue (time axis)
           └── SwimlaneRow.vue[] (agent lanes)
                   │
                   └── SwimlaneEvent.vue[] (event markers)
```

### 3.3 Component Responsibilities

| Component | Responsibility | Props | Emits |
|-----------|---------------|-------|-------|
| `AgentSwimlane.vue` | Container, orchestrates sub-components | `agents`, `events` | `select-agent`, `select-event` |
| `SwimlaneControls.vue` | Zoom slider, time range picker, agent filter | `zoom`, `timeRange`, `agents` | `update:zoom`, `update:timeRange`, `update:filter` |
| `SwimlaneTimeline.vue` | Renders time axis with tick marks and grid | `timeRange`, `zoom` | - |
| `SwimlaneRow.vue` | Single agent's horizontal lane | `lane: SwimlaneLane`, `timeRange`, `zoom` | `select-event` |
| `SwimlaneEvent.vue` | Individual event marker (tool, thinking, etc.) | `event: SwimlaneEvent`, `color` | `click` |

---

## 4. Type Definitions

### 4.1 New Types to Add to `types.d.ts`

```typescript
// ═══════════════════════════════════════════════════════════
// SWIMLANE TYPES
// ═══════════════════════════════════════════════════════════

export type SwimlaneViewMode = 'stream' | 'swimlane'

export type SwimlaneEventType =
  | 'spawn'
  | 'tool_use'
  | 'thinking'
  | 'text'
  | 'complete'
  | 'error'
  | 'waiting'
  | 'blocked'

export interface SwimlaneEvent {
  id: string
  agentId: string
  agentName?: string
  type: SwimlaneEventType
  timestamp: Date
  endTimestamp?: Date        // For duration-based events
  duration?: number          // Milliseconds
  label?: string             // Short description
  metadata?: Record<string, any>
}

export interface SwimlaneLane {
  agent: Agent
  events: SwimlaneEvent[]
  depth: number              // Nesting level (0 = orchestrator, 1 = direct child, etc.)
  isExpanded: boolean        // For collapsible hierarchy
  children: SwimlaneLane[]   // Nested agents spawned by this agent
}

export interface SwimlaneTimeRange {
  start: Date
  end: Date
}

export interface SwimlaneState {
  viewMode: SwimlaneViewMode
  zoom: number               // 0.5 to 4.0 (50% to 400%)
  timeRange: SwimlaneTimeRange | null
  selectedAgentIds: string[] // Filter to specific agents
  showCompleted: boolean     // Show/hide completed agents
  autoFollow: boolean        // Auto-scroll to latest events
}
```

### 4.2 Agent Interface Extension

```typescript
// Extend existing Agent interface
export interface Agent {
  // ... existing fields ...

  // NEW: For swimlane hierarchy visualization
  parent_agent_id?: string | null    // ID of agent that spawned this one
  spawned_at?: string                // ISO timestamp when agent was created
  completed_at?: string | null       // ISO timestamp when agent finished
}
```

---

## 5. Styling Guidelines

### 5.1 CSS Variables to Add to `global.css`

```css
:root {
  /* ═══════════════════════════════════════════════════════════
     SWIMLANE COLORS
     ═══════════════════════════════════════════════════════════ */

  /* Lane backgrounds */
  --swimlane-bg: #0a0a0a;
  --swimlane-lane-bg: #0d0f1a;
  --swimlane-lane-bg-alt: #12141f;
  --swimlane-lane-border: rgba(255, 255, 255, 0.08);
  --swimlane-lane-hover: rgba(255, 255, 255, 0.03);

  /* Timeline */
  --swimlane-timeline-bg: #1a1a1a;
  --swimlane-grid-line: rgba(255, 255, 255, 0.05);
  --swimlane-grid-line-major: rgba(255, 255, 255, 0.1);
  --swimlane-tick-color: var(--text-dim);

  /* Event type colors (match existing status colors) */
  --swimlane-event-spawn: var(--status-success);      /* #10b981 green */
  --swimlane-event-tool: var(--status-warning);       /* #f59e0b orange */
  --swimlane-event-thinking: #a855f7;                 /* purple */
  --swimlane-event-text: var(--accent-primary);       /* #06b6d4 cyan */
  --swimlane-event-complete: var(--text-muted);       /* gray */
  --swimlane-event-error: var(--status-error);        /* #ef4444 red */
  --swimlane-event-waiting: #eab308;                  /* yellow */
  --swimlane-event-blocked: var(--status-error);      /* red */

  /* Active/Idle bars */
  --swimlane-bar-active: rgba(6, 182, 212, 0.6);      /* cyan with opacity */
  --swimlane-bar-idle: rgba(255, 255, 255, 0.1);
  --swimlane-bar-executing: rgba(16, 185, 129, 0.6);  /* green */

  /* Controls */
  --swimlane-control-bg: var(--bg-secondary);
  --swimlane-control-border: var(--border-color);
}
```

### 5.2 Styling Patterns to Follow

1. **Reuse existing agent colors** from `useAgentColors.ts` for lane borders
2. **Reuse pulse animations** from `useAgentPulse.ts` for active event highlighting
3. **Follow responsive breakpoints** defined in `global.css` (650px mobile, 1024px tablet)
4. **Use CSS Grid** for timeline layout (matches existing patterns)
5. **Use scoped styles** in Vue components (all existing components use `<style scoped>`)

---

## 6. Integration Points

### 6.1 Store Integration

```typescript
// In orchestratorStore.ts, add to state section:

// Swimlane state
const swimlaneState = ref<SwimlaneState>({
  viewMode: 'stream',
  zoom: 1.0,
  timeRange: null,
  selectedAgentIds: [],
  showCompleted: true,
  autoFollow: true
})

// Add computed getter for agent hierarchy
const agentHierarchy = computed<SwimlaneLane[]>(() => {
  // Build tree structure from flat agents array
  // Root = orchestrator (no parent_agent_id)
  // Children = agents where parent_agent_id matches
})

// Add computed getter for swimlane events
const swimlaneEvents = computed<SwimlaneEvent[]>(() => {
  // Transform eventStreamEntries to SwimlaneEvent format
  // Map event types: tool_use_block → 'tool_use', thinking_block → 'thinking', etc.
})
```

### 6.2 WebSocket Event Handling

The existing WebSocket handlers in `orchestratorStore.ts` (lines 320-425) already capture:
- `onAgentCreated` → Map to swimlane 'spawn' event
- `onAgentStatusChange` → Update lane status
- `onToolUseBlock` → Map to swimlane 'tool_use' event
- `onThinkingBlock` → Map to swimlane 'thinking' event
- `onAgentLog` → Map to appropriate event type

No new WebSocket messages needed—just transform existing data.

### 6.3 Composable Reuse

| Existing Composable | Reuse in Swimlane |
|---------------------|-------------------|
| `useAgentPulse.ts` | Highlight active lanes during events |
| `useAgentColors.ts` | Color-code lanes by agent |
| `useEventStreamFilter.ts` | Pattern for filter state management |
| `useHeaderBar.ts` | Pattern for computed stats |

---

## 7. Implementation Phases

### Phase 1: Foundation (1-2 days)
- Create `AgentSwimlane.vue` shell component
- Add tab toggle to `App.vue` center column
- Add `viewMode` state to store
- Define types in `types.d.ts`

### Phase 2: Core Components (2-3 days)
- Implement `useSwimlane.ts` composable
- Build `SwimlaneTimeline.vue` with time axis
- Build `SwimlaneRow.vue` for agent lanes
- Build `SwimlaneEvent.vue` for event markers

### Phase 3: Controls & Polish (1-2 days)
- Implement `SwimlaneControls.vue` toolbar
- Add zoom and pan functionality
- Add agent filtering
- Style refinement and animations

### Phase 4: Integration (1 day)
- Connect to real-time WebSocket events
- Add auto-follow (scroll to latest)
- Test with multiple concurrent agents

### Phase 5: Responsive & Testing (1 day)
- Mobile responsive adjustments
- Playwright validation per CLAUDE.md requirements
- Edge case testing (many agents, long durations)

---

## 8. Rationale Summary

### Why Tabbed Center Column?

| Criteria | Score | Explanation |
|----------|-------|-------------|
| **Layout Disruption** | ✅ Minimal | No changes to 3-column grid structure |
| **Implementation Complexity** | ✅ Low | Tab toggle is simple state change |
| **Code Reuse** | ✅ High | Uses existing store, types, composables |
| **User Experience** | ✅ Good | Familiar tab pattern, preserves context |
| **Responsive Support** | ✅ Native | Follows existing responsive breakpoints |
| **Future Extensibility** | ✅ High | Easy to add more view modes later |

### Key Benefits

1. **Non-Destructive** - EventStream remains fully functional; swimlane is additive
2. **Context Preserved** - AgentList (left) and Chat (right) remain visible for reference
3. **Consistent Architecture** - Follows existing Vue 3 + Pinia + Composables patterns
4. **Incremental Delivery** - Can ship basic swimlane quickly, enhance iteratively
5. **Performance Safe** - Switching views unmounts unused component, no dual rendering

---

## 9. Files Reference

### Existing Files Analyzed

| File | Lines | Key Insights |
|------|-------|--------------|
| `App.vue` | 261 | 3-column grid layout, responsive breakpoints |
| `types.d.ts` | 391 | Agent, EventStreamEntry, ChatMessage types |
| `orchestratorStore.ts` | 1133 | WebSocket handlers, agent/event state |
| `AgentList.vue` | 894 | Agent card rendering, pulse animations |
| `EventStream.vue` | 381 | Event filtering, auto-scroll pattern |
| `OrchestratorChat.vue` | 771 | Chat layout, typing indicators |
| `global.css` | 695 | CSS variables, responsive utilities |
| `useAgentPulse.ts` | - | Animation composable pattern |
| `useAgentColors.ts` | - | Agent color generation |
| `useEventStreamFilter.ts` | - | Filter state management pattern |

---

## 10. Conclusion

The recommended approach places the swimlane component in the **center column as a tabbed alternative to EventStream**. This provides:

- **Minimal code changes** to existing layout
- **Maximum reuse** of existing state, types, and styling
- **Clean separation** between list view (EventStream) and timeline view (Swimlane)
- **Familiar UX pattern** (tabs) that users understand
- **Clear implementation path** with phased delivery

The swimlane will visualize agent hierarchies (orchestrator → subagents), parallel execution, and event timelines—providing a powerful complement to the existing chronological log view.

---

*Report generated by Scout Agent analyzing Orchestrator 3 Stream codebase*
