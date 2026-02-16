<template>
  <div class="adw-swimlanes">
    <!-- ADW List Header -->
    <div class="adw-list-header">
      <h3>AI Developer Workflows</h3>
      <div class="header-controls">
        <!-- Event Type Filters -->
        <div class="category-filters">
          <button
            class="quick-filter-btn qf-response"
            :class="{ active: isFilterActive('response') }"
            @click="toggleFilter('response')"
            title="Show response events (TextBlock)"
          >
            <span class="filter-emoji">💬</span>
            Response
          </button>
          <button
            class="quick-filter-btn qf-tool"
            :class="{ active: isFilterActive('tool') }"
            @click="toggleFilter('tool')"
            title="Show tool events (ToolUseBlock)"
          >
            <span class="filter-emoji">🛠️</span>
            Tool
          </button>
          <button
            class="quick-filter-btn qf-thinking"
            :class="{ active: isFilterActive('thinking') }"
            @click="toggleFilter('thinking')"
            title="Show thinking events (ThinkingBlock)"
          >
            <span class="filter-emoji">🧠</span>
            Thinking
          </button>
          <button
            class="quick-filter-btn qf-hook"
            :class="{ active: isFilterActive('hook') }"
            @click="toggleFilter('hook')"
            title="Show hook events (PreToolUse, PostToolUse)"
          >
            <span class="filter-emoji">🪝</span>
            Hook
          </button>
          <button
            class="quick-filter-btn qf-system"
            :class="{ active: isFilterActive('system') }"
            @click="toggleFilter('system')"
            title="Show system events (StepStart, StepEnd, Stop)"
          >
            <span class="filter-emoji">⚙️</span>
            System
          </button>
        </div>
        <button
          class="btn-refresh"
          @click="store.fetchAdws()"
          :disabled="store.adwsLoading"
        >
          {{ store.adwsLoading ? "Loading..." : "Refresh" }}
        </button>
      </div>
    </div>

    <!-- ADW Swimlane List -->
    <div class="adw-swimlane-list">
      <div
        v-for="adw in store.adws"
        :key="adw.id"
        class="adw-swimlane-row"
        :class="[`status-${adw.status}`]"
      >
        <!-- ADW Header Row (info + duration) -->
        <div class="adw-header-row">
          <!-- ADW Info Section -->
          <div class="adw-info">
            <div class="adw-key">ADW: {{ adw.workflow_type }}</div>
            <div class="adw-name">{{ adw.adw_name }}</div>
            <div class="adw-status-row">
              <span class="adw-status-text" :class="`status-${adw.status}`">
                {{ adw.status }}
              </span>
            </div>
          </div>

          <!-- Duration in top-right corner -->
          <div class="adw-duration-corner">
            <span class="adw-duration" v-if="adw.duration_seconds">
              {{ formatDuration(adw.duration_seconds) }}
            </span>
            <span
              class="adw-duration duration-running"
              v-else-if="adw.started_at"
            >
              {{ getElapsedTime(adw.started_at) }}
            </span>
          </div>
        </div>

        <!-- Swimlane Steps - Wrapping Container -->
        <div class="adw-swimlanes-container">
          <div
            v-for="step in getStepsForAdw(adw.id)"
            :key="step"
            class="swimlane-step"
            :style="getStepBackgroundStyle(step)"
          >
            <div class="step-header">
              <span class="step-name">{{ formatStepName(step) }}</span>
            </div>
            <div class="step-squares">
              <div
                v-for="event in getEventsForStep(adw.id, step)"
                :key="event.id"
                class="swimlane-square"
                :class="[getEventClass(event)]"
                :title="getEventTooltip(event)"
                @click="selectEvent(event)"
              >
                <span class="square-icon">{{ getEventIcon(event) }}</span>
              </div>
            </div>
          </div>

          <!-- No events placeholder -->
          <div
            v-if="getStepsForAdw(adw.id).length === 0"
            class="no-events-inline"
          >
            <span v-if="adw.status === 'pending'">Waiting to start...</span>
            <span v-else-if="adw.status === 'in_progress'">Running...</span>
            <span v-else>No events</span>
          </div>
        </div>
      </div>

      <div v-if="store.adws.length === 0 && !store.adwsLoading" class="no-adws">
        No AI Developer Workflows found.
        <br />
        <span class="hint">Start an ADW from the orchestrator chat.</span>
      </div>
    </div>

    <!-- Event Detail Panel (Slide-out) -->
    <Transition name="slide">
      <div class="event-detail-panel" v-if="selectedEvent" ref="detailPanelRef">
        <div class="event-detail-header">
          <h4>Event Details</h4>
          <button class="btn-close" @click="selectedEvent = null">×</button>
        </div>
        <div class="event-detail-body">
          <!-- Summary at top with prominent styling -->
          <div class="event-summary-hero" v-if="selectedEvent.summary">
            <div class="summary-icon">{{ getEventIcon(selectedEvent) }}</div>
            <div class="summary-content">
              <span class="summary-label">Summary</span>
              <div class="summary-text">{{ selectedEvent.summary }}</div>
            </div>
          </div>
          <div class="event-summary-hero empty" v-else>
            <div class="summary-icon">{{ getEventIcon(selectedEvent) }}</div>
            <div class="summary-content">
              <span class="summary-label">Summary</span>
              <div class="summary-text">{{ selectedEvent.event_type }} event</div>
            </div>
          </div>

          <!-- Event metadata -->
          <div class="detail-row">
            <span class="detail-label">Type:</span>
            <span class="detail-value">{{ selectedEvent.event_type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Category:</span>
            <span class="detail-value">{{ selectedEvent.event_category }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Step:</span>
            <span class="detail-value">{{
              selectedEvent.adw_step || "workflow"
            }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Time:</span>
            <span class="detail-value">{{
              formatTime(selectedEvent.timestamp)
            }}</span>
          </div>
          <div class="detail-payload" v-if="selectedEvent.payload">
            <span class="detail-label">Payload:</span>
            <pre>{{ JSON.stringify(selectedEvent.payload, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useOrchestratorStore } from "../stores/orchestratorStore";
import type { AdwEvent } from "../types";

const store = useOrchestratorStore();
const selectedEvent = ref<AdwEvent | null>(null);
const detailPanelRef = ref<HTMLElement | null>(null);

// Filter state - which event types to show
type FilterType = "response" | "tool" | "thinking" | "hook" | "system";
const activeFilters = ref<Set<FilterType>>(new Set(["response", "tool", "thinking", "hook", "system"]));

function toggleFilter(filter: FilterType) {
  const newFilters = new Set(activeFilters.value);
  if (newFilters.has(filter)) {
    // Don't allow deselecting all filters
    if (newFilters.size > 1) {
      newFilters.delete(filter);
    }
  } else {
    newFilters.add(filter);
  }
  activeFilters.value = newFilters;
}

function isFilterActive(filter: FilterType): boolean {
  return activeFilters.value.has(filter);
}

// Map event types to filter categories
function getEventFilterCategory(event: AdwEvent): FilterType | null {
  const eventType = event.event_type;
  const category = event.event_category;

  // System events - step lifecycle, stop, system logs (from system_logs table with event_category="system")
  if (eventType === "StepStart" || eventType === "StepEnd" || eventType === "Stop" ||
      eventType?.startsWith("System") || category === "system") {
    return "system";
  }

  // Response category events
  if (eventType === "TextBlock" || eventType === "text" || eventType === "result") {
    return "response";
  }

  // Tool events
  if (eventType === "ToolUseBlock") {
    return "tool";
  }

  // Thinking events
  if (eventType === "ThinkingBlock") {
    return "thinking";
  }

  // Hook events
  if (category === "hook" || eventType === "PreToolUse" || eventType === "PostToolUse") {
    return "hook";
  }

  return null; // Unknown events always shown
}

// Load ADWs on mount
onMounted(() => {
  if (store.adws.length === 0) {
    store.fetchAdws();
  }
  // Add click-away listener
  document.addEventListener("click", handleClickAway);
});

onUnmounted(() => {
  // Clean up click-away listener
  document.removeEventListener("click", handleClickAway);
});

// Close panel when clicking outside of it
function handleClickAway(event: MouseEvent) {
  if (!selectedEvent.value) return;

  const target = event.target as HTMLElement;
  const panel = detailPanelRef.value;

  // Check if click is inside the panel
  if (panel && panel.contains(target)) return;

  // Check if click is on a swimlane square (opening a new event)
  if (target.closest(".swimlane-square")) return;

  // Close the panel
  selectedEvent.value = null;
}

function getStepsForAdw(adwId: string): string[] {
  const eventsByStep = store.allAdwEventsByStep[adwId];
  if (!eventsByStep) return [];
  return Object.keys(eventsByStep);
}

function getEventsForStep(adwId: string, step: string): AdwEvent[] {
  const eventsByStep = store.allAdwEventsByStep[adwId];
  if (!eventsByStep || !eventsByStep[step]) return [];

  // Filter events based on active filters
  return eventsByStep[step].filter((event) => {
    const filterCategory = getEventFilterCategory(event);
    // If no category (step events, unknown), always show
    if (filterCategory === null) return true;
    // Otherwise check if filter is active
    return activeFilters.value.has(filterCategory);
  });
}

function formatStepName(step: string): string {
  if (step === "_workflow") return "Workflow";
  return step
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatTime(timestamp: string): string {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function getElapsedTime(startedAt: string): string {
  const start = new Date(startedAt).getTime();
  const now = Date.now();
  const elapsed = Math.floor((now - start) / 1000);
  return formatDuration(elapsed);
}

function selectEvent(event: AdwEvent) {
  selectedEvent.value = event;
}

function getEventClass(event: AdwEvent): string {
  const classes: string[] = [];

  // By event type
  const eventType = event.event_type;
  if (eventType === "StepStart") classes.push("event-start");
  else if (eventType === "StepEnd") classes.push("event-end");
  else if (eventType === "PreToolUse") classes.push("event-tool-pre");
  else if (eventType === "PostToolUse") classes.push("event-tool");
  else if (eventType === "ToolUseBlock") classes.push("event-tool-block");
  else if (eventType === "ThinkingBlock") classes.push("event-thinking");
  else if (eventType === "TextBlock" || eventType === "text") classes.push("event-response");
  else if (eventType === "result") classes.push("event-result");
  else if (eventType === "Stop") classes.push("event-stop");
  // System log events
  else if (eventType?.startsWith("System")) classes.push("event-system");
  else classes.push("event-other");

  // By category
  if (event.event_category === "hook") classes.push("category-hook");
  else if (event.event_category === "response")
    classes.push("category-response");
  else if (event.event_category === "adw_step") classes.push("category-step");
  else if (event.event_category === "system") classes.push("category-system");

  return classes.join(" ");
}

function getEventIcon(event: AdwEvent): string {
  // Match icons used in AgentLogRow for consistency
  switch (event.event_type) {
    case "StepStart":
      return "▶";
    case "StepEnd":
      return "■";
    case "PreToolUse":
    case "PostToolUse":
      return "🪝"; // Hook icon (matches AgentLogRow HOOK category)
    case "ToolUseBlock":
      return "🛠️"; // Tool icon (matches AgentLogRow TOOL category)
    case "ThinkingBlock":
      return "🧠"; // Thinking icon (matches AgentLogRow THINKING category)
    case "TextBlock":
    case "text":
      return "💬"; // Response icon (matches AgentLogRow RESPONSE category)
    case "result":
      return "✓";
    case "Stop":
      return "⏹";
    // System log events
    case "SystemInfo":
      return "ℹ️";
    case "SystemWarning":
      return "⚠️";
    case "SystemError":
      return "❌";
    case "SystemDebug":
      return "🔍";
    default:
      // Check if it's a system event by category
      if (event.event_category === "system") {
        return "⚙️";
      }
      return "📋"; // Default icon (matches AgentLogRow default)
  }
}

function getEventTooltip(event: AdwEvent): string {
  return `${event.event_type}: ${event.summary || event.event_category}`;
}

/**
 * Hash a string to a consistent color
 * Uses HSL for visually distinct colors
 */
function hashStringToColor(str: string): { bg: string; border: string } {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32bit integer
  }

  // Use hue from hash (0-360), fixed saturation and lightness for dark theme
  const hue = Math.abs(hash) % 360;
  const saturation = 60 + (Math.abs(hash >> 8) % 20); // 60-80%
  const lightness = 45 + (Math.abs(hash >> 16) % 10); // 45-55%

  return {
    bg: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.15)`,
    border: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.4)`,
  };
}

function getStepBackgroundStyle(step: string): Record<string, string> {
  const colors = hashStringToColor(step);
  return {
    background: colors.bg,
    borderColor: colors.border,
  };
}
</script>

<style scoped>
.adw-swimlanes {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
  position: relative;
}

/* ADW List Header */
.adw-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.adw-list-header h3 {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* Category Filters - matches FilterControls.vue */
.category-filters {
  display: flex;
  gap: 4px;
  align-items: center;
}

.quick-filter-btn {
  padding: 0.375rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 4px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.quick-filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.filter-emoji {
  margin-right: 2px;
}

.qf-tool {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
  border-color: rgba(251, 146, 60, 0.3);
}

.qf-tool.active {
  background: #fb923c;
  color: white;
}

.qf-response {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
  border-color: rgba(34, 197, 94, 0.3);
}

.qf-response.active {
  background: var(--status-success);
  color: white;
}

.qf-thinking {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border-color: rgba(168, 85, 247, 0.3);
}

.qf-thinking.active {
  background: #a855f7;
  color: white;
}

.qf-hook {
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent-primary);
  border-color: rgba(6, 182, 212, 0.3);
}

.qf-hook.active {
  background: var(--accent-primary);
  color: white;
}

.qf-system {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border-color: rgba(148, 163, 184, 0.3);
}

.qf-system.active {
  background: #94a3b8;
  color: white;
}

.btn-refresh {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-refresh:hover {
  background: var(--bg-quaternary);
  color: var(--text-primary);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ADW Swimlane List */
.adw-swimlane-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* ADW Swimlane Row */
.adw-swimlane-row {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  border-left: 4px solid var(--border-color);
}

.adw-swimlane-row.status-in_progress {
  border-left-color: var(--status-warning);
}

.adw-swimlane-row.status-completed {
  border-left-color: var(--status-success);
}

.adw-swimlane-row.status-failed {
  border-left-color: var(--status-error);
}

.adw-swimlane-row.status-pending {
  border-left-color: var(--text-muted);
}

/* ADW Header Row - flexbox for info + duration */
.adw-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

/* Duration in top-right corner */
.adw-duration-corner {
  flex-shrink: 0;
  padding-left: var(--spacing-md);
}

/* ADW Info Section */
.adw-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.adw-key {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent-primary);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.adw-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.adw-status-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.adw-status-text {
  text-transform: uppercase;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-tertiary);
}

.adw-status-text.status-in_progress {
  background: rgba(251, 191, 36, 0.2);
  color: var(--status-warning);
}

.adw-status-text.status-completed {
  background: rgba(16, 185, 129, 0.2);
  color: var(--status-success);
}

.adw-status-text.status-failed {
  background: rgba(239, 68, 68, 0.2);
  color: var(--status-error);
}

.adw-duration {
  font-size: 0.75rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-weight: 600;
}

.duration-running {
  color: var(--status-warning);
  font-weight: 700;
}

/* Swimlanes Container - Wrapping Steps */
.adw-swimlanes-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  align-items: stretch;
  align-content: flex-start;
}

/* Swimlane Step - Unique colors via style binding, can grow but wraps */
.swimlane-step {
  border: 1px solid;
  border-radius: 8px;
  padding: var(--spacing-sm) var(--spacing-md);
  flex: 0 1 auto;
  max-width: 100%;
}

.step-header {
  margin-bottom: var(--spacing-sm);
}

.step-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Step Squares - Wrapping */
.step-squares {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 2x larger squares: 20px -> 40px */
.swimlane-square {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 1rem;
  background: var(--bg-tertiary);
  border: 2px solid var(--border-color);
}

.swimlane-square:hover {
  transform: scale(1.15);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.swimlane-square.event-start {
  background: rgba(6, 182, 212, 0.3);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.swimlane-square.event-end {
  background: rgba(16, 185, 129, 0.3);
  border-color: var(--status-success);
  color: var(--status-success);
}

.swimlane-square.event-tool-pre {
  background: rgba(251, 191, 36, 0.3);
  border-color: #fbbf24;
  color: #fbbf24;
}

.swimlane-square.event-tool {
  background: rgba(251, 146, 60, 0.3);
  border-color: #fb923c;
  color: #fb923c;
}

.swimlane-square.event-tool-block {
  background: rgba(234, 179, 8, 0.3);
  border-color: #eab308;
  color: #eab308;
}

.swimlane-square.event-thinking {
  background: rgba(168, 85, 247, 0.3);
  border-color: #a855f7;
  color: #a855f7;
}

.swimlane-square.event-response {
  background: rgba(59, 130, 246, 0.3);
  border-color: #3b82f6;
  color: #3b82f6;
}

.swimlane-square.event-result {
  background: rgba(16, 185, 129, 0.4);
  border-color: var(--status-success);
  color: var(--status-success);
}

.swimlane-square.event-stop {
  background: rgba(239, 68, 68, 0.3);
  border-color: #ef4444;
  color: #ef4444;
}

.swimlane-square.event-system {
  background: rgba(148, 163, 184, 0.3);
  border-color: #94a3b8;
  color: #94a3b8;
}

.swimlane-square.category-system {
  border-left: 3px solid #94a3b8;
}

.swimlane-square.event-other {
  background: rgba(156, 163, 175, 0.3);
  border-color: #9ca3af;
  color: #9ca3af;
}

.square-icon {
  font-size: 1rem;
  line-height: 1;
}

/* No events inline */
.no-events-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 150px;
  padding: var(--spacing-md);
  color: var(--text-muted);
  font-size: 0.8rem;
  font-style: italic;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border: 1px dashed var(--border-color);
}

/* No ADWs */
.no-adws {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-xl);
  font-size: 0.875rem;
}

.hint {
  font-size: 0.75rem;
  opacity: 0.7;
}

/* Event Detail Panel */
.event-detail-panel {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.event-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.event-detail-header h4 {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.btn-close {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: var(--bg-quaternary);
  color: var(--text-primary);
}

.event-detail-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

/* Summary Hero - Prominent top section */
.event-summary-hero {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.1));
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 8px;
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
}

.event-summary-hero.empty {
  background: linear-gradient(135deg, rgba(148, 163, 184, 0.1), rgba(100, 116, 139, 0.05));
  border-color: rgba(148, 163, 184, 0.2);
}

.summary-icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
  min-width: 0;
}

.summary-label {
  display: block;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--accent-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.summary-text {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--text-primary);
  font-weight: 500;
  word-wrap: break-word;
  overflow-wrap: break-word;
  /* Never truncate - show full text */
  white-space: normal;
}

.event-summary-hero.empty .summary-text {
  color: var(--text-muted);
  font-style: italic;
  font-weight: 400;
}

.event-summary-hero.empty .summary-label {
  color: var(--text-muted);
}

.detail-row {
  margin-bottom: var(--spacing-sm);
}

.detail-label {
  display: block;
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 2px;
}

.detail-value {
  font-size: 0.8rem;
  color: var(--text-primary);
}

.detail-payload {
  margin-top: var(--spacing-md);
}

.detail-payload pre {
  background: var(--bg-primary);
  padding: var(--spacing-sm);
  border-radius: 4px;
  font-size: 0.7rem;
  overflow-x: auto;
  color: var(--text-secondary);
  max-height: 300px;
  overflow-y: auto;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
