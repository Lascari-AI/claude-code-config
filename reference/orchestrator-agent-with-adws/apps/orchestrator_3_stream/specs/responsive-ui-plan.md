# Responsive UI Implementation Plan

**Objective:** Make the Orchestrator 3 Stream UI responsive for narrow viewport widths (< 650px) by implementing responsive behavior for AgentList and OrchestratorChat components.

**Target Viewport:** < 650px width

**Date:** 2025-01-08

---

## Executive Summary

This plan details the implementation of responsive design patterns for the multi-agent orchestration interface at narrow viewport widths (< 650px). The goal is to maintain full functionality while optimizing screen real estate for smaller displays. The approach focuses on:

1. **AgentList**: Implementing a mobile-optimized collapsed mode (always collapsed on mobile)
2. **OrchestratorChat**: Creating a compact small mode with reduced padding and optimized layout
3. **App Layout**: Adjusting grid layout for narrow screens
4. **AppHeader**: Simplifying header content for mobile displays
5. **EventStream**: Optimizing event row layout for narrow viewports

---

## Current State Analysis

### AgentList.vue (Left Sidebar)
- **Current width**: 280px (desktop), scales down to 240px at 1200px, 220px at 1024px
- **Collapsed mode**: Already implemented (48px when manually collapsed via button)
- **Structure**:
  - Header with title, agent count, collapse button
  - Agent cards with full details (name, status, template, task, context window, log counters, model, cost)
  - Compact view available (icon-only with first letter and status dot)
- **Key features**:
  - Manual collapse toggle
  - Pulsing animations on agent activity
  - Agent selection
  - Comprehensive agent information display

### OrchestratorChat.vue (Right Sidebar)
- **Current width**: 418px (sm), 518px (md), 618px (lg), scales down to 385px at 1400px, 352px at 1200px, 330px at 1024px
- **Structure**:
  - Header with width toggle, title, cost, context window display
  - Scrollable messages area
  - Empty state
  - Message bubbles (user & orchestrator)
  - Typing indicator
  - Thinking and Tool Use bubbles
- **Current responsive breakpoints**: Stops at 1024px, no handling for < 650px
- **Header stats**: Cost and context window displays in header

### App.vue (Main Layout)
- **Grid layout**: `grid-template-columns: 280px 1fr 418px` (default)
- **Responsive breakpoints**: 1600px, 1400px, 1200px, 1024px
- **Missing**: No breakpoint for < 650px
- **Grid adjusts for**:
  - Sidebar collapse state
  - Chat width variations (sm/md/lg)

### AppHeader.vue
- **Content**: Title, subtitle, connection status, stats (Active, Running, Logs, Cost), buttons (Clear All, Prompt)
- **Stats displayed**: 4 stat pills with emoji-style display
- **Responsive**: Has breakpoints at 1200px and 1024px reducing font sizes
- **Missing**: No handling for < 650px where content needs significant reduction

### EventStream.vue (Center Column)
- **Layout**: Filter controls at top, scrollable event rows below
- **Event row grid**: `grid-template-columns: 50px 80px 100px 1fr 180px`
- **Responsive**: Has breakpoint at 1200px reducing column widths
- **Missing**: No handling for < 650px where grid needs to stack or significantly reduce

### global.css
- **Design tokens**: CSS variables for colors, spacing, typography
- **Status colors**: Pre-defined for success, error, warning, info, debug
- **Scrollbar styling**: Custom webkit scrollbar
- **Utility classes**: Typography, badges, animations
- **Markdown styles**: Comprehensive styling for rendered markdown
- **No mobile-specific media queries**: Currently stops at standard desktop breakpoints

---

## Proposed Responsive Design (< 650px)

### 1. Overall Layout Strategy

**Breakpoint**: `@media (max-width: 650px)`

**Layout Approach**: Single-column stacked layout with collapsible sections

#### App.vue Grid Changes
```css
@media (max-width: 650px) {
  .app-main {
    /* Change from 3-column to stacked layout */
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
    /* OR maintain 3-column with heavily reduced sidebars */
    grid-template-columns: 48px 1fr 48px;
  }

  /* Force AgentList to always be collapsed on mobile */
  .app-sidebar.left {
    width: 48px;
    min-width: 48px;
  }

  /* Force OrchestratorChat to small mode */
  .app-sidebar.right {
    /* Option A: Hide completely with toggle button */
    display: none;

    /* Option B: Keep visible but very narrow */
    width: 48px;
    min-width: 48px;
  }
}
```

**Recommendation**: Use 3-column layout with 48px sidebars, allowing users to temporarily expand via overlay/modal pattern.

---

### 2. AgentList.vue - Mobile Collapsed Mode

#### Design Specification

**Default Behavior at < 650px**:
- Automatically collapse to 48px width
- Hide collapse button (always collapsed on mobile)
- Show compact agent items (first letter + status dot)
- Maintain agent selection functionality
- Keep pulsing animations for visual feedback

