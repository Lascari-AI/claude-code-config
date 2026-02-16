<template>
  <div
    class="event-row system-log-row"
    :class="`event-${event.level.toLowerCase()}`"
  >
    <div class="event-line-number">{{ lineNumber }}</div>

    <div class="event-badge" :class="`badge-${event.level.toLowerCase()}`">
      [{{ event.level }}]
    </div>

    <div class="system-icon">
      <span class="icon">{{ getLevelIcon(event.level) }}</span>
      <span class="label">SYSTEM</span>
    </div>

    <div class="event-source" v-if="event.file_path">
      {{ formatFilePath(event.file_path) }}
    </div>

    <div class="event-content">
      {{ event.message }}
    </div>

    <div class="event-meta">
      <span class="event-time">{{ formatTime(event.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SystemLog } from '../../types'

interface Props {
  event: SystemLog
  lineNumber: number
}

defineProps<Props>()

function getLevelIcon(level: string): string {
  switch (level) {
    case 'DEBUG': return '🔍'
    case 'INFO': return 'ℹ️'
    case 'WARNING': return '⚠️'
    case 'ERROR': return '❌'
    default: return '📝'
  }
}

function formatFilePath(path: string): string {
  // Show only the filename, not full path
  const parts = path.split('/')
  return parts[parts.length - 1]
}

function formatTime(timestamp: Date | string): string {
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
.system-log-row {
  display: grid;
  grid-template-columns: 50px 80px 100px 150px 1fr 180px;
  gap: var(--spacing-md);
  align-items: baseline;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-left: 3px solid transparent;
  transition: all 0.15s ease;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

.system-log-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* Line number */
.event-line-number {
  text-align: right;
  color: var(--text-muted);
  opacity: 0.5;
  font-size: 0.8rem;
}

/* Level badges */
.event-badge {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.badge-debug { color: var(--status-debug); }
.badge-info { color: var(--status-info); }
.badge-warning { color: var(--status-warning); }
.badge-error { color: var(--status-error); }

/* System indicator */
.system-icon {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(147, 51, 234, 0.15);
  color: #a855f7;
  border: 1px solid rgba(147, 51, 234, 0.3);
}

.icon {
  font-size: 1rem;
}

/* Source file */
.event-source {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-style: italic;
  opacity: 0.8;
}

/* Content */
.event-content {
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Metadata */
.event-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-align: right;
}

.event-time {
  opacity: 0.7;
  white-space: nowrap;
}

/* Border colors by level */
.event-debug {
  border-left-color: var(--status-debug);
}

.event-info {
  border-left-color: var(--status-info);
}

.event-warning {
  border-left-color: var(--status-warning);
  background: rgba(245, 158, 11, 0.03);
}

.event-error {
  border-left-color: var(--status-error);
  background: rgba(239, 68, 68, 0.05);
}

/* Animations */
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

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.system-log-row {
  animation: slideIn 0.2s ease-out;
}
</style>
