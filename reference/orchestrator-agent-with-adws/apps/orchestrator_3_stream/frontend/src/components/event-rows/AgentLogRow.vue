<template>
  <div class="agent-log-row-wrapper">
    <div
      class="event-row agent-log-row"
      :class="[`event-${level.toLowerCase()}`, { 'is-expanded': isExpanded }]"
      :style="{
        borderLeftColor: agentColor,
        backgroundColor: agentBackgroundColor,
      }"
    >
      <div class="event-line-number">{{ lineNumber }}</div>

      <div
        class="event-category-badge"
        :class="`category-${displayCategory.toLowerCase()}`"
      >
        {{ categoryIcon }}
        {{ displayCategory }}
      </div>

      <div class="event-agent">
        <span class="agent-id" :style="{ borderColor: agentColor }">{{
          agentDisplayName
        }}</span>
      </div>

      <div class="event-content" @click="toggleExpanded">
        <span class="event-type">{{ displayEventType }}</span>

        <!-- Response content (payload.text) - expandable -->
        <span
          v-if="displayCategory === 'RESPONSE'"
          class="event-summary clickable"
          v-html="formattedContent"
        ></span>

        <!-- Tool content (summary) - expandable -->
        <span
          v-else-if="displayCategory === 'TOOL'"
          class="event-summary clickable"
          v-html="formattedContent"
        ></span>

        <!-- Thinking content (summary) - expandable -->
        <span
          v-else-if="displayCategory === 'THINKING'"
          class="event-summary clickable"
          v-html="formattedContent"
        ></span>

        <!-- Hook content - expandable -->
        <span
          v-else-if="displayCategory === 'HOOK'"
          class="event-summary clickable"
          v-html="formattedContent"
        ></span>

        <!-- Other content -->
        <span v-else class="event-summary" v-html="formattedContent"></span>
      </div>

      <div class="event-meta">
        <span v-if="tokens" class="event-tokens">🪙 {{ tokens }} tokens</span>
        <span class="event-time">{{ formatTime(event.timestamp) }}</span>
      </div>
    </div>

    <!-- File Changes Display - integrated inside response block -->
    <div
      v-if="hasFileActivity && event.event_category === 'response'"
      class="file-tracking-container"
      :style="{
        borderLeftColor: agentColor,
        backgroundColor: agentBackgroundColor,
      }"
    >
      <FileChangesDisplay
        :file-changes="fileChanges"
        :read-files="readFiles"
        layout="two-column"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type {
  AgentLog,
  FileChange,
  FileRead,
  AgentLogMetadata,
} from "../../types";
import { renderMarkdown } from "../../utils/markdown";
import {
  getAgentBorderColor,
  getAgentBackgroundColor,
} from "../../utils/agentColors";
import FileChangesDisplay from "./FileChangesDisplay.vue";
import { useOrchestratorStore } from "../../stores/orchestratorStore";

interface Props {
  event: AgentLog;
  lineNumber: number;
}

const props = defineProps<Props>();

const store = useOrchestratorStore();
const isExpanded = ref(false);

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value;
};

// Generate agent-specific colors using shared utility
const agentColor = computed(() =>
  getAgentBorderColor(props.event.agent_name, props.event.agent_id)
);

const agentBackgroundColor = computed(() =>
  getAgentBackgroundColor(props.event.agent_name, props.event.agent_id)
);

const level = computed(() => {
  // Map event type to display level
  const type = props.event.event_type?.toLowerCase() || "";
  if (type.includes("error")) return "ERROR";
  if (type.includes("warn")) return "WARN";
  if (type.includes("success")) return "SUCCESS";
  if (type.includes("debug")) return "DEBUG";
  return "INFO";
});

const displayCategory = computed(() => {
  // Determine high-level category based on event type
  const type = props.event.event_type?.toLowerCase() || "";

  // Tools are a top-level category
  if (type === "tool_use" || type === "tooluseblock") return "TOOL";

  // Thinking blocks
  if (type === "thinking" || type === "thinkingblock") return "THINKING";

  // Text responses
  if (type === "text" || type === "textblock") return "RESPONSE";

  // Hooks
  if (props.event.event_category === "hook") return "HOOK";

  // Fallback to event category
  return props.event.event_category?.toUpperCase() || "UNKNOWN";
});