#### Implementation Details

**CSS Media Query**:
```css
@media (max-width: 650px) {
  /* Force collapsed state */
  .agent-list {
    width: 48px !important;
    min-width: 48px !important;
  }

  /* Hide header text elements */
  .agent-list-header h3,
  .agent-list-header .total-count,
  .agent-list-header .collapse-btn {
    display: none !important;
  }

  /* Adjust header padding for mobile */
  .agent-list-header {
    padding: 0.75rem 0.5rem;
    justify-content: center;
  }

  /* Hide full agent cards on mobile */
  .agent-list-content {
    display: none !important;
  }

  /* Always show compact view on mobile */
  .compact-agent-list {
    display: flex !important;
    padding: 0.5rem 0.25rem;
  }

  /* Optimize compact items for mobile */
  .compact-agent-item {
    padding: 0.4rem;
    min-height: 48px;
    touch-action: manipulation; /* Optimize for touch */
  }

  /* Increase tap target size for mobile */
  .compact-agent-letter {
    font-size: 1rem;
  }

  .compact-agent-dot {
    width: 8px;
    height: 8px;
  }
}
```

**Optional Enhancement**: Expandable overlay on tap
- When agent item is tapped, show overlay with full agent details
- Overlay appears over EventStream
- Includes dismiss button/gesture

---

### 3. OrchestratorChat.vue - Mobile Small Mode

#### Design Specification

**Layout Changes at < 650px**:
- Reduce header padding significantly
- Simplify header display (remove or stack stats)
- Make message bubbles narrower max-width
- Reduce message padding
- Compact empty state
- Optimize typing indicator

#### Implementation Details

**CSS Media Query**:
```css
@media (max-width: 650px) {
  .orchestrator-chat {
    /* Component stays full height */
  }

  /* Compact header */
  .chat-header {
    padding: 0.5rem 0.75rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* Stack header elements */
  .header-left,
  .header-right {
    flex: 1 1 100%;
    justify-content: space-between;
  }

  /* Hide width toggle on mobile (no point, always small) */
  .width-toggle-btn {
    display: none;
  }

  /* Compact title */
  .chat-header h3 {
    font-size: 0.75rem;
    letter-spacing: 0.03em;
  }

  /* Simplify header stats display */
  .header-right {
    border-left: none;
    padding-left: 0;
    gap: 0.5rem;
  }

  .cost-display,
  .context-display {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
  }

  /* Compact stat labels */
  .cost-label,
  .context-label {
    display: none; /* Hide labels, show only values */
  }

  .cost-value::before {
    content: "$";
  }

  /* Reduce message area padding */
  .chat-messages {
    padding: 0.5rem;
  }

  /* Wider message bubbles on small screens (more space usage) */
  .message-bubble {
    max-width: 92%;
    padding: 0.625rem 0.75rem;
    font-size: 0.8125rem;
  }

  /* Compact message header */
  .message-header {
    margin-bottom: 0.25rem;
    gap: 0.5rem;
  }

  .message-sender {
    font-size: 0.65rem;
  }

  .message-time {
    font-size: 0.65rem;
  }

  /* Compact empty state */
  .empty-state {
    padding: 1rem;
  }

  .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  .empty-title {
    font-size: 0.875rem;
  }

  .empty-subtitle {
    font-size: 0.75rem;
    max-width: 250px;
  }

  /* Touch-optimized typing indicator */
  .typing-indicator {
    padding: 0.5rem 0.75rem;
  }
}
```

**Alternative Approach**: Bottom sheet pattern
- Hide chat by default on mobile
- Floating action button to open chat as bottom sheet
- Bottom sheet slides up from bottom, covers 60-80% of screen
- Includes drag-to-dismiss gesture

---

### 4. AppHeader.vue - Mobile Simplified Header

#### Design Specification

**Changes at < 650px**:
- Single-row layout with essential info only
- Hide some stats or collapse into dropdown
- Reduce padding and font sizes
- Stack or hide less critical elements

#### Implementation Details

**CSS Media Query**:
```css
@media (max-width: 650px) {
  .app-header {
    padding: 0.5rem 0.75rem;
  }

  .header-content {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* Compact title */
  .header-title {
    flex: 1 1 100%;
    gap: 0.5rem;
  }

  .header-title h1 {
    font-size: 0.75rem;
    letter-spacing: 0.03em;
  }

  .header-subtitle {
    font-size: 0.65rem;
  }

  .connection-status {
    font-size: 0.65rem;
    padding-left: 0.5rem;
  }

  /* Compact stats - show only essential */
  .header-right {
    flex: 1 1 100%;
    gap: 0.5rem;
    justify-content: space-between;
  }

  .header-stats {
    gap: 0.25rem;
    flex-wrap: wrap;
  }

  /* Hide less critical stats on very narrow screens */
  .stat-pill:nth-child(3), /* Logs count */
  .stat-pill:nth-child(2) { /* Running count */
    display: none;
  }

  .stat-pill {
    padding: 0.25rem 0.5rem;
    font-size: 0.7rem;
  }

  .stat-pill .stat-label {
    font-size: 0.65rem;
  }

  .stat-pill .stat-value {
    font-size: 0.7rem;
  }

  /* Compact action buttons */
  .header-actions {
    gap: 0.25rem;
    padding-left: 0;
    border-left: none;
  }

  .btn-prompt,
  .btn-clear {
    padding: 0.25rem 0.5rem;
    font-size: 0.65rem;
  }

  /* Hide button hints on mobile */
  .btn-hint {
    display: none;
  }
}
```

