<template>
  <div class="agent-list" :class="{ collapsed: isCollapsed }">
    <div class="agent-list-header">
      <h3>AGENTS</h3>
      <div class="header-right">
        <div class="total-count">{{ agents.length }} Total</div>
        <button
          class="collapse-btn"
          @click="toggleCollapse"
          :title="isCollapsed ? 'Expand' : 'Collapse'"
        >
          <span class="collapse-icon">{{ isCollapsed ? "›" : "‹" }}</span>
        </button>
      </div>
    </div>

    <!-- Compact Agent View (when collapsed) -->
    <div class="compact-agent-list" v-show="isCollapsed">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="compact-agent-item"
        :class="{
          active: agent.id === selectedAgentId,
          'agent-pulsing': store.isAgentPulsing(agent.id)
        }"
        :style="store.isAgentPulsing(agent.id) ? {
          borderColor: getAgentColor(agent),
          '--pulse-color': getPulseColorValue(agent)
        } : { borderColor: getAgentColor(agent) }"
        @click="onSelectAgent(agent.id)"
        :title="agent.name"
      >
        <span
          class="compact-agent-dot"
          :class="getStatusClass(agent.status)"
        ></span>
        <span class="compact-agent-letter">{{
          getFirstLetter(agent.name)
        }}</span>
      </div>
    </div>

    <div class="agent-list-content" v-show="!isCollapsed">
      <!-- Agent Items -->
      <div class="agent-items">
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="agent-card"
          :class="{
            active: agent.id === selectedAgentId,
            'agent-pulsing': store.isAgentPulsing(agent.id)
          }"
          :style="store.isAgentPulsing(agent.id) ? {
            '--pulse-color': getPulseColorValue(agent)
          } : {}"
          @click="onSelectAgent(agent.id)"
        >
          <div class="agent-card-header">
            <div class="agent-name-row">
              <span
                class="agent-name"
                :style="{ borderColor: getAgentColor(agent) }"
                >{{ agent.name }}</span
              >
            </div>
            <div
              class="agent-status-badge"
              :class="getStatusClass(agent.status)"
            >
              {{ getStatusLabel(agent.status) }}
            </div>
          </div>

          <!-- Template Badge -->
          <div v-if="agent.metadata?.template_name" class="template-badge">
            <span class="template-icon">📋</span>
            <span class="template-text"
              >Template: {{ agent.metadata.template_name }}</span
            >
          </div>

          <div class="agent-task">{{ getTaskDescription(agent) }}</div>

          <!-- Context Window -->
          <div class="context-window">
            <div class="context-header">
              <span class="context-label">Context Window</span>
              <span class="context-values"
                >{{ formatTokens(getTotalTokens(agent)) }} / 200k</span
              >
            </div>
            <div class="context-bar-container">
              <div
                class="context-bar-fill"
                :style="{ width: getContextPercentage(agent) + '%' }"
              ></div>
            </div>
          </div>

          <!-- Log Counters Row -->
          <div class="agent-log-counters">
            <div
              class="log-counter counter-response"
              :title="`${getAgentLogCount(agent, 'RESPONSE')} responses`"
            >
              <span class="counter-emoji">💬</span>
              <span class="counter-value">{{
                getAgentLogCount(agent, "RESPONSE")
              }}</span>
            </div>
            <div
              class="log-counter counter-tool"
              :title="`${getAgentLogCount(agent, 'TOOL')} tools`"
            >
              <span class="counter-emoji">🛠️</span>
              <span class="counter-value">{{
                getAgentLogCount(agent, "TOOL")
              }}</span>
            </div>
            <div
              class="log-counter counter-hook"
              :title="`${getAgentLogCount(agent, 'HOOK')} hooks`"
            >
              <span class="counter-emoji">🪝</span>
              <span class="counter-value">{{
                getAgentLogCount(agent, "HOOK")
              }}</span>
            </div>
            <div
              class="log-counter counter-thinking"
              :title="`${getAgentLogCount(agent, 'THINKING')} thinking`"
            >
              <span class="counter-emoji">🧠</span>
              <span class="counter-value">{{
                getAgentLogCount(agent, "THINKING")
              }}</span>
            </div>
          </div>

          <!-- Model & Cost Row -->
          <div class="agent-card-footer">
            <div class="agent-model">{{ formatModel(agent.model) }}</div>
            <div class="agent-cost">${{ agent.total_cost.toFixed(3) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useOrchestratorStore } from "../stores/orchestratorStore";
import { getAgentBorderColor as getAgentBorderColorUtil, getAgentBackgroundColor } from "../utils/agentColors";
import type { Agent } from "../types";

// Store
const store = useOrchestratorStore();

// Props
const props = defineProps<{
  agents: Agent[];
  selectedAgentId?: string | null;
}>();

// Emits
const emit = defineEmits<{
  selectAgent: [id: string];
  collapseChange: [isCollapsed: boolean];
}>();

// Computed
const agents = computed(() => props.agents);

// Collapse state
const isCollapsed = ref(false);

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
  emit("collapseChange", isCollapsed.value);
};