const categoryIcon = computed(() => {
  // Icon based on display category
  const category = displayCategory.value;
  if (category === "TOOL") return "🛠️";
  if (category === "RESPONSE") return "💬";
  if (category === "HOOK") return "🪝";
  if (category === "THINKING") return "🧠";
  return "📋";
});

const tokens = computed(() => {
  // Extract tokens from payload
  const payload = props.event.payload;
  return payload?.tokens || payload?.input_tokens || payload?.output_tokens;
});

const agentDisplayName = computed(() => {
  // Use agent_name if available, otherwise show truncated ID
  if (props.event.agent_name) {
    return props.event.agent_name;
  }
  return `Agent-${formatAgentId(props.event.agent_id || "")}`;
});

const displayEventType = computed(() => {
  // Display the specific action/tool name
  const type = props.event.event_type || "";
  const payload = props.event.payload;

  // For tool use events, show the actual tool name
  if (type === "ToolUseBlock" || type === "tool_use") {
    return payload?.tool_name || "TOOL_USE";
  }

  // For other event types, show the type
  if (type === "TextBlock" || type === "text") return "RESPONSE";
  if (type === "ThinkingBlock" || type === "thinking") return "THINKING";
  return type ? type.toUpperCase() : "UNKNOWN";
});

const displayContent = computed(() => {
  const type = props.event.event_type || "";
  const payload = props.event.payload;

  // For RESPONSE events, show the payload text
  if (type === "TextBlock" || type === "text") {
    const text = payload?.text || "—";

    // Truncate to 200 chars if not expanded
    if (!isExpanded.value && text.length > 200) {
      return text.substring(0, 200) + "...";
    }
    return text;
  }

  // For HOOK events, prefer content over summary (summary is truncated)
  if (displayCategory.value === "HOOK") {
    const fullContent = props.event.content || props.event.summary || "—";

    // Truncate to 200 chars if not expanded
    if (!isExpanded.value && fullContent.length > 200) {
      return fullContent.substring(0, 200) + "...";
    }
    return fullContent;
  }

  // For THINKING events, prefer content over summary, fall back to payload.text
  if (displayCategory.value === "THINKING") {
    const thinkingContent =
      props.event.content || props.event.summary || payload?.text || "—";

    // Truncate to 200 chars if not expanded
    if (!isExpanded.value && thinkingContent.length > 200) {
      return thinkingContent.substring(0, 200) + "...";
    }
    return thinkingContent;
  }

  // For other events (tools), show the summary
  return props.event.summary || "—";
});

const formattedContent = computed(() => {
  // Render markdown content with XSS protection
  return renderMarkdown(displayContent.value);
});

// File tracking computed properties - check payload first (from DB), then WebSocket Map
const fileChanges = computed((): FileChange[] => {
  // PRIORITY 1: Check event payload (from database - persists across refreshes)
  if (props.event.payload?.file_changes && Array.isArray(props.event.payload.file_changes)) {
    return props.event.payload.file_changes;
  }

  // PRIORITY 2: Fallback to WebSocket fileTrackingEvents Map (real-time updates)
  const fileTracking = store.fileTrackingEvents.get(props.event.id);
  if (fileTracking && Array.isArray(fileTracking.file_changes)) {
    return fileTracking.file_changes;
  }

  return [];
});

const readFiles = computed((): FileRead[] => {
  // PRIORITY 1: Check event payload (from database - persists across refreshes)
  if (props.event.payload?.read_files && Array.isArray(props.event.payload.read_files)) {
    return props.event.payload.read_files;
  }

  // PRIORITY 2: Fallback to WebSocket fileTrackingEvents Map (real-time updates)
  const fileTracking = store.fileTrackingEvents.get(props.event.id);
  if (fileTracking && Array.isArray(fileTracking.read_files)) {
    return fileTracking.read_files;
  }

  return [];
});

const hasFileActivity = computed((): boolean => {
  return fileChanges.value.length > 0 || readFiles.value.length > 0;
});

