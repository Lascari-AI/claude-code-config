<template>
  <div
    class="event-row orchestrator-chat-row"
    :class="[
      `sender-${event.sender_type}`,
      `category-${displayCategory.toLowerCase()}`
    ]"
  >
    <div class="event-line-number">{{ lineNumber }}</div>

    <div class="communication-badge" :class="`category-${displayCategory.toLowerCase()}`">
      <span class="icon">{{ categoryIcon }}</span>
      {{ displayCategory }}
    </div>

    <div class="communication-flow">
      <span class="sender" :class="`type-${event.sender_type}`">
        {{ formatParticipant(event.sender_type) }}
      </span>
      <span class="arrow">→</span>
      <span class="receiver" :class="`type-${event.receiver_type}`">
        {{ formatParticipant(event.receiver_type) }}
      </span>
    </div>

    <div class="event-content">
      <div class="event-type" v-if="displayEventType">{{ displayEventType }}</div>
      <div
        class="message-bubble"
        :class="`from-${event.sender_type}`"
        v-html="formattedMessage"
      ></div>
    </div>

    <div class="event-meta">
      <span class="event-time">{{ formatTime(event.created_at || event.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { OrchestratorChat } from '../../types'
import { renderMarkdown } from '../../utils/markdown'

interface Props {
  event: OrchestratorChat | any // Accept both database and WebSocket formats
  lineNumber: number
}

const props = defineProps<Props>()

const displayCategory = computed(() => {
  // Determine category based on metadata type
  const metadata = props.event.metadata || {}
  const metadataType = metadata.type

  // Check metadata type field for specific event types
  if (metadataType === 'tool_use' || metadataType === 'tool_block') return 'TOOL'
  if (metadataType === 'thinking' || metadataType === 'thinking_block') return 'THINKING'

  // Default to CHAT for normal communication
  return 'CHAT'
})

const categoryIcon = computed(() => {
  const category = displayCategory.value
  if (category === 'TOOL') return '🛠️'
  if (category === 'THINKING') return '🧠'
  return '💬'
})

const displayEventType = computed(() => {
  const metadata = props.event.metadata || {}

  // For tool events, show tool name
  if (displayCategory.value === 'TOOL') {
    return metadata.tool_name ? `Tool: ${metadata.tool_name}` : 'TOOL USE'
  }

  // For thinking events
  if (displayCategory.value === 'THINKING') {
    return 'THINKING'
  }

  // No type label for normal chat
  return ''
})

const formattedMessage = computed(() => {
  // Render message markdown with XSS protection
  return renderMarkdown(props.event.message || '')
})

function formatParticipant(type: 'user' | 'orchestrator' | 'agent'): string {
  switch (type) {
    case 'user':
      return '👤 User'
    case 'orchestrator':
      return '🤖 Orchestrator'
    case 'agent':
      return '⚙️ Agent'
    default:
      return type
  }
}

function formatAgentId(agentId: string): string {
  return agentId.slice(-4).toUpperCase()
}

function formatTime(timestamp: Date | string | null | undefined): string {
  if (!timestamp) {
    return new Date().toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}
</script>

<style scoped>
.orchestrator-chat-row {
  display: grid;
  grid-template-columns: 50px 100px 220px 1fr 100px;
  gap: var(--spacing-md);
  align-items: start;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-left: 3px solid #d946ef; /* Magenta/pink for communication */
  transition: all 0.15s ease;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

.orchestrator-chat-row:hover {
  background: rgba(217, 70, 239, 0.05);
}

/* Border colors by category */
.category-tool {
  border-left-color: #fb923c;
}

.category-thinking {
  border-left-color: #a855f7;
}

/* Line number */
.event-line-number {
  text-align: right;
  color: var(--text-muted);
  opacity: 0.5;
  font-size: 0.8rem;
  padding-top: 2px;
}

/* Communication badge with category-specific colors */
.communication-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

/* Default CHAT badge */
.communication-badge.category-chat {
  background: rgba(217, 70, 239, 0.15);
  color: #d946ef;
  border: 1px solid rgba(217, 70, 239, 0.3);
}

/* TOOL badge */
.communication-badge.category-tool {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
}

/* THINKING badge */
.communication-badge.category-thinking {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.icon {
  font-size: 1rem;
}

/* Communication flow visualization */
.communication-flow {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 0.75rem;
  font-weight: 600;
  padding-top: 2px;
}

.sender,
.receiver {
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.type-user {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.type-orchestrator {
  background: rgba(217, 70, 239, 0.15);
  color: #d946ef;
}

.type-agent {
  background: rgba(6, 182, 212, 0.15);
  color: #06b6d4;
}

.arrow {
  color: var(--text-muted);
  font-weight: normal;
}

/* Message content */
.event-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-type {
  color: var(--text-secondary);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.message-bubble {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.5;
}

/* Border accents by sender */
.from-user {
  border-left: 3px solid #3b82f6;
}

.from-orchestrator {
  border-left: 3px solid #d946ef;
}

.from-agent {
  border-left: 3px solid #06b6d4;
}

/* Markdown content styles in message bubble */
.message-bubble :deep(p) {
  margin: 0;
}

.message-bubble :deep(p:not(:last-child)) {
  margin-bottom: 0.5em;
}

.message-bubble :deep(strong) {
  font-weight: 700;
}

.message-bubble :deep(em) {
  font-style: italic;
}

.message-bubble :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
}

.message-bubble :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
}

.message-bubble :deep(a:hover) {
  text-decoration: underline;
}

.message-bubble :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5em 0;
  font-family: 'JetBrains Mono', monospace;
}

.message-bubble :deep(ul),
.message-bubble :deep(ol) {
  margin: 0.5em 0;
  padding-left: 20px;
}

.message-bubble :deep(li) {
  margin: 0.25em 0;
}

.message-bubble :deep(h1),
.message-bubble :deep(h2),
.message-bubble :deep(h3),
.message-bubble :deep(h4),
.message-bubble :deep(h5),
.message-bubble :deep(h6) {
  margin: 0.5em 0 0.25em 0;
  font-weight: 700;
}

.message-bubble :deep(h1) {
  font-size: 1.2em;
}
.message-bubble :deep(h2) {
  font-size: 1.1em;
}
.message-bubble :deep(h3) {
  font-size: 1em;
}

/* Metadata */
.event-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-align: right;
  padding-top: 2px;
}

.event-time {
  opacity: 0.7;
  white-space: nowrap;
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

.orchestrator-chat-row {
  animation: slideIn 0.2s ease-out;
}
</style>