// Methods
const onSelectAgent = (id: string) => {
  emit("selectAgent", id);
};

const formatModel = (model: string): string => {
  if (model.includes("sonnet")) {
    return "sonnet-4.5";
  } else if (model.includes("opus")) {
    return "opus-4.5";
  } else if (model.includes("haiku")) {
    return "haiku-4.5";
  }
  return model;
};

const getTaskDescription = (agent: Agent): string => {
  // Priority order for task description:
  // 1. adw_step (current workflow step)
  // 2. task (explicitly set task description)
  // 3. latest_summary (latest log summary from backend)
  // 4. status-based description

  if (agent.adw_step) {
    return `STEP: ${agent.adw_step}`;
  }

  if (agent.task) {
    return agent.task;
  }

  // Use latest log summary if available
  if (agent.latest_summary) {
    return agent.latest_summary;
  }

  // Status-based descriptions (fallback)
  switch (agent.status) {
    case "executing":
      return "Processing task...";
    case "waiting":
      return "Waiting for dependencies";
    case "blocked":
      return "Blocked - needs attention";
    case "complete":
      return "Task completed";
    case "idle":
    default:
      return "Ready for tasks";
  }
};

const getStatusClass = (status: string | null): string => {
  // Map status to dot color classes
  switch (status) {
    case "executing":
      return "status-executing";
    case "waiting":
      return "status-waiting";
    case "blocked":
      return "status-blocked";
    case "complete":
      return "status-complete";
    case "idle":
    default:
      return "status-idle";
  }
};

const getStatusLabel = (status: string | null): string => {
  // Map status to uppercase labels
  switch (status) {
    case "executing":
      return "EXECUTING";
    case "waiting":
      return "WAITING";
    case "blocked":
      return "BLOCKED";
    case "complete":
      return "COMPLETE";
    case "idle":
    default:
      return "IDLE";
  }
};

// Context window calculations
const MAX_TOKENS = 200000; // 200k tokens

const getTotalTokens = (agent: Agent): number => {
  return agent.input_tokens + agent.output_tokens;
};

const formatTokens = (tokens: number): string => {
  if (tokens >= 1000) {
    return Math.round(tokens / 1000) + "k";
  }
  return tokens.toString();
};

const getContextPercentage = (agent: Agent): number => {
  const total = getTotalTokens(agent);
  return Math.min((total / MAX_TOKENS) * 100, 100);
};

const getFirstLetter = (name: string): string => {
  return name.charAt(0).toUpperCase();
};

