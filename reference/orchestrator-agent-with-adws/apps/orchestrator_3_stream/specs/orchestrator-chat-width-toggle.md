# OrchestratorChat Width Toggle Implementation Plan

## Problem Statement & Objectives

The OrchestratorChat component currently has a fixed width of 418px. Users need the ability to adjust the chat panel width to accommodate different amounts of content and screen sizes. This plan implements a toggle button that cycles through three predefined width sizes.

### Requirements
- Add a toggle button to the OrchestratorChat component header
- Support three width sizes:
  - Small (sm): 418px (current default)
  - Medium (md): 518px (+100px)
  - Large (lg): 618px (+200px)
- Toggle should cycle: sm → md → lg → sm
- Smooth transitions between sizes
- Persist user preference in localStorage
- Responsive behavior for different screen sizes

## Technical Approach

### Architecture Decisions
1. **State Management**: Use Pinia store to manage chat width state globally
2. **Persistence**: Store preference in localStorage for consistent experience
3. **Styling**: Use CSS custom properties for dynamic width values
4. **Animation**: CSS transitions for smooth width changes
5. **Icon**: Use width/expand icons to indicate current state

### Component Structure
```
App.vue (parent)
  ├── Manages grid layout with dynamic chat width
  └── OrchestratorChat.vue (child)
      └── Contains toggle button in header
```

## Step-by-Step Implementation Guide

### Step 1: Update Pinia Store
**File**: `frontend/src/stores/orchestratorStore.ts`

Add state and actions for managing chat width:
```typescript
// Add to state
chatWidth: 'sm' as 'sm' | 'md' | 'lg',

// Add getters
chatWidthPixels: (state) => {
  const widths = {
    sm: 418,
    md: 518,
    lg: 618
  }
  return widths[state.chatWidth]
},

// Add actions
toggleChatWidth() {
  const sizes = ['sm', 'md', 'lg'] as const
  const currentIndex = sizes.indexOf(this.chatWidth)
  const nextIndex = (currentIndex + 1) % sizes.length
  this.chatWidth = sizes[nextIndex]

  // Persist to localStorage
  localStorage.setItem('orchestrator_chat_width', this.chatWidth)
},

initializeChatWidth() {
  const saved = localStorage.getItem('orchestrator_chat_width')
  if (saved && ['sm', 'md', 'lg'].includes(saved)) {
    this.chatWidth = saved as 'sm' | 'md' | 'lg'
  }
}
```

### Step 2: Update OrchestratorChat Component
**File**: `frontend/src/components/OrchestratorChat.vue`

#### Template Changes
```vue
<!-- Update chat-header div -->
<div class="chat-header">
  <h3>CHAT</h3>

  <!-- Add width toggle button -->
  <div class="header-controls">
    <button
      class="width-toggle-btn"
      @click="handleToggleWidth"
      :title="`Chat width: ${currentWidthLabel}`"
    >
      <svg class="width-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <!-- Icon for width toggle -->
        <path v-if="chatWidth === 'sm'" d="M8 7h8m-8 5h8m-8 5h6" stroke-width="2" stroke-linecap="round"/>
        <path v-else-if="chatWidth === 'md'" d="M4 7h16m-16 5h16m-16 5h12" stroke-width="2" stroke-linecap="round"/>
        <path v-else d="M3 7h18m-18 5h18m-18 5h18" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div class="chat-status">
      <span class="status-indicator" :class="{ online: isConnected }"></span>
      <span class="status-text">{{ isConnected ? "Connected" : "Disconnected" }}</span>
    </div>
  </div>
</div>
```

#### Script Changes
```typescript
import { useOrchestratorStore } from '../stores/orchestratorStore'

// Add to setup
const store = useOrchestratorStore()

// Add computed properties
const chatWidth = computed(() => store.chatWidth)
const currentWidthLabel = computed(() => {
  const labels = {
    sm: 'Small',
    md: 'Medium',
    lg: 'Large'
  }
  return labels[store.chatWidth]
})

// Add handler
const handleToggleWidth = () => {
  store.toggleChatWidth()
}
```

#### Style Changes
```css
/* Update chat-header styles */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.width-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.width-toggle-btn:hover {
  background: rgba(0, 255, 255, 0.05);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.width-toggle-btn:active {
  transform: scale(0.95);
}

.width-icon {
  width: 18px;
  height: 18px;
}
```

### Step 3: Update App.vue Layout
**File**: `frontend/src/App.vue`

