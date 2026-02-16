<template>
  <div class="tool-use-bubble">
    <div class="message-header">
      <span class="message-sender">
        <span class="icon">🔧</span>
        ORCHESTRATOR ACTION
      </span>
      <span class="message-time">{{ formatTime(timestamp) }}</span>
    </div>
    <div class="tool-content">
      <div class="tool-name-section">
        <span class="tool-label">Tool:</span>
        <code class="tool-name">{{ simplifiedToolName }}</code>
      </div>

      <div v-if="hasInput" class="tool-params-section">
        <div class="tool-label">Parameters:</div>
        <div class="tool-params">
          <div v-if="isExpanded || inputString.length <= 200" class="params-display">
            <pre>{{ formattedInput }}</pre>
          </div>
          <div v-else class="params-display">
            <pre>{{ formattedInput.slice(0, 200) }}...</pre>
          </div>
          <button
            v-if="inputString.length > 200"
            @click="toggleExpanded"
            class="expand-button"
          >
            {{ isExpanded ? '▲ Show Less' : '▼ Show More' }}
          </button>
        </div>
      </div>
      <div v-else class="no-params">
        (No parameters)
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  toolName: string
  toolInput: Record<string, any> | null
  timestamp: string | Date
}

const props = defineProps<Props>()
const isExpanded = ref(false)

const simplifiedToolName = computed(() => {
  // Strip mcp__mgmt__ prefix for display
  return props.toolName.replace('mcp__mgmt__', '')
})

const hasInput = computed(() => {
  return props.toolInput && Object.keys(props.toolInput).length > 0
})

const formattedInput = computed(() => {
  if (!hasInput.value) return ''
  return JSON.stringify(props.toolInput, null, 2)
})

const inputString = computed(() => {
  return formattedInput.value
})

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}

function formatTime(timestamp: string | Date) {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.tool-use-bubble {
  max-width: 85%;
  padding: var(--spacing-md);
  border-radius: 12px;
  border-bottom-left-radius: 4px;
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.3);
  word-wrap: break-word;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  gap: var(--spacing-md);
}

.message-sender {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #eab308;
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon {
  font-size: 0.9rem;
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.tool-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tool-name-section {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.tool-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}

.tool-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #eab308;
  background: rgba(234, 179, 8, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.tool-params-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tool-params {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.params-display {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: 6px;
  padding: var(--spacing-sm);
}

.params-display pre {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.no-params {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-style: italic;
}

.expand-button {
  align-self: flex-start;
  padding: 4px 12px;
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: 6px;
  color: #eab308;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.expand-button:hover {
  background: rgba(234, 179, 8, 0.25);
  border-color: rgba(234, 179, 8, 0.5);
}
</style>