// Log counters by category
const getAgentLogCount = (
  agent: Agent,
  category: "RESPONSE" | "TOOL" | "HOOK" | "THINKING"
): number => {
  const events = store.eventStreamEntries.filter(
    (event) => event.agentId === agent.id
  );

  switch (category) {
    case "RESPONSE":
      return events.filter((e) => {
        const type = e.eventType?.toLowerCase();
        return type === "text" || type === "textblock";
      }).length;

    case "TOOL":
      return events.filter((e) => {
        const type = e.eventType?.toLowerCase();
        return type === "tool_use" || type === "tooluseblock";
      }).length;

    case "HOOK":
      return events.filter((e) => e.eventCategory === "hook").length;

    case "THINKING":
      return events.filter((e) => {
        const type = e.eventType?.toLowerCase();
        return type === "thinking" || type === "thinkingblock";
      }).length;

    default:
      return 0;
  }
};

// Agent color generation - uses shared utility with memoization
const agentColorsMap = computed(() => {
  const map = new Map<string, string>();
  agents.value.forEach((agent) => {
    const color = getAgentBorderColorUtil(agent.name, agent.id);
    map.set(agent.id, color);
  });
  return map;
});

const getAgentColor = (agent: Agent): string => {
  return agentColorsMap.value.get(agent.id) || "#6b7280";
};

/**
 * Extract RGB values from rgba color string for pulse animation
 * Converts rgba(r, g, b, a) to rgb(r, g, b) for use in animations
 */
const getPulseColorValue = (agent: Agent): string => {
  const fullColor = getAgentColor(agent);
  // Extract RGB values from rgba(r, g, b, a)
  const match = fullColor.match(/\d+/g);
  if (match && match.length >= 3) {
    return `${match[0]}, ${match[1]}, ${match[2]}`;
  }
  // Fallback to a neutral gray
  return "107, 114, 128";
};
</script>

<style scoped>
.agent-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1c1f2e;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.agent-list.collapsed {
  width: 48px !important;
  min-width: 48px !important;
}

.agent-list.collapsed h3,
.agent-list.collapsed .total-count {
  display: none;
}

.agent-list.collapsed .agent-list-header {
  justify-content: center;
  padding: 1rem 0.5rem;
}

/* Header */
.agent-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: #0d0f1a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.agent-list-header h3 {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #6b7280;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.total-count {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.collapse-icon {
  font-size: 1.25rem;
  color: #9ca3af;
  line-height: 1;
  font-weight: 600;
}

/* Compact Agent List */
.compact-agent-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 0.5rem;
  overflow-y: auto;
}

.compact-agent-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  background: #0d0f1a;
  border: 1.5px solid;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.compact-agent-item:hover {
  background: #13152a;
  transform: scale(1.05);
}

.compact-agent-item.active {
  background: #13152a;
  box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.5);
}

.compact-agent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  flex-shrink: 0;
  margin-bottom: 0.25rem;
}

.compact-agent-letter {
  font-size: 0.875rem;
  font-weight: 700;
  color: #e5e7eb;
}

/* Content */
.agent-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

/* All Agents Button */
.all-agents-btn {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  margin-bottom: 0.75rem;
  transition: all 0.2s ease;
}

.all-agents-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.all-agents-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.all-agents-subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 400;
}

/* Agent Items */
.agent-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.agent-card {
  background: #0d0f1a;
  border-radius: 6px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.agent-card:hover {
  background: #13152a;
  transform: translateY(-1px);
}

.agent-card.active {
  background: #13152a;
  box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.5);
}

/* Card Header */
.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.375rem;
}

.agent-name-row {
  display: flex;
  align-items: center;
}

.agent-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #e5e7eb;
  padding: 2px 6px;
  border: 1.5px solid;
  border-radius: 4px;
  display: inline-block;
}

