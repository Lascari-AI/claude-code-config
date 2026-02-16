<template>
  <div class="event-stream">
    <!-- Filter Controls Component -->
    <FilterControls
      :category-filters="categoryFilters"
      :quick-filters="quickFilters"
      :agent-filters="agentFilters"
      :tool-filters="toolFilters"
      :search-query="searchQuery"
      :auto-scroll="autoScroll"
      :active-quick-filters="activeQuickFilters"
      :active-agent-filters="activeAgentFilters"
      :active-category-filters="activeCategoryFilters"
      :active-tool-filters="activeToolFilters"
      @quick-filter-toggle="toggleQuickFilter"
      @agent-filter-toggle="toggleAgentFilter"
      @category-filter-toggle="toggleCategoryFilter"
      @tool-filter-toggle="toggleToolFilter"
      @update:search-query="searchQuery = $event"
      @auto-scroll-toggle="store.toggleAutoScroll"
      @clear-all="store.clearEventStream"
    />

    <div class="event-stream-content" ref="streamRef">
      <!-- Empty State -->
      <div v-if="filteredEvents.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg
            width="98"
            height="98"
            viewBox="0 0 98 98"
            xmlns="http://www.w3.org/2000/svg"
          >
            <!-- 3x3 grid of rounded rectangles -->
            <!-- Row 1 -->
            <rect x="0" y="0" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="34" y="0" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="68" y="0" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>

            <!-- Row 2 -->
            <rect x="0" y="34" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="34" y="34" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="68" y="34" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>

            <!-- Row 3 -->
            <rect x="0" y="68" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="34" y="68" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
            <rect x="68" y="68" width="30" height="30" rx="2" fill="#000" stroke="#404040" stroke-width="1"/>
          </svg>
        </div>
        <p class="empty-title">
          {{
            searchQuery
              ? "No events match your search"
              : "No events yet. Waiting for agent activity..."
          }}
        </p>
      </div>

      <!-- Event Items -->
      <div v-else class="event-items">
        <template v-for="event in filteredEvents" :key="event.id">
          <component
            v-if="getEventComponent(event)"
            :is="getEventComponent(event)"
            :event="getEventData(event)"
            :line-number="event.lineNumber"
          />
        </template>
      </div>

      <!-- Auto-scroll anchor -->
      <div ref="bottomRef"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  watch,
  nextTick,
  onMounted,
  ref,
  type ComputedRef,
} from "vue";
import { useOrchestratorStore } from "../stores/orchestratorStore";
import { useEventStreamFilter } from "../composables/useEventStreamFilter";
import FilterControls from "./FilterControls.vue";
import AgentLogRow from "./event-rows/AgentLogRow.vue";
import AgentToolUseBlockRow from "./event-rows/AgentToolUseBlockRow.vue";
import type { EventStreamEntry } from "../types";

// Store
const store = useOrchestratorStore();

// Get events from store
const events: ComputedRef<EventStreamEntry[]> = computed(
  () => store.filteredEventStream
);

// Use filter composable (without autoScroll, which is now in store)
const {
  activeAgentFilters,
  activeCategoryFilters,
  activeToolFilters,
  activeQuickFilters,
  searchQuery,
  categoryFilters,
  quickFilters,
  agentFilters,
  toolFilters,
  filteredEvents,
  toggleQuickFilter,
  toggleAgentFilter,
  toggleCategoryFilter,
  toggleToolFilter,
  clearAllFilters,
} = useEventStreamFilter(() => events.value);

// Get autoScroll from store (shared with OrchestratorChat)
const autoScroll = computed(() => store.autoScroll);

// Get appropriate component for event type
function getEventComponent(event: EventStreamEntry) {
  // Check for special block types first (for the orchestrator, no need to display this here its in the chat)
  if (event.sourceType === "thinking_block") {
    // return ThinkingBlockRow;
    return null;
  }
  // Skip tool_use_block - orchestrator tools only show in chat
  if (event.sourceType === "tool_use_block") {
    return null;
  }
  // SKIP: orchestrator_chat messages in event stream for searchability
  if (event.sourceType === "orchestrator_chat") {
    return null; // Don't display in event stream, only in chat
  }

  // Then check standard types
  switch (event.sourceType) {
    case "agent_log":
      // Check if this is an agent tool use event
      const eventType = event.eventType?.toLowerCase();
      if (eventType === "tool_use" || eventType === "tooluseblock") {
        return AgentToolUseBlockRow;
      }
      return AgentLogRow;
    default:
      return AgentLogRow; // Fallback
  }
}

