<template>
  <div
    class="event-row agent-tool-use-block-row"
    :style="{
      borderLeftColor: agentColor,
      backgroundColor: agentBackgroundColor,
    }"
  >
    <div class="event-line-number">{{ lineNumber }}</div>

    <div class="tool-badge">
      <span class="icon">🔧</span>
      TOOL
    </div>

    <div class="tool-header">
      <span class="agent-label" :style="{ borderColor: agentColor }">{{
        agentDisplayName
      }}</span>
      <span class="tool-name">{{ simplifiedToolName }}</span>
    </div>

    <div class="event-content">
      <div class="tool-content">
        <div class="tool-info">
          <span class="tool-label">Tool:</span>
          <code class="tool-value">{{ toolName }}</code>
        </div>

        <div v-if="hasInput" class="tool-input-section">
          <div class="tool-label">Parameters:</div>
          <div
            v-if="isExpanded || inputString.length <= 150"
            class="tool-input"
          >
            <pre>{{ formattedInput }}</pre>
          </div>
          <div v-else class="tool-input">
            <pre>{{ formattedInput.slice(0, 150) }}...</pre>
          </div>
          <button
            v-if="inputString.length > 150"
            @click="toggleExpanded"
            class="expand-button"
          >
            {{ isExpanded ? "Show Less" : "Show More" }}
          </button>
        </div>
        <div v-else class="no-params">No parameters</div>
      </div>
    </div>

    <div class="event-meta">
      <span class="event-time">{{ formatTime(event.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { AgentLog } from "../../types";
import {
  getAgentBorderColor,
  getAgentBackgroundColor,
} from "../../utils/agentColors";

interface Props {
  event: AgentLog;
  lineNumber: number;
}

const props = defineProps<Props>();
const isExpanded = ref(false);

// Generate agent-specific colors using shared utility
const agentColor = computed(() =>
  getAgentBorderColor(props.event.agent_name, props.event.agent_id)
);

const agentBackgroundColor = computed(() =>
  getAgentBackgroundColor(props.event.agent_name, props.event.agent_id)
);

const agentDisplayName = computed(() => {
  if (props.event.agent_name) {
    return props.event.agent_name;
  }
  return `Agent-${formatAgentId(props.event.agent_id || "")}`;
});

const toolName = computed(() => {
  return props.event.payload?.tool_name || "Unknown Tool";
});

const simplifiedToolName = computed(() => {
  // Strip common prefixes for display
  const name = toolName.value;
  return name.replace("mcp__mgmt__", "").replace("mcp__", "");
});

const hasInput = computed(() => {
  const input = props.event.payload?.tool_input;
  return input && typeof input === "object" && Object.keys(input).length > 0;
});

const formattedInput = computed(() => {
  if (!hasInput.value) return "";
  try {
    return JSON.stringify(props.event.payload?.tool_input, null, 2);
  } catch (error) {
    console.error("[AgentToolUseBlockRow] Error formatting input:", error);
    return String(props.event.payload?.tool_input || "");
  }
});

const inputString = computed(() => {
  return formattedInput.value;
});

function toggleExpanded() {
  isExpanded.value = !isExpanded.value;
}

function formatAgentId(agentId: string): string {
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
.agent-tool-use-block-row {
  display: grid;
  grid-template-columns: 50px 100px 120px 1fr 180px;
  gap: var(--spacing-md);
  align-items: start;
  padding: var(--spacing-md);
  border-left: 8px solid; /* Color set via inline style */
  transition: all 0.15s ease;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.875rem;
}

.agent-tool-use-block-row:hover {
  opacity: 0.9;
}

/* Line number */
.event-line-number {
  text-align: right;
  color: var(--text-muted);
  opacity: 0.5;
  font-size: 0.8rem;
  padding-top: 4px;
}

/* Tool badge */
.tool-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
  height: fit-content;
}

.icon {
  font-size: 1rem;
}

/* Header */
.tool-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.75rem;
}

.agent-label {
  font-weight: 600;
  color: var(--accent-secondary);
  padding: 2px 6px;
  border: 1.5px solid; /* Color set via inline style */
  border-radius: 4px;
  width: 100%;
  font-size: 0.7rem;
}

.tool-name {
  color: #fb923c;
  font-weight: 600;
  font-family: "JetBrains Mono", monospace;
}

/* Content */
.event-content {
  min-width: 0;
}

.tool-content {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: 8px;
  background: rgba(251, 146, 60, 0.05);
  border: 1px solid rgba(251, 146, 60, 0.2);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tool-info {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.tool-label {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
}

.tool-value {
  color: #fb923c;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(251, 146, 60, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.tool-input-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tool-input {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  padding: var(--spacing-sm);
  border: 1px solid rgba(251, 146, 60, 0.2);
}

.tool-input pre {
  margin: 0;
  color: var(--text-primary);
  font-family: "JetBrains Mono", monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.no-params {
  color: var(--text-muted);
  font-style: italic;
  font-size: 0.8rem;
}

.expand-button {
  margin-top: 4px;
  padding: 4px 12px;
  background: rgba(251, 146, 60, 0.15);
  border: 1px solid rgba(251, 146, 60, 0.3);
  border-radius: 4px;
  color: #fb923c;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  align-self: flex-start;
}

.expand-button:hover {
  background: rgba(251, 146, 60, 0.25);
  border-color: rgba(251, 146, 60, 0.5);
}

/* Metadata */
.event-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding-top: 4px;
}

.event-time {
  opacity: 0.7;
}

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

.agent-tool-use-block-row {
  animation: slideIn 0.2s ease-out;
}
</style>