.agent-status-badge {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.agent-status-badge.status-idle {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

.agent-status-badge.status-executing {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.agent-status-badge.status-waiting {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.agent-status-badge.status-blocked {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.agent-status-badge.status-complete {
  background: rgba(107, 114, 128, 0.2);
  color: #6b7280;
  border: 1px solid rgba(107, 114, 128, 0.4);
}

.agent-model {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(107, 114, 128, 0.2);
  color: #9ca3af;
  border: 1px solid rgba(107, 114, 128, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Template Badge */
.template-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  color: #9ca3af;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 2px 6px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 3px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  width: fill-available;
}

.template-icon {
  font-size: 0.75rem;
  line-height: 1;
}

.template-text {
  font-weight: 500;
  font-style: italic;
}

/* Card Task */
.agent-task {
  font-size: 0.8125rem;
  color: #9ca3af;
  line-height: 1.4;
  margin-bottom: 0.5rem;
  min-height: 1.8em;
}

/* Context Window */
.context-window {
  margin-bottom: 0.625rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.375rem;
}

.context-label {
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #6b7280;
  text-transform: uppercase;
}

.context-values {
  color: #e5e7eb;
  font-weight: 600;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.context-bar-container {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.context-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Card Footer */
.agent-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

/* Log Counters */
.agent-log-counters {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-bottom: 0.5rem;
}

.log-counter {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid transparent;
  flex: 1;
  justify-content: center;
}

.counter-emoji {
  font-size: 0.875rem;
  line-height: 1;
}

.counter-value {
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.counter-response {
  background: rgba(34, 197, 94, 0.1);
  color: var(--status-success);
  border-color: rgba(34, 197, 94, 0.2);
}

.counter-tool {
  background: rgba(251, 146, 60, 0.1);
  color: #fb923c;
  border-color: rgba(251, 146, 60, 0.2);
}

.counter-hook {
  background: rgba(6, 182, 212, 0.1);
  color: var(--accent);
  border-color: rgba(6, 182, 212, 0.2);
}

.counter-thinking {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
  border-color: rgba(168, 85, 247, 0.2);
}

.agent-cost {
  color: #e5e7eb;
  font-weight: 600;
  font-size: 0.75rem;
}

/* Scrollbar */
.agent-list-content::-webkit-scrollbar {
  width: 6px;
}

.agent-list-content::-webkit-scrollbar-track {
  background: transparent;
}

.agent-list-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.agent-list-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* ═════════════════════════════════════════════════════════════ */
/* PULSE ANIMATION - Optimized for Production Use               */
/* Performance: Uses only GPU-accelerated properties (background) */
/* Can handle 1000s of simultaneous pulses without lag          */
/* ═════════════════════════════════════════════════════════════ */

/* Simple background color fade animation - most efficient */
@keyframes agentPulseBackground {
  0% {
    background: #0d0f1a;  /* Original deep blue - card background */
  }
  50% {
    background: rgba(var(--pulse-color), 0.15);  /* Subtle color brightening */
  }
  100% {
    background: #0d0f1a;  /* Back to original deep blue */
  }
}

/* Compact view - minimal inset shadow for visual feedback */
@keyframes compactAgentPulseBg {
  0% {
    box-shadow: inset 0 0 0 1px rgba(var(--pulse-color), 0);
  }
  50% {
    box-shadow: inset 0 0 6px 1px rgba(var(--pulse-color), 0.25);
  }
  100% {
    box-shadow: inset 0 0 0 1px rgba(var(--pulse-color), 0);
  }
}

/* Agent card pulse - expanded sidebar view (335ms for snappy feel) */
.agent-card.agent-pulsing {
  animation: agentPulseBackground 0.335s ease-out forwards;
}

/* Compact agent pulse - collapsed sidebar view (335ms for snappy feel) */
.compact-agent-item.agent-pulsing {
  animation: compactAgentPulseBg 0.335s ease-out forwards;
}

/* ═══════════════════════════════════════════════════════════
   MOBILE RESPONSIVE DESIGN (< 650px)
   ═══════════════════════════════════════════════════════════ */

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

  /* Touch feedback for mobile */
  .compact-agent-item:active {
    transform: scale(0.95);
    background: #13152a;
  }
}
</style>