// Get event data in correct format for component
function getEventData(event: EventStreamEntry) {
  // For thinking_block events
  if (event.sourceType === "thinking_block") {
    return event.metadata?.data || event;
  }

  // For tool_use_block events
  if (event.sourceType === "tool_use_block") {
    return event.metadata?.data || event;
  }

  // For orchestrator_chat events, pass the metadata which contains all needed fields
  if (event.sourceType === "orchestrator_chat") {
    return {
      message: event.content,
      sender_type: event.metadata?.sender_type || "user",
      receiver_type: event.metadata?.receiver_type || "orchestrator",
      agent_id: event.metadata?.agent_id,
      orchestrator_agent_id: event.metadata?.orchestrator_agent_id,
      timestamp: event.timestamp,
      created_at: event.timestamp, // Provide both for compatibility
      id: event.id,
      metadata: event.metadata,
    };
  }
  // EventStreamEntry metadata contains the original event for other types
  return event.metadata?.originalEvent || event;
}

// Refs
const streamRef = ref<HTMLElement>();
const bottomRef = ref<HTMLElement>();

// Auto-scroll to bottom when new events arrive or filters change
watch(
  () => filteredEvents.value.length,
  async () => {
    if (autoScroll.value) {
      await nextTick();
      bottomRef.value?.scrollIntoView({ behavior: "smooth" });
    }
  }
);

const formatTime = (timestamp: string | Date) => {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// Load event history on mount
onMounted(async () => {
  // Events are loaded in store.initialize()
  // This component just displays them

  // Scroll to bottom after initial render
  await nextTick();
  if (autoScroll.value && bottomRef.value) {
    bottomRef.value.scrollIntoView({ behavior: "auto" });
  }
});

// Expose methods for parent components
defineExpose({
  toggleAgentFilter,
  clearAllFilters,
});
</script>

<style scoped>
.event-stream {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.event-stream-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  line-height: 1.6;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon {
  width: 98px;
  height: 98px;
  margin-bottom: var(--spacing-md);
  opacity: 0.3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-title {
  font-size: 0.875rem;
}

/* Event Items */
.event-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-item {
  display: grid;
  grid-template-columns: 50px 80px 100px 1fr 180px;
  gap: var(--spacing-md);
  align-items: baseline;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-left: 3px solid transparent;
  transition: all 0.15s ease;
}

.event-item:hover {
  background: var(--bg-tertiary);
}

/* Event Level Styling */
.event-info {
  border-left-color: var(--status-info);
}

.event-debug {
  border-left-color: var(--status-debug);
}

.event-success {
  border-left-color: var(--status-success);
}

.event-warn {
  border-left-color: var(--status-warning);
}

.event-error {
  border-left-color: var(--status-error);
  background: rgba(239, 68, 68, 0.05);
}

.event-line-number {
  font-size: 0.75rem;
  color: var(--text-dim);
  text-align: right;
}

.event-badge {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.025em;
}

.badge-info {
  color: var(--status-info);
}

.badge-debug {
  color: var(--status-debug);
}

.badge-success {
  color: var(--status-success);
}

.badge-warn {
  color: var(--status-warning);
}

.badge-error {
  color: var(--status-error);
}

.event-agent {
  font-size: 0.75rem;
  color: var(--agent-active);
  font-weight: 600;
}

.event-content {
  color: var(--text-primary);
  word-wrap: break-word;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  justify-content: flex-end;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.event-tokens {
  color: var(--status-warning);
}

.event-time {
  color: var(--text-dim);
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .event-item {
    grid-template-columns: 40px 70px 80px 1fr 150px;
    gap: var(--spacing-sm);
  }
}
</style>
