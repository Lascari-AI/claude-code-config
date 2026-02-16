<template>
  <div class="filter-controls">
    <!-- Left side: All filters -->
    <div class="filter-left">
      <!-- Category Filters (TOOL, RESPONSE, THINKING) -->
      <div class="category-filters">
        <button
          v-for="filter in categoryFilters"
          :key="filter.value"
          class="quick-filter-btn"
          :class="[filter.class, { active: categoryFilterActive(filter.value) }]"
          @click="toggleCategoryFilter(filter.value)"
          :title="`Filter by ${filter.label}`"
        >
          <span class="filter-emoji">{{ getCategoryEmoji(filter.value) }}</span>
          {{ filter.label }}
        </button>
      </div>

      <!-- Active Agent Filters (prominent display) -->
      <div v-if="activeAgentFilters && activeAgentFilters.size > 0" class="active-agent-filters">
        <button
          v-for="agentName in Array.from(activeAgentFilters)"
          :key="agentName"
          class="active-agent-filter-btn"
          :style="{ borderColor: getAgentBorderColorForName(agentName) }"
          @click="toggleAgentFilter(agentName)"
          :title="`Click to clear filter for ${agentName}`"
        >
          <span class="filter-prefix">AGENTS:</span>
          <span class="filter-name">{{ agentName }}</span>
          <span class="filter-remove">✕</span>
        </button>
      </div>
    </div>

    <!-- Right side: Search and Controls -->
    <div class="filter-right">
      <!-- Search Input -->
      <input
        :value="searchQuery"
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        type="text"
        placeholder="Search agents, events, tasks, files (regex)"
        class="search-input"
        title="Search across: agent name, content, event type, summary, task ID, session ID, file paths"
      />

      <!-- Clear All Button -->
      <button
        class="control-btn clear-all"
        @click="$emit('clear-all')"
        title="Clear all events from the stream"
      >
        Clear All
      </button>

      <!-- Auto-Follow Button -->
      <button
        class="control-btn auto-follow"
        :class="{ active: autoScroll }"
        @click="toggleAutoScroll"
        title="Auto-scroll to bottom when new events arrive"
      >
        Auto-Follow
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import type { FilterTab, QuickFilter, AgentFilter } from '../composables/useEventStreamFilter'
import { useOrchestratorStore } from '../stores/orchestratorStore'
import { getAgentBorderColor } from '../utils/agentColors'

interface Props {
  categoryFilters: QuickFilter[]
  agentFilters: AgentFilter[]
  searchQuery: string
  autoScroll: boolean
  activeAgentFilters?: Set<string>
  activeCategoryFilters?: Set<string>
}

interface Emits {
  'update:searchQuery': [value: string]
  'update:autoScroll': [value: boolean]
  'agent-filter-toggle': [value: string]
  'category-filter-toggle': [value: string]
  'auto-scroll-toggle': []
  'clear-all': []
}

const props = withDefaults(defineProps<Props>(), {
  activeAgentFilters: () => new Set(),
  activeCategoryFilters: () => new Set()
})
const emit = defineEmits<Emits>()

// Store access for agent data
const store = useOrchestratorStore()

// Get agent border color by agent name
const getAgentBorderColorForName = (agentName: string): string => {
  // Find agent in store by name
  const agent = store.agents.find(a => a.name === agentName)

  if (agent) {
    // Use agent ID and name for consistent color
    return getAgentBorderColor(agent.name, agent.id)
  }

  // Fallback: use name as both parameters if agent not found in store
  return getAgentBorderColor(agentName, agentName)
}

const agentFilterActive = (value: string): boolean => {
  return props.activeAgentFilters?.has(value) ?? false
}

const categoryFilterActive = (value: string): boolean => {
  return props.activeCategoryFilters?.has(value) ?? false
}

const toggleAgentFilter = (value: string) => {
  emit('agent-filter-toggle', value)
}

const toggleCategoryFilter = (value: string) => {
  emit('category-filter-toggle', value)
}

const toggleAutoScroll = () => {
  emit('update:autoScroll', !props.autoScroll)
  emit('auto-scroll-toggle')
}

const getCategoryEmoji = (category: string): string => {
  const emojiMap: Record<string, string> = {
    'TOOL': '🛠️',
    'RESPONSE': '💬',
    'THINKING': '🧠',
    'HOOK': '🪝'
  }
  return emojiMap[category] || '📋'
}
</script>

<style scoped>
/* Filter Controls Container */
.filter-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  gap: var(--spacing-md);
}

/* Left side container */
.filter-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
  flex-wrap: wrap;
}

/* Filter Right Side */
.filter-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

/* Search Input */
.search-input {
  width: 250px;
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.search-input:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.1);
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted);
  font-size: 0.8125rem;
}

/* Category Filters */
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

/* Filter Emoji */
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
  color: var(--accent);
  border-color: rgba(6, 182, 212, 0.3);
}

.qf-hook.active {
  background: var(--accent);
  color: white;
}

/* Active Agent Filters (prominent display) */
.active-agent-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.active-agent-filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0.375rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 4px;
  border: 2px solid;
  /* Border color set dynamically via :style binding */
  cursor: pointer;
  transition: all 0.2s ease;
  background: #0d0f1a;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.active-agent-filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
  background: #13152a;
  filter: brightness(1.05);
}

.filter-prefix {
  font-size: 0.7rem;
  opacity: 0.7;
  font-weight: 600;
  color: #9ca3af;
}

.filter-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: #e5e7eb;
}

.filter-remove {
  font-size: 0.875rem;
  opacity: 0.6;
  margin-left: 2px;
  color: #9ca3af;
}

.active-agent-filter-btn:hover .filter-remove {
  opacity: 0.9;
  color: #d1d5db;
}

/* Auto-Follow Button */
.control-btn {
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

.control-btn.auto-follow {
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent-primary);
  border-color: rgba(6, 182, 212, 0.3);
}

.control-btn.auto-follow:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.control-btn.auto-follow.active {
  background: var(--accent-primary);
  color: white;
}

/* Clear All Button */
.control-btn.clear-all {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.control-btn.clear-all:hover {
  background: #ef4444;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
</style>