function formatAgentId(agentId: string): string {
  // Show last 4 characters of UUID
  return agentId.slice(-4).toUpperCase();
}

function formatTime(timestamp: Date | string): string {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}
</script>

<style scoped>
.agent-log-row {
  display: grid;
  grid-template-columns: 50px 100px 120px 1fr 120px;
  gap: var(--spacing-md);
  align-items: baseline;
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 8px solid; /* Color set via inline style */
  transition: all 0.15s ease;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.875rem;
  cursor: pointer;
}

.agent-log-row:hover {
  opacity: 0.9;
}

.agent-log-row.is-expanded {
  opacity: 0.95;
}

/* Line number */
.event-line-number {
  text-align: right;
  color: var(--text-muted);
  opacity: 0.5;
  font-size: 0.8rem;
}

/* Category badge */
.event-category-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.category-hook {
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.category-response {
  background: rgba(34, 197, 94, 0.15);
  color: var(--status-success);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.category-tool {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
}

.category-thinking {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

/* Agent info */
.event-agent {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-id {
  color: var(--accent-secondary);
  font-weight: 600;
  padding: 2px 6px;
  border: 1.5px solid; /* Color set via inline style */
  border-radius: 4px;
  display: inline-block;
}

/* Content */
.event-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.event-type {
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-summary {
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.event-summary.clickable {
  cursor: pointer;
}

.event-summary.clickable:hover {
  opacity: 0.8;
}

/* Markdown content styles */
.event-summary :deep(p) {
  margin: 0.5em 0;
  line-height: 1.6;
}

.event-summary :deep(p:first-child) {
  margin-top: 0;
}

.event-summary :deep(p:last-child) {
  margin-bottom: 0;
}

.event-summary :deep(strong) {
  font-weight: 700;
}

.event-summary :deep(em) {
  font-style: italic;
}

.event-summary :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.85em;
}

.event-summary :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
}

.event-summary :deep(a:hover) {
  text-decoration: underline;
}

.event-summary :deep(pre) {
  background: rgba(0, 0, 0, 0.2);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1em 0;
  line-height: 1.5;
}

.event-summary :deep(ul),
.event-summary :deep(ol) {
  margin: 0.75em 0;
  padding-left: 20px;
  line-height: 1.6;
}

.event-summary :deep(li) {
  margin: 0.4em 0;
}

.event-summary :deep(h1),
.event-summary :deep(h2),
.event-summary :deep(h3),
.event-summary :deep(h4),
.event-summary :deep(h5),
.event-summary :deep(h6) {
  margin: 1.2em 0 0.6em 0;
  font-weight: 700;
  line-height: 1.3;
}

.event-summary :deep(h1:first-child),
.event-summary :deep(h2:first-child),
.event-summary :deep(h3:first-child),
.event-summary :deep(h4:first-child),
.event-summary :deep(h5:first-child),
.event-summary :deep(h6:first-child) {
  margin-top: 0;
}

.event-summary :deep(h1) {
  font-size: 1.3em;
}

.event-summary :deep(h2) {
  font-size: 1.2em;
}

.event-summary :deep(h3) {
  font-size: 1.1em;
}

.event-summary :deep(h4),
.event-summary :deep(h5),
.event-summary :deep(h6) {
  font-size: 1em;
}

.event-summary :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin: 1em 0;
}

/* Metadata */
.event-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: var(--text-muted);
  font-size: 0.75rem;
}

.event-tokens {
  color: var(--status-warning);
}

.event-time {
  opacity: 0.7;
}

/* Border and background colors set via inline styles based on agent */
/* Removed level-based border colors to allow agent-specific colors */

/* Animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.agent-log-row {
  animation: slideIn 0.2s ease-out;
}

/* File activity badge */
.file-activity-badge {
  margin-top: 4px;
  display: flex;
  gap: 4px;
  font-size: 0.7rem;
}

.modified-count {
  color: var(--accent);
}

.read-count {
  color: var(--status-info);
}

/* File tracking container - integrated inside block */
.file-tracking-container {
  border-left: 8px solid; /* Color set via inline style */
  padding: var(--spacing-md);
  padding-left: 200px;
  padding-top: 40px;
}

.agent-log-row-wrapper {
}
</style>