---

### 5. EventStream.vue - Mobile Optimized Event Rows

#### Design Specification

**Changes at < 650px**:
- Stack event columns vertically or use 2-column layout
- Reduce padding between events
- Compact filter controls
- Prioritize content readability

#### Implementation Details

**CSS Media Query**:
```css
@media (max-width: 650px) {
  .event-stream-content {
    padding: 0.5rem;
    font-size: 0.75rem;
  }

  /* Simplified event item layout */
  .event-item {
    /* Change from 5-column to 2-row stacked layout */
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    gap: 0.25rem;
    padding: 0.5rem;
  }

  /* Alternative: 2-column compact layout */
  .event-item {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "line content"
      "meta meta";
    gap: 0.5rem;
    padding: 0.5rem;
  }

  .event-line-number {
    grid-area: line;
    font-size: 0.65rem;
  }

  .event-content {
    grid-area: content;
    font-size: 0.75rem;
  }

  .event-meta {
    grid-area: meta;
    font-size: 0.65rem;
  }

  /* Hide less critical metadata */
  .event-badge {
    font-size: 0.65rem;
  }

  /* Compact empty state */
  .empty-state {
    padding: 1rem;
  }

  .empty-icon {
    width: 64px;
    height: 64px;
  }

  .empty-title {
    font-size: 0.8125rem;
  }
}
```

**FilterControls.vue** (if exists - needs similar treatment):
```css
@media (max-width: 650px) {
  /* Collapse filter controls into dropdown/expandable section */
  /* Reduce filter button sizes */
  /* Stack filter rows */
}
```

---

### 6. Global CSS Additions

#### New Mobile Utility Classes

Add to `global.css`:

```css
/* ═══════════════════════════════════════════════════════════
   MOBILE RESPONSIVE UTILITIES (< 650px)
   ═══════════════════════════════════════════════════════════ */

/* Mobile-specific breakpoint */
@media (max-width: 650px) {
  /* Force no horizontal scroll */
  html, body {
    overflow-x: hidden;
  }

  /* Optimize touch targets (minimum 44x44px) */
  button,
  .agent-card,
  .compact-agent-item,
  .message-bubble {
    min-height: 44px;
    min-width: 44px;
  }

  /* Reduce global spacing on mobile */
  :root {
    --spacing-xs: 0.2rem;
    --spacing-sm: 0.35rem;
    --spacing-md: 0.65rem;
    --spacing-lg: 1rem;
    --spacing-xl: 1.25rem;
  }

  /* Smaller font sizes for mobile */
  body {
    font-size: 0.875rem;
  }

  h1 {
    font-size: 1.25rem;
  }

  h2 {
    font-size: 1.125rem;
  }

  h3 {
    font-size: 1rem;
  }

  /* Touch-optimized scrollbars */
  ::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }

  /* Reduce markdown spacing on mobile */
  .message-content h1,
  .thinking-text h1 {
    font-size: 1.125rem;
    margin: 0.75rem 0 0.4rem 0;
  }

  .message-content h2,
  .thinking-text h2 {
    font-size: 1rem;
    margin: 0.65rem 0 0.4rem 0;
  }

  .message-content h3,
  .thinking-text h3 {
    font-size: 0.9375rem;
    margin: 0.5rem 0 0.35rem 0;
  }

  .message-content pre,
  .thinking-text pre {
    padding: 0.5rem;
    margin: 0.5rem 0;
    font-size: 0.75rem;
    overflow-x: auto;
  }

  .message-content code,
  .thinking-text code {
    font-size: 0.8125em;
  }

  /* Utility classes for mobile visibility */
  .mobile-hidden {
    display: none;
  }

  .mobile-visible {
    display: block;
  }
}

/* Desktop-only utilities */
@media (min-width: 651px) {
  .desktop-hidden {
    display: none;
  }

  .desktop-visible {
    display: block;
  }
}
```

---

## Implementation Steps

### Phase 1: Foundation (Core Layout)
**Priority**: High
**Estimated Time**: 2-3 hours

1. **Update App.vue**
   - Add `@media (max-width: 650px)` breakpoint
   - Implement 3-column narrow layout (`48px 1fr 48px` or alternative)
   - Test layout switching at 650px breakpoint
   - Ensure smooth transitions