#### Template Changes
```vue
<!-- Update main element to use dynamic class -->
<main class="app-main"
      :class="{
        'sidebar-collapsed': isSidebarCollapsed,
        'chat-md': store.chatWidth === 'md',
        'chat-lg': store.chatWidth === 'lg'
      }">
```

#### Style Changes
```css
/* Base layout */
.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 418px;
  overflow: hidden;
  transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Chat width variations */
.app-main.chat-md {
  grid-template-columns: 280px 1fr 518px;
}

.app-main.chat-lg {
  grid-template-columns: 280px 1fr 618px;
}

/* Combined with sidebar collapsed */
.app-main.sidebar-collapsed {
  grid-template-columns: 48px 1fr 418px;
}

.app-main.sidebar-collapsed.chat-md {
  grid-template-columns: 48px 1fr 518px;
}

.app-main.sidebar-collapsed.chat-lg {
  grid-template-columns: 48px 1fr 618px;
}

/* Responsive adjustments */
@media (max-width: 1600px) {
  /* Limit large size on smaller screens */
  .app-main.chat-lg {
    grid-template-columns: 280px 1fr 518px; /* Fall back to medium */
  }

  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 518px;
  }
}

@media (max-width: 1400px) {
  .app-main {
    grid-template-columns: 260px 1fr 385px;
  }

  .app-main.chat-md {
    grid-template-columns: 260px 1fr 450px; /* Reduced increase */
  }

  .app-main.chat-lg {
    grid-template-columns: 260px 1fr 450px; /* Cap at medium */
  }
}

@media (max-width: 1200px) {
  /* Force small size on narrow screens */
  .app-main,
  .app-main.chat-md,
  .app-main.chat-lg {
    grid-template-columns: 240px 1fr 352px;
  }
}
```

### Step 4: Initialize Chat Width on App Mount
**File**: `frontend/src/App.vue`

```typescript
// In onMounted hook
onMounted(() => {
  store.initialize()
  store.initializeChatWidth() // Add this line
})
```

## Edge Cases & Considerations

### 1. Screen Size Constraints
- On screens < 1600px wide, large size falls back to medium
- On screens < 1200px wide, all sizes revert to small
- Prevents UI overflow and maintains usability

### 2. Transition Smoothness
- Use cubic-bezier easing for natural feel
- 300ms duration balances speed and smoothness
- Avoid layout jumps with consistent transition timing

### 3. LocalStorage Failures
- Wrap localStorage operations in try-catch
- Fallback to default 'sm' if read fails
- Continue functioning without persistence if storage unavailable

### 4. Keyboard Accessibility
- Add keyboard shortcut (Ctrl+Shift+W) for toggle
- Ensure button is keyboard focusable
- Provide clear aria-label for screen readers

## Testing Strategy

### Unit Tests
1. Store mutations for width toggle cycling
2. LocalStorage read/write operations
3. Computed property calculations for pixel values

### Integration Tests
1. Click toggle button → verify width changes
2. Refresh page → verify width persists
3. Resize window → verify responsive fallbacks

### Visual Regression Tests
1. Capture screenshots at each width size
2. Verify smooth transitions between states
3. Check responsive breakpoint behaviors

### Manual Testing Checklist
- [ ] Toggle cycles correctly: sm → md → lg → sm
- [ ] Transitions are smooth without jumps
- [ ] Width persists after page refresh
- [ ] Responsive fallbacks work at breakpoints
- [ ] Toggle button visual feedback on hover/active
- [ ] No content overflow at any width
- [ ] Chat functionality unaffected by width changes
- [ ] Keyboard shortcut works (if implemented)

## Success Criteria

✅ **Functional Requirements**
- Toggle button visible in chat header
- Three distinct width sizes functional
- Smooth cycling between sizes
- User preference persists across sessions

✅ **Performance Requirements**
- Transitions complete in < 300ms
- No layout thrashing during resize
- No impact on chat message rendering

✅ **User Experience**
- Clear visual feedback for current state
- Intuitive toggle behavior
- Graceful degradation on small screens
- No disruption to active conversations

## Implementation Notes

### File Modifications Summary
1. `frontend/src/stores/orchestratorStore.ts` - Add width state management
2. `frontend/src/components/OrchestratorChat.vue` - Add toggle button and handler
3. `frontend/src/App.vue` - Update grid layout for dynamic widths
4. `frontend/src/styles/global.css` - Add any missing CSS variables if needed

### Potential Enhancements (Future)
- Drag-to-resize functionality
- Custom width input option
- Per-agent width preferences
- Animate chat content during resize
- Add collapse to minimal view option