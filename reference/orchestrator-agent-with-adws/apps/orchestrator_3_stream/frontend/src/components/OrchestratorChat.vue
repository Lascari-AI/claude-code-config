<template>
  <div class="orchestrator-chat">
    <div class="chat-header">
      <!-- Left section: toggle button and title -->
      <div class="header-left">
        <button
          class="width-toggle-btn"
          @click="handleToggleWidth"
          :title="`Chat width: ${currentWidthLabel}`"
        >
          <svg
            class="width-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <!-- Icon for width toggle -->
            <path
              v-if="chatWidth === 'sm'"
              d="M8 7h8m-8 5h8m-8 5h6"
              stroke-width="2"
              stroke-linecap="round"
            />
            <path
              v-else-if="chatWidth === 'md'"
              d="M4 7h16m-16 5h16m-16 5h12"
              stroke-width="2"
              stroke-linecap="round"
            />
            <path
              v-else
              d="M3 7h18m-18 5h18m-18 5h18"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>
        <h3>O-Agent</h3>
      </div>

      <!-- Right section: cost and context window display -->
      <div class="header-right">
        <div class="cost-display">
          <span class="cost-label">Cost:</span>
          <span class="cost-value">${{ orchestratorCost }}</span>
        </div>
        <div class="context-display" :class="contextWindowClass">
          <span class="context-label">Context:</span>
          <span class="context-value">{{ contextWindowDisplay }}</span>
        </div>
      </div>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <!-- Empty State -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p class="empty-title">Start a conversation</p>
        <p class="empty-subtitle">
          Ask the orchestrator to create, manage, or command agents
        </p>
      </div>

      <!-- Chat Messages -->
      <div v-else class="message-list">
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-wrapper"
          :class="`message-${message.sender}`"
        >
          <!-- Text Message -->
          <div v-if="message.type === 'text'" class="message-bubble">
            <div class="message-header">
              <span class="message-sender">{{
                message.sender === "user" ? "YOU" : "ORCHESTRATOR"
              }}</span>
              <span class="message-time">{{
                formatTime(message.timestamp)
              }}</span>
            </div>
            <div
              class="message-content"
              v-html="formatContent(message.content)"
            ></div>
          </div>

          <!-- Thinking Block -->
          <ThinkingBubble
            v-else-if="message.type === 'thinking'"
            :thinking="message.thinking"
            :timestamp="message.timestamp"
          />

          <!-- Tool Use Block -->
          <ToolUseBubble
            v-else-if="message.type === 'tool_use'"
            :tool-name="message.toolName"
            :tool-input="message.toolInput"
            :timestamp="message.timestamp"
          />
        </div>
      </div>

      <!-- Typing Indicator -->
      <div
        v-if="isTyping"
        class="message-wrapper message-orchestrator typing-indicator-wrapper"
      >
        <div class="message-bubble typing-indicator">
          <div class="message-sender">ORCHESTRATOR</div>
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- Auto-scroll anchor -->
      <div ref="bottomRef"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, toRef, onMounted } from "vue";
import ThinkingBubble from "./chat/ThinkingBubble.vue";
import ToolUseBubble from "./chat/ToolUseBubble.vue";
import type { ChatMessage } from "../types";
import { renderMarkdown } from "../utils/markdown";
import { useOrchestratorStore } from "../stores/orchestratorStore";

// Props
const props = defineProps<{
  messages?: ChatMessage[];
  isConnected?: boolean;
  isTyping?: boolean;
  autoScroll?: boolean;
}>();

// Store
const store = useOrchestratorStore();

// Refs
const messagesRef = ref<HTMLElement>();
const bottomRef = ref<HTMLElement>();

// Use computed properties for reactive prop access with defaults
const messages = computed(() => props.messages || []);
const isConnected = computed(() => props.isConnected ?? false);
const isTyping = computed(() => props.isTyping ?? false);
const autoScroll = computed(() => props.autoScroll ?? true);

// Chat width computed properties
const chatWidth = computed(() => store.chatWidth);
const currentWidthLabel = computed(() => {
  const labels = {
    sm: "Small",
    md: "Medium",
    lg: "Large",
  };
  return labels[store.chatWidth];
});

// Orchestrator cost display (from store)
const orchestratorCost = computed(() => {
  return (store.orchestratorAgent?.total_cost ?? 0).toFixed(2);
});

// Context window display (200k for Claude Sonnet 4.5)
const CONTEXT_WINDOW_SIZE = 200000;

const currentTokens = computed(() => {
  const inputTokens = store.orchestratorAgent?.input_tokens ?? 0;
  const outputTokens = store.orchestratorAgent?.output_tokens ?? 0;
  return inputTokens + outputTokens;
});

const contextWindowDisplay = computed(() => {
  const current = currentTokens.value;
  const total = CONTEXT_WINDOW_SIZE;

  // Format with 'k' notation for compact display (matches AgentList.vue)
  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000) {
      return Math.round(tokens / 1000) + "k";
    }
    return tokens.toString();
  };

  return `${formatTokens(current)}/${formatTokens(total)}`;
});

const contextPercentage = computed(() => {
  return (currentTokens.value / CONTEXT_WINDOW_SIZE) * 100;
});

const contextWindowClass = computed(() => {
  const percentage = contextPercentage.value;

  if (percentage >= 90) return "context-critical"; // Red - very close to limit
  if (percentage >= 70) return "context-warning"; // Yellow - getting high
  if (percentage >= 50) return "context-moderate"; // Orange - moderate usage
  return "context-normal"; // Cyan - normal usage
});

// Scroll to bottom helper
const scrollToBottom = async () => {
  await nextTick();
  bottomRef.value?.scrollIntoView({ behavior: "smooth" });
};

// Auto-scroll to bottom when new messages arrive (only if autoScroll is enabled)
watch(
  () => messages.value.length,
  () => {
    if (autoScroll.value) {
      scrollToBottom();
    }
  }
);

// Auto-scroll when typing indicator changes (only if autoScroll is enabled)
watch(isTyping, () => {
  if (autoScroll.value) {
    scrollToBottom();
  }
});

// Auto-scroll when message content changes during streaming (only if autoScroll is enabled)
watch(
  () => {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      return lastMsg?.type === "text" ? lastMsg.content : lastMsg?.id;
    }
    return "";
  },
  () => {
    if (autoScroll.value) {
      scrollToBottom();
    }
  }
);

const formatTime = (timestamp: string | Date) => {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatContent = (content: string) => {
  // Render markdown with syntax highlighting and XSS protection
  return renderMarkdown(content);
};

// Handler for width toggle
const handleToggleWidth = () => {
  store.toggleChatWidth();
};

// Scroll to bottom on mount (when app loads with existing messages)
onMounted(() => {
  // Use setTimeout to ensure DOM is fully rendered
  if (autoScroll.value) {
    setTimeout(() => {
      scrollToBottom();
    }, 100);
  }
});
</script>

<style scoped>
.orchestrator-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.chat-header h3 {
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--accent-primary);
}

.width-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.width-toggle-btn:hover {
  background: rgba(0, 255, 255, 0.05);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.width-toggle-btn:active {
  transform: scale(0.95);
}

.width-icon {
  width: 18px;
  height: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding-left: var(--spacing-md);
  border-left: 1px solid var(--border-color);
}

.cost-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.8125rem;
  padding: 0.375rem 0.625rem;
  background: rgba(6, 182, 212, 0.1);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 4px;
  white-space: nowrap;
}

.cost-label {
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.025em;
}

.cost-value {
  color: var(--accent-primary);
  font-weight: 700;
  font-family: var(--font-mono);
}

/* Context Window Display */
.context-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.8125rem;
  padding: 0.375rem 0.625rem;
  border-radius: 4px;
  white-space: nowrap;
  transition: all 0.3s ease;
}

.context-label {
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.025em;
}

.context-value {
  font-weight: 700;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

/* Context window color states */
.context-normal {
  background: rgba(6, 182, 212, 0.1);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.context-normal .context-value {
  color: var(--accent-primary);
}

.context-moderate {
  background: rgba(251, 146, 60, 0.1);
  border: 1px solid rgba(251, 146, 60, 0.3);
}

.context-moderate .context-value {
  color: rgb(251, 146, 60);
}

.context-warning {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.context-warning .context-value {
  color: rgb(234, 179, 8);
}

.context-critical {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  animation: pulse-critical 2s infinite;
}

.context-critical .context-value {
  color: rgb(239, 68, 68);
}

@keyframes pulse-critical {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  height: calc(100% - 60px); /* Account for header */
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: var(--spacing-xl);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-md);
  opacity: 0.3;
}

.empty-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.empty-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  max-width: 300px;
}

/* Message List */
.message-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.message-wrapper {
  display: flex;
  animation: fadeIn 0.3s ease-out;
}

.message-user {
  justify-content: flex-end;
}

.message-orchestrator {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: var(--spacing-md);
  border-radius: 12px;
  word-wrap: break-word;
}

.message-user .message-bubble {
  background: var(--chat-user-bg);
  border-bottom-right-radius: 4px;
}

.message-orchestrator .message-bubble {
  background: var(--chat-orch-bg);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  gap: var(--spacing-md);
}

.message-sender {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.message-content {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--text-primary);
}

/* Markdown element styling - matches OrchestratorChatRow.vue */
.message-content :deep(p) {
  margin: 0;
}

.message-content :deep(p:not(:last-child)) {
  margin-bottom: 0.5em;
}

.message-content :deep(strong) {
  font-weight: 700;
}

.message-content :deep(em) {
  font-style: italic;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.9em;
}

.message-content :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5em 0;
  font-family: "JetBrains Mono", monospace;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 0.25em 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 0.25em 0;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4),
.message-content :deep(h5),
.message-content :deep(h6) {
  margin: 0.5em 0 0.25em 0;
  font-weight: 700;
}

.message-content :deep(h1) {
  font-size: 1.2em;
}
.message-content :deep(h2) {
  font-size: 1.1em;
}
.message-content :deep(h3) {
  font-size: 1em;
}

/* Typing Indicator */
.message-wrapper.typing-indicator-wrapper {
  margin-top: var(--spacing-md);
}

.typing-indicator {
  background: var(--chat-orch-bg);
  border: 1px solid var(--border-color);
}

.typing-dots {
  display: flex;
  gap: 4px;
  padding: var(--spacing-xs) 0;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-4px);
  }
}

/* ═══════════════════════════════════════════════════════════
   MOBILE RESPONSIVE DESIGN (< 650px)
   ═══════════════════════════════════════════════════════════ */

@media (max-width: 650px) {
  .orchestrator-chat {
    /* Component stays full height */
  }

  /* Compact header */
  .chat-header {
    padding: 0.5rem 0.75rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* Stack header elements */
  .header-left,
  .header-right {
    flex: 1 1 100%;
    justify-content: space-between;
  }

  /* Hide width toggle on mobile (no point, always small) */
  .width-toggle-btn {
    display: none;
  }

  /* Compact title */
  .chat-header h3 {
    font-size: 0.75rem;
    letter-spacing: 0.03em;
  }

  /* Simplify header stats display */
  .header-right {
    border-left: none;
    padding-left: 0;
    gap: 0.5rem;
  }

  .cost-display,
  .context-display {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
  }

  /* Compact stat labels */
  .cost-label,
  .context-label {
    display: none; /* Hide labels, show only values */
  }

  .cost-value::before {
    content: "$";
  }

  /* Reduce message area padding */
  .chat-messages {
    padding: 0.5rem;
  }

  /* Wider message bubbles on small screens (more space usage) */
  .message-bubble {
    max-width: 92%;
    padding: 0.625rem 0.75rem;
    font-size: 0.8125rem;
  }

  /* Compact message header */
  .message-header {
    margin-bottom: 0.25rem;
    gap: 0.5rem;
  }

  .message-sender {
    font-size: 0.65rem;
  }

  .message-time {
    font-size: 0.65rem;
  }

  /* Compact empty state */
  .empty-state {
    padding: 1rem;
  }

  .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  .empty-title {
    font-size: 0.875rem;
  }

  .empty-subtitle {
    font-size: 0.75rem;
    max-width: 250px;
  }

  /* Touch-optimized typing indicator */
  .typing-indicator {
    padding: 0.5rem 0.75rem;
  }
}
</style>