2. **Update global.css**
   - Add mobile utility classes
   - Add mobile breakpoint variable overrides
   - Add touch-optimized styles
   - Test scrollbar and font size changes

### Phase 2: AgentList Mobile Mode
**Priority**: High
**Estimated Time**: 2-3 hours

1. **Update AgentList.vue styles**
   - Add mobile media query
   - Force collapsed state at < 650px
   - Hide header text and collapse button
   - Always show compact view
   - Optimize compact items for touch
   - Test pulsing animations on mobile
   - Verify agent selection works

2. **Optional: Add agent detail overlay**
   - Create AgentDetailOverlay.vue component
   - Implement slide-in animation
   - Add dismiss gesture/button
   - Connect to agent selection

### Phase 3: OrchestratorChat Mobile Mode
**Priority**: High
**Estimated Time**: 2-3 hours

1. **Update OrchestratorChat.vue styles**
   - Add mobile media query
   - Compact header layout
   - Stack or simplify stats
   - Hide width toggle
   - Reduce message padding
   - Optimize message bubbles for mobile
   - Test typing indicator
   - Verify markdown rendering in messages

2. **Optional: Bottom sheet pattern**
   - Create floating action button
   - Implement bottom sheet component
   - Add drag-to-dismiss
   - Test on touch devices

### Phase 4: AppHeader Mobile Mode
**Priority**: Medium
**Estimated Time**: 1-2 hours

1. **Update AppHeader.vue styles**
   - Add mobile media query
   - Reduce padding
   - Hide less critical stats
   - Compact stat pills
   - Stack elements if needed
   - Hide button hints
   - Test connection status visibility

### Phase 5: EventStream Mobile Mode
**Priority**: Medium
**Estimated Time**: 2-3 hours

1. **Update EventStream.vue styles**
   - Add mobile media query
   - Simplify event row layout (2-column or stacked)
   - Reduce padding
   - Optimize font sizes
   - Test scrolling performance
   - Verify auto-scroll works

2. **Update FilterControls.vue** (if it exists)
   - Add mobile optimizations
   - Consider collapsible filters
   - Test filter interactions on touch

### Phase 6: Testing & Refinement
**Priority**: High
**Estimated Time**: 3-4 hours

1. **Device Testing**
   - Test on iOS Safari (iPhone SE, iPhone 12/13/14, iPad Mini)
   - Test on Android Chrome (various devices)
   - Test on Chrome DevTools device emulation
   - Test landscape orientation
   - Test with different zoom levels

2. **Interaction Testing**
   - Test all touch interactions
   - Verify tap targets are ≥ 44x44px
   - Test scrolling behavior
   - Test WebSocket updates on mobile
   - Test agent selection
   - Test chat input and sending
   - Test filter controls

3. **Performance Testing**
   - Monitor memory usage
   - Check for layout thrashing
   - Verify smooth scrolling
   - Test with many agents (10+)
   - Test with many events (100+)

4. **Accessibility Testing**
   - Test with screen reader (VoiceOver/TalkBack)
   - Test keyboard navigation (if applicable)
   - Verify color contrast ratios
   - Test with zoom enabled (200%)

---

## Files to Create/Modify

### Files to Modify

1. **frontend/src/App.vue**
   - Add mobile media query to `<style scoped>` section
   - Update grid layout for < 650px

2. **frontend/src/components/AgentList.vue**
   - Add mobile media query to `<style scoped>` section
   - Force collapsed mode on mobile
   - Optimize compact view for touch

3. **frontend/src/components/OrchestratorChat.vue**
   - Add mobile media query to `<style scoped>` section
   - Implement compact header
   - Reduce message padding
   - Optimize for narrow width

4. **frontend/src/components/AppHeader.vue**
   - Add mobile media query to `<style scoped>` section
   - Hide less critical stats
   - Compact layout

5. **frontend/src/components/EventStream.vue**
   - Add mobile media query to `<style scoped>` section
   - Simplify event row layout
   - Reduce padding

6. **frontend/src/styles/global.css**
   - Add mobile utilities section
   - Add mobile breakpoint overrides
   - Add touch-optimized styles

### Optional Files to Create

1. **frontend/src/components/AgentDetailOverlay.vue** (if implementing overlay pattern)
   - Overlay component for expanded agent details on mobile
   - Props: agent data, isVisible
   - Emits: close event

2. **frontend/src/components/ChatBottomSheet.vue** (if implementing bottom sheet)
   - Bottom sheet component for chat on mobile
   - Drag gesture support
   - Props: messages, isTyping
   - Emits: send, close

3. **frontend/src/composables/useMobileDetection.ts** (if needed)
   - Composable for detecting mobile viewport
   - Returns reactive boolean for isMobile
   - Handles resize events

---

## Technical Considerations

### 1. Viewport Width Detection

**Option A**: Pure CSS (Recommended)
- Use media queries exclusively
- No JavaScript required
- Automatic responsiveness
- Better performance

**Option B**: JavaScript + Composable
- Detect viewport in composable
- Expose reactive `isMobile` boolean
- Allow conditional rendering in templates
- More control but adds complexity

**Recommendation**: Use pure CSS media queries for simplicity and performance.

### 2. Touch Interactions

**Requirements**:
- Minimum tap target size: 44x44px (iOS/Android guidelines)
- Use `touch-action: manipulation` to prevent double-tap zoom
- Avoid hover-only interactions
- Add visual feedback for touch (active states)

**Implementation**:
```css
.compact-agent-item,
.message-bubble,
button {
  min-width: 44px;
  min-height: 44px;
  touch-action: manipulation;
  -webkit-tap-highlight-color: rgba(6, 182, 212, 0.2);
}

.compact-agent-item:active {
  transform: scale(0.95);
  background: #13152a;
}
```

### 3. Pulsing Animations on Mobile

**Consideration**: Animations can impact mobile performance

**Implementation**:
- Keep existing pulse animations (they're GPU-accelerated)
- Ensure animations use `transform` and `opacity` only
- Consider reducing animation duration on mobile
- Test with many agents pulsing simultaneously

```css
@media (max-width: 650px) {
  .compact-agent-item.agent-pulsing {
    /* Keep animation but possibly reduce duration */
    animation: compactAgentPulseBg 0.25s ease-out forwards;
  }
}
```

### 4. Scrolling Performance

**Optimization Techniques**:
- Use `will-change: transform` sparingly on scrollable containers
- Avoid expensive styles during scroll (box-shadow, filters)
- Use `content-visibility: auto` for long event lists (experimental)
- Test with many items (100+ events, 20+ agents)

```css
.event-stream-content,
.chat-messages,
.agent-list-content {
  /* Enable momentum scrolling on iOS */
  -webkit-overflow-scrolling: touch;

  /* Optimize scroll performance */
  overflow-y: auto;

  /* Paint optimization */
  transform: translateZ(0);
}
```

### 5. WebSocket Updates on Mobile

**Considerations**:
- Mobile browsers may throttle when app is backgrounded
- Need to handle reconnection gracefully
- Auto-scroll should work on mobile

**Testing**:
- Test with rapid event updates
- Test when switching tabs/apps
- Verify auto-scroll doesn't cause jank

### 6. Landscape Orientation

**Additional Breakpoint** (Optional):
```css
@media (max-width: 900px) and (orientation: landscape) {
  /* Tablet landscape mode */
  /* Keep 3-column layout but with reduced widths */
  .app-main {
    grid-template-columns: 64px 1fr 280px;
  }
}

@media (max-width: 650px) and (orientation: landscape) {
  /* Phone landscape mode */
  /* Ultra-compact layout */
  .app-main {
    grid-template-columns: 40px 1fr 40px;
  }
}
```

### 7. Design Token Overrides

**Mobile-specific spacing** (already planned in global.css):
- Reduce spacing variables at < 650px
- Use relative units (rem/em) for better scaling
- Maintain visual hierarchy

### 8. CSS Variables for Responsive Values

**Option**: Use CSS clamp() for fluid typography
```css
:root {
  /* Fluid font sizes using clamp */
  --font-size-base: clamp(0.875rem, 2vw, 1rem);
  --font-size-sm: clamp(0.75rem, 1.75vw, 0.875rem);
  --font-size-xs: clamp(0.65rem, 1.5vw, 0.75rem);

  /* Fluid spacing */
  --spacing-mobile: clamp(0.25rem, 1vw, 0.5rem);
}
```

**Recommendation**: Keep it simple initially, add fluid typography if needed later.

---

## Acceptance Criteria

### Layout Requirements
- [ ] App maintains 3-column layout at < 650px with narrower sidebars
- [ ] No horizontal scrolling at any viewport width ≥ 320px
- [ ] Smooth transitions when resizing across breakpoints
- [ ] Grid layout responds correctly to sidebar collapse state

### AgentList Requirements
- [ ] AgentList automatically collapses to 48px at < 650px
- [ ] Collapse button hidden on mobile (always collapsed)
- [ ] Compact agent view displays correctly (first letter + status dot)
- [ ] Agent selection works on mobile
- [ ] Pulsing animations work smoothly on mobile
- [ ] Status colors visible in compact view
- [ ] Tap targets are ≥ 44x44px

### OrchestratorChat Requirements
- [ ] Chat header is compact and readable at < 650px
- [ ] Width toggle hidden on mobile
- [ ] Cost and context stats visible and compact
- [ ] Message bubbles render correctly in narrow width
- [ ] Typing indicator displays properly
- [ ] Auto-scroll works on mobile
- [ ] Empty state is visible and well-formatted
- [ ] Markdown content renders correctly in messages

### AppHeader Requirements
- [ ] Header is compact at < 650px
- [ ] Essential stats remain visible (Active, Cost)
- [ ] Less critical stats hidden on very narrow screens
- [ ] Action buttons (Prompt, Clear All) remain functional
- [ ] Connection status indicator visible
- [ ] No text overflow or truncation issues

### EventStream Requirements
- [ ] Event rows layout works on narrow screens (2-column or stacked)
- [ ] Content remains readable
- [ ] Auto-scroll works smoothly
- [ ] Filter controls are accessible
- [ ] Empty state displays correctly
- [ ] Line numbers visible (if kept in mobile design)

### Performance Requirements
- [ ] Smooth scrolling on mobile devices (60fps target)
- [ ] No layout thrashing during WebSocket updates
- [ ] Animations perform well with multiple agents
- [ ] Page load time < 3s on 3G connection
- [ ] No memory leaks during extended use

### Interaction Requirements
- [ ] All tap targets ≥ 44x44px
- [ ] No hover-only interactions that break on touch
- [ ] Visual feedback for all touch interactions
- [ ] Double-tap zoom prevented where appropriate
- [ ] Pinch-to-zoom works on scrollable content
- [ ] Swipe gestures don't conflict with browser navigation

### Accessibility Requirements
- [ ] Color contrast ratios meet WCAG AA standards (4.5:1 for text)
- [ ] Content remains readable when zoomed to 200%
- [ ] Focus indicators visible on interactive elements
- [ ] Screen reader navigation works correctly
- [ ] Text doesn't overlap or get cut off

### Cross-Browser/Device Requirements
- [ ] Works on iOS Safari 14+
- [ ] Works on Chrome Mobile (latest)
- [ ] Works on Firefox Mobile (latest)
- [ ] Works on Android WebView
- [ ] Tested on iPhone SE (375px width)
- [ ] Tested on iPhone 12/13/14 (390px width)
- [ ] Tested on larger phones (414px+ width)
- [ ] Works in both portrait and landscape orientation

---

## Testing Recommendations

### 1. Browser DevTools Testing

**Chrome DevTools Device Emulation**:
1. Open DevTools (F12)
2. Enable device toolbar (Cmd+Shift+M / Ctrl+Shift+M)
3. Test these presets:
   - iPhone SE (375x667)
   - iPhone 12 Pro (390x844)
   - iPhone 14 Pro Max (430x932)
   - Pixel 5 (393x851)
   - Galaxy S20 (360x800)
4. Test custom viewport: 320px width (minimum support)
5. Test transition at 650px breakpoint (649px vs 651px)

**Firefox Responsive Design Mode**:
1. Open DevTools
2. Enable Responsive Design Mode (Cmd+Opt+M / Ctrl+Shift+M)
3. Test same devices as Chrome
4. Test touch simulation

### 2. Real Device Testing

**iOS Devices** (High Priority):
- iPhone SE (2020/2022) - 375px
- iPhone 12/13/14 - 390px
- iPhone 14 Plus/Pro Max - 428px
- iPad Mini - 744px (landscape)

**Android Devices**:
- Pixel 5 - 393px
- Samsung Galaxy S20 - 360px
- OnePlus 9 - 412px

**Test Cases**:
1. Load app and verify layout
2. Trigger agent activity, verify pulsing
3. Select agent, verify EventStream filters
4. Send chat message, verify typing indicator and response
5. Scroll all three panes
6. Test auto-scroll in EventStream and Chat
7. Test filter controls
8. Test Clear All button
9. Test Prompt button (Cmd+K)
10. Rotate to landscape, verify layout
11. Test with slow 3G connection
12. Test with many agents (10+) and events (100+)

### 3. Performance Testing

**Tools**:
- Chrome DevTools Performance tab
- Lighthouse mobile audit
- WebPageTest (mobile profile)

**Metrics to Monitor**:
- First Contentful Paint (< 2s target)
- Time to Interactive (< 3.5s target)
- Cumulative Layout Shift (< 0.1 target)
- Frame rate during scrolling (60fps target)
- Memory usage over time

**Test Scenarios**:
1. Initial page load
2. Scrolling EventStream with 100+ events
3. Adding 10 agents rapidly
4. All agents pulsing simultaneously
5. Sending 20 chat messages rapidly
6. Keeping app open for 30 minutes with constant updates

### 4. Accessibility Testing

**Tools**:
- Chrome Lighthouse accessibility audit
- axe DevTools extension
- iOS VoiceOver
- Android TalkBack

**Test Cases**:
1. Run Lighthouse accessibility audit (target score: 90+)
2. Test color contrast with DevTools
3. Test with 200% browser zoom
4. Test with VoiceOver enabled:
   - Navigate through agents
   - Read chat messages
   - Trigger actions
5. Verify all interactive elements have labels
6. Verify focus order is logical

### 5. WebSocket Testing

**Test Cases**:
1. Verify real-time updates appear instantly on mobile
2. Test reconnection when switching tabs
3. Test reconnection after backgrounding app (iOS)
4. Verify auto-scroll during rapid updates
5. Test with throttled connection (3G simulation)

### 6. Edge Case Testing

**Scenarios**:
1. Very long agent names (50+ characters)
2. Very long chat messages (1000+ characters)
3. Code blocks in chat on mobile
4. Tables in markdown on mobile
5. 50+ agents in list
6. 500+ events in stream
7. Empty states (no agents, no events, no messages)
8. Error states (disconnected, failed to load)

---

## Rollback Plan

### If Issues Arise

1. **CSS-only changes**: Easy to rollback
   - Comment out mobile media queries
   - Deploy without mobile styles
   - Minimum viewport width: 650px (desktop-only)

2. **Progressive rollout**:
   - Use feature flag for mobile CSS
   - Enable for internal testing first
   - Gradual rollout to users

3. **Fallback messaging**:
   - If mobile support isn't ready, show message:
   - "For best experience, please use a device with width ≥ 650px"

---

## Future Enhancements (Post-MVP)

### Phase 2 Features

1. **Advanced Mobile Navigation**
   - Bottom navigation bar for switching between Agent List / Stream / Chat
   - Swipe gestures to switch panes
   - Overlay/modal pattern for expanded views

2. **Mobile-Specific Features**
   - Pull-to-refresh for event stream
   - Voice input for chat
   - Haptic feedback for actions
   - Share agent data via native share sheet

3. **Progressive Web App (PWA)**
   - Add manifest.json
   - Service worker for offline support
   - Install prompt
   - Push notifications for agent updates

4. **Touch Gestures**
   - Swipe agent card for quick actions
   - Long-press for context menu
   - Pinch-to-zoom on agent details
   - Drag-to-reorder agents

5. **Advanced Responsive Features**
   - Tablet-optimized layout (768px - 1024px)
   - Multi-column layout on large tablets
   - Split-screen support
   - Picture-in-picture for chat

6. **Performance Optimizations**
   - Virtual scrolling for long lists
   - Lazy loading of images/markdown
   - Request idling during inactivity
   - Reduced motion mode for accessibility

---

## Dependencies & Prerequisites

### Required Knowledge
- Vue 3 Composition API
- CSS Grid and Flexbox
- Media queries
- Touch events
- Mobile browser quirks (Safari, Chrome)

### Tools Needed
- Chrome DevTools with device emulation
- iOS device or simulator (for testing)
- Android device or emulator (for testing)
- Lighthouse / axe for accessibility testing

### No Breaking Changes
- All changes are CSS-only (initially)
- No changes to component props or emits
- No changes to store structure
- No changes to WebSocket protocol
- Backwards compatible with desktop view

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review existing responsive patterns in codebase
- [ ] Set up device testing environment
- [ ] Create branch: `feature/mobile-responsive-ui`
- [ ] Inform team of upcoming changes

### Phase 1: Foundation
- [ ] Update App.vue with mobile grid layout
- [ ] Update global.css with mobile utilities
- [ ] Test layout switching at 650px
- [ ] Commit: "feat: add mobile grid layout foundation"

### Phase 2: AgentList
- [ ] Add mobile styles to AgentList.vue
- [ ] Force collapsed mode on mobile
- [ ] Test compact view on mobile
- [ ] Test agent selection on touch
- [ ] Commit: "feat: implement AgentList mobile mode"

### Phase 3: OrchestratorChat
- [ ] Add mobile styles to OrchestratorChat.vue
- [ ] Compact header layout
- [ ] Optimize message bubbles
- [ ] Test typing indicator
- [ ] Commit: "feat: implement OrchestratorChat mobile mode"

### Phase 4: AppHeader
- [ ] Add mobile styles to AppHeader.vue
- [ ] Hide less critical stats
- [ ] Test stat visibility
- [ ] Commit: "feat: implement AppHeader mobile mode"

### Phase 5: EventStream
- [ ] Add mobile styles to EventStream.vue
- [ ] Simplify event row layout
- [ ] Test scrolling performance
- [ ] Commit: "feat: implement EventStream mobile mode"

### Phase 6: Testing
- [ ] Test on Chrome DevTools device emulation
- [ ] Test on real iOS device
- [ ] Test on real Android device
- [ ] Run Lighthouse mobile audit
- [ ] Test accessibility with VoiceOver
- [ ] Test WebSocket updates on mobile
- [ ] Test performance with many agents/events
- [ ] Document any issues found

### Final Steps
- [ ] Create PR with screenshots/video
- [ ] Code review
- [ ] QA testing
- [ ] Merge to main
- [ ] Deploy to staging
- [ ] Final testing on staging
- [ ] Deploy to production
- [ ] Monitor for issues

---

## Notes for Build Agent

### Implementation Approach

1. **Start with CSS-only changes**: No JavaScript modifications needed initially
2. **Progressive enhancement**: Desktop experience remains unchanged
3. **Mobile-first within breakpoint**: Design for 375px, scale up to 650px
4. **Test frequently**: Check each component change on mobile emulator

### Key Files Priority

**High Priority** (core functionality):
1. `App.vue` - layout foundation
2. `global.css` - utilities and overrides
3. `AgentList.vue` - left sidebar mobile mode
4. `OrchestratorChat.vue` - right sidebar mobile mode

**Medium Priority** (important but not blocking):
5. `AppHeader.vue` - header mobile mode
6. `EventStream.vue` - center column mobile mode

### Code Style Guidelines

- Use existing CSS variable names
- Follow existing media query pattern
- Match existing animation timing (0.3s ease, 0.2s ease)
- Keep specificity low (avoid `!important` unless necessary)
- Add comments for complex mobile-specific logic
- Group mobile styles in single media query per component

### Testing During Development

After each component update:
1. Open Chrome DevTools
2. Enable device emulation (iPhone SE, 375px)
3. Verify layout looks correct
4. Test touch interactions (click, scroll)
5. Resize viewport from 650px down to 375px
6. Check for horizontal scrolling
7. Verify text is readable

### Common Pitfalls to Avoid

- ❌ Don't use fixed pixel widths for content (use %, rem, auto)
- ❌ Don't rely on hover states (use :active for touch)
- ❌ Don't create tap targets smaller than 44x44px
- ❌ Don't nest media queries excessively
- ❌ Don't override existing desktop styles unnecessarily
- ✅ Do use relative units (rem, em, %)
- ✅ Do test on real devices if possible
- ✅ Do maintain existing color scheme and design tokens
- ✅ Do keep animations smooth (GPU-accelerated properties)

### Debugging Tips

**If layout breaks**:
1. Check grid template columns syntax
2. Verify no conflicting media queries
3. Use DevTools computed styles to see what's applied
4. Check for typos in class names

**If touch doesn't work**:
1. Verify tap target size (should be ≥ 44px)
2. Check for `pointer-events: none`
3. Test `:active` pseudo-class
4. Verify `touch-action` is set correctly

**If performance is poor**:
1. Check for expensive CSS properties (box-shadow, filter)
2. Verify animations use `transform` and `opacity` only
3. Look for layout thrashing (forced reflows)
4. Test with Chrome DevTools Performance tab

---

## Success Metrics

### Technical Metrics
- Mobile Lighthouse score ≥ 90 (performance, accessibility, best practices)
- No horizontal scrolling at any viewport ≥ 320px
- Frame rate ≥ 55fps during scrolling (mobile)
- Time to Interactive < 3.5s on 3G

### User Experience Metrics
- All functionality accessible on mobile
- No loss of critical information
- Touch interactions feel natural
- Visual hierarchy maintained

### Code Quality Metrics
- No new console errors
- No new accessibility violations
- CSS complexity remains manageable
- Changes are well-documented

---

## Questions for Stakeholder

Before implementation, confirm:

1. **Layout Approach**:
   - ✅ Preferred: 3-column with 48px sidebars (AgentList/Chat collapsed)
   - ⚠️ Alternative: Full-screen center column with tab navigation
   - ⚠️ Alternative: Bottom sheet pattern for chat

2. **Feature Priority**:
   - Which is more important on mobile: Agent List or Chat?
   - Should one be hidden by default?

3. **Breakpoints**:
   - Is 650px the right breakpoint?
   - Should we support 320px width (very old phones)?
   - Should we add tablet breakpoint (768px)?

4. **Testing Devices**:
   - Which devices/browsers are priority for testing?
   - Do we have access to real devices for testing?

5. **Timeline**:
   - What's the target delivery date?
   - Can we do phased rollout (desktop → tablet → mobile)?

6. **Future Plans**:
   - Is PWA support planned?
   - Will there be a native mobile app?
   - Should we design for mobile-first going forward?

---

## Conclusion

This implementation plan provides a comprehensive approach to making the Orchestrator 3 Stream UI responsive for mobile devices at viewport widths < 650px. The strategy focuses on:

1. **CSS-only changes** for minimal risk and easy rollback
2. **Progressive enhancement** preserving desktop experience
3. **Touch-optimized interactions** following platform guidelines
4. **Performance-conscious design** ensuring smooth scrolling and animations
5. **Accessibility compliance** maintaining WCAG AA standards

The phased implementation approach allows for incremental progress with testing at each stage. The plan prioritizes core functionality (AgentList and OrchestratorChat) before moving to supporting components.

**Total Estimated Time**: 12-16 hours (including testing and refinement)

**Risk Level**: Low (CSS-only, non-breaking changes)

**Impact**: High (enables mobile users to access full functionality)

---

**Plan Author**: Claude (Frontend Architecture Planner Agent)
**Date**: 2025-01-08
**Version**: 1.0
**Status**: Ready for Implementation
