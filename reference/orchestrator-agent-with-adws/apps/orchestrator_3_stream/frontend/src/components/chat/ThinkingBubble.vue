<template>
  <div class="thinking-bubble">
    <div class="message-header">
      <span class="message-sender">
        <span class="icon">🤔</span>
        ORCHESTRATOR THINKING
      </span>
      <span class="message-time">{{ formatTime(timestamp) }}</span>
    </div>
    <div class="thinking-content">
      <div
        v-if="isExpanded || thinking.length <= 300"
        class="thinking-text"
        v-html="renderMarkdown(thinking)"
      ></div>
      <div
        v-else
        class="thinking-text"
        v-html="renderMarkdown(thinking.slice(0, 300) + '...')"
      ></div>
      <button
        v-if="thinking.length > 300"
        @click="toggleExpanded"
        class="expand-button"
      >
        {{ isExpanded ? "▲ Show Less" : "▼ Show More" }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { renderMarkdown } from "../../utils/markdown";

interface Props {
  thinking: string;
  timestamp: string | Date;
}

const props = defineProps<Props>();
const isExpanded = ref(false);

function toggleExpanded() {
  isExpanded.value = !isExpanded.value;
}

function formatTime(timestamp: string | Date) {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<style scoped>
.thinking-bubble {
  max-width: 85%;
  padding: var(--spacing-md);
  border-radius: 12px;
  border-bottom-left-radius: 4px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.3);
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
  color: #8b5cf6;
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

.thinking-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.thinking-text {
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", monospace;
  opacity: 0.95;
  font-style: italic;
}

.expand-button {
  align-self: flex-start;
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 6px;
  color: #8b5cf6;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.expand-button:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
}
</style>
