<template>
  <Transition name="command-input">
    <div v-show="visible" class="global-command-input-container">
      <div class="command-input-wrapper">
        <textarea
          ref="textareaRef"
          v-model="message"
          @input="handleInput"
          @keydown="handleKeydown"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.escape="handleEscape"
          @autocomplete-accept="handleAutocompleteAccept"
          class="command-input"
          placeholder="Type your command or message..."
          rows="4"
          :disabled="!isConnected"
          aria-label="Command input"
        />

        <div class="command-actions">
          <!-- Autocomplete Section - Pills and/or Loading -->
          <div
            v-if="hasAutocompleteItems || autocompleteLoading"
            class="autocomplete-section"
          >
            <!-- Loading Indicator - Shows to the left when refreshing -->
            <div v-if="autocompleteLoading" class="autocomplete-loading">
              <div class="loading-spinner"></div>
              <span class="loading-text">{{
                hasAutocompleteItems
                  ? "Refreshing..."
                  : "Generating suggestions..."
              }}</span>
            </div>

            <!-- Autocomplete Pills - Keep visible during refresh -->
            <div v-if="hasAutocompleteItems" class="autocomplete-pills">
              <div
                v-for="(item, index) in autocompleteItems"
                :key="index"
                class="autocomplete-pill"
                @click="handlePillClick(index)"
                :title="item.reasoning"
              >
                <span class="pill-hotkey">Ctrl+{{ index + 1 }}</span>
                <span class="pill-text">{{ item.completion }}</span>
              </div>
            </div>
          </div>

          <!-- Spacer to push right content to the right -->
          <div class="center-spacer"></div>

          <!-- Right Actions - Hints and Send Button -->
          <div class="right-actions">
            <div class="shortcut-hint">
              Press <kbd>Esc</kbd> to close • <kbd>Enter</kbd> to send •
              <kbd>Shift+Enter</kbd> for new line
            </div>
            <button
              class="btn-send"
              @click="sendMessage"
              :disabled="!message.trim() || !isConnected"
            >
              <span class="send-icon">▶</span>
              Send
            </button>
          </div>
        </div>
      </div>

      <!-- NEW: System Information Panel -->
      <div
        v-if="
          systemInfo ||
          agents.length > 0 ||
          slashCommands.length > 0 ||
          agentTemplates.length > 0 ||
          adwWorkflows.length > 0 ||
          orchestratorTools.length > 0
        "
        class="system-info-panel"
      >
        <div class="info-row" v-if="systemInfo?.session_id">
          <span class="info-label">Orchestrator Session ID:</span>
          <span
            class="info-value clickable-value"
            @click="copyToClipboard(systemInfo.session_id, 'Session ID')"
            :class="{ copied: copiedItem === 'Session ID' }"
            title="Click to copy"
          >
            {{ systemInfo.session_id }}
          </span>
        </div>

        <div class="info-row" v-if="systemInfo?.cwd">
          <span class="info-label">Working Directory:</span>
          <span
            class="info-value clickable-value"
            @click="copyToClipboard(systemInfo.cwd, 'CWD')"
            :class="{ copied: copiedItem === 'CWD' }"
            title="Click to copy"
          >
            {{ systemInfo.cwd }}
          </span>
        </div>

        <div class="info-row" v-if="agents.length > 0">
          <span class="info-label">Agents:</span>
          <div class="info-tags">
            <span
              v-for="agent in agents"
              :key="agent.id"
              class="badge clickable-badge agent-badge"
              :class="{ copied: copiedItem === `agent-${agent.id}` }"
              :style="{
                borderColor: getAgentBorderColor(agent.name, agent.id),
              }"
              :title="`${agent.name} (click to add)`"
              @click="appendToInput(agent.name, `agent-${agent.id}`)"
            >
              {{ agent.name }}
            </span>
          </div>
        </div>

        <div class="info-row" v-if="slashCommands.length > 0">
          <span class="info-label">Slash Commands:</span>
          <div class="info-tags">
            <span
              v-for="cmd in slashCommands"
              :key="cmd.name"
              class="badge badge-info clickable-badge"
              :class="{ copied: copiedItem === `cmd-${cmd.name}` }"
              :title="`${cmd.description} (click to add)`"
              @click="appendToInput(`/${cmd.name}`, `cmd-${cmd.name}`)"
            >
              /{{ cmd.name }}
            </span>
          </div>
        </div>

        <div class="info-row" v-if="agentTemplates.length > 0">
          <span class="info-label">Agent Templates:</span>
          <div class="info-tags">
            <span
              v-for="template in agentTemplates"
              :key="template.frontmatter?.name || template.name"
              class="badge badge-success clickable-badge"
              :class="{
                copied:
                  copiedItem ===
                  `tpl-${template.frontmatter?.name || template.name}`,
              }"
              :title="`${
                template.frontmatter?.description || template.description
              } (click to add)`"
              @click="
                appendToInput(
                  template.frontmatter?.name || template.name,
                  `tpl-${template.frontmatter?.name || template.name}`
                )
              "
            >
              {{ template.frontmatter?.name || template.name }}
            </span>
          </div>
        </div>

        <div class="info-row" v-if="adwWorkflows.length > 0">
          <span class="info-label">AI Developer Workflows:</span>
          <div class="info-tags">
            <span
              v-for="workflow in adwWorkflows"
              :key="workflow.type"
              class="badge badge-adw clickable-badge"
              :class="{ copied: copiedItem === `adw-${workflow.type}` }"
              :title="`${workflow.description} (click to add)`"
              @click="
                appendToInput(
                  `start_adw workflow_type=${workflow.display_name}`,
                  `adw-${workflow.type}`
                )
              "
            >
              🔄 {{ workflow.display_name }}
            </span>
          </div>
        </div>

        <div class="info-row" v-if="orchestratorTools.length > 0">
          <span class="info-label">Orchestrator Tools:</span>
          <div class="info-tags">
            <span
              v-for="(tool, index) in orchestratorTools"
              :key="index"
              class="badge badge-warning clickable-badge"
              :class="{ copied: copiedItem === `tool-${index}` }"
              :title="`Click to add`"
              @click="appendToInput(tool, `tool-${index}`)"
            >
              {{ tool }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from "vue";
import { useOrchestratorStore } from "../stores/orchestratorStore";
import { useAutocomplete } from "../composables/useAutocomplete";
import { getOrchestratorInfo } from "../services/chatService";
import { getAgentBorderColor } from "../utils/agentColors";
import type {
  SystemMessageInfo,
  SlashCommand,
  SubagentTemplate,
  AdwWorkflow,
  Agent,
} from "../types";

// Store
const store = useOrchestratorStore();

// Autocomplete
const {
  autocompleteItems,
  autocompleteLoading,
  hasAutocompleteItems,
  generateAutocomplete,
  clearAutocomplete,
  handleAutocompleteKeydown,
} = useAutocomplete();

// Props
const props = defineProps<{
  visible: boolean;
}>();

// Emits
const emit = defineEmits<{
  send: [message: string];
}>();

// Refs
const textareaRef = ref<HTMLTextAreaElement>();
const message = ref("");

// NEW: System info refs
const systemInfo = ref<SystemMessageInfo | null>(null);
const slashCommands = ref<SlashCommand[]>([]);
const agentTemplates = ref<SubagentTemplate[]>([]);
const orchestratorTools = ref<string[]>([]);
const adwWorkflows = ref<AdwWorkflow[]>([]);

// Copy to clipboard state
const copiedItem = ref<string | null>(null);
let copyTimeout: NodeJS.Timeout | null = null;

// Computed
const isConnected = computed(() => store.isConnected);
const agents = computed(() => store.agents);

// NEW: Fetch orchestrator info
const fetchOrchestratorInfo = async () => {
  try {
    console.log("[GlobalCommandInput] Fetching orchestrator info...");
    const response = await getOrchestratorInfo();

    console.log("[GlobalCommandInput] Response received:", {
      status: response.status,
      orchestrator: response.orchestrator,
      slashCommandsCount: response.slash_commands?.length || 0,
      agentTemplatesCount: response.agent_templates?.length || 0,
    });

    if (response.status === "success") {
      // Extract system message info from metadata
      const metadata = response.orchestrator.metadata;
      console.log("[GlobalCommandInput] Metadata:", metadata);

      if (metadata?.system_message_info) {
        systemInfo.value = metadata.system_message_info;
        console.log(
          "[GlobalCommandInput] System info extracted:",
          systemInfo.value
        );
      } else {
        console.warn("[GlobalCommandInput] No system_message_info in metadata");
      }

      // Store slash commands, templates, tools, and ADW workflows
      slashCommands.value = response.slash_commands || [];
      agentTemplates.value = response.agent_templates || [];
      orchestratorTools.value = response.orchestrator_tools || [];
      adwWorkflows.value = response.adw_workflows || [];

      console.log("[GlobalCommandInput] Loaded system info:", {
        hasSystemInfo: !!systemInfo.value,
        sessionId: systemInfo.value?.session_id,
        cwd: systemInfo.value?.cwd,
        commandCount: slashCommands.value.length,
        templateCount: agentTemplates.value.length,
        toolCount: orchestratorTools.value.length,
        adwWorkflowCount: adwWorkflows.value.length,
      });
    }
  } catch (error) {
    console.error(
      "[GlobalCommandInput] Failed to fetch orchestrator info:",
      error
    );
  }
};

// Autocomplete tracking
const inputBeforeCompletion = ref("");

// Autocomplete handlers
const handleInput = (event: Event) => {
  const value = (event.target as HTMLTextAreaElement).value;
  message.value = value;
  generateAutocomplete(value);
};

const handleKeydown = (event: KeyboardEvent) => {
  handleAutocompleteKeydown(event);
};

const handleAutocompleteAccept = (event: any) => {
  const { completion, reasoning } = event.detail;
  inputBeforeCompletion.value = message.value;
  message.value += completion;

  // Track autocomplete acceptance
  store.updateAutocompleteHistory(
    "autocomplete",
    undefined,
    inputBeforeCompletion.value,
    completion,
    reasoning
  );

  clearAutocomplete();
  nextTick(() => textareaRef.value?.focus());
};

const handlePillClick = (index: number) => {
  // Simulate Ctrl+number keypress
  const event = new KeyboardEvent("keydown", {
    ctrlKey: true,
    key: String(index + 1),
  });
  textareaRef.value?.dispatchEvent(event);
};

// Methods
const sendMessage = () => {
  if (!message.value.trim() || !isConnected.value) return;

  const messageToSend = message.value.trim();

  // Track completion history if autocomplete was shown but not used
  if (hasAutocompleteItems.value) {
    store.updateAutocompleteHistory("none", messageToSend);
  }

  emit("send", messageToSend);
  message.value = "";
  inputBeforeCompletion.value = "";

  // Clear autocomplete
  clearAutocomplete();

  // Close the command input after sending
  store.hideCommandInput();
};

const handleEscape = () => {
  store.hideCommandInput();
};

// Append text to input field
const appendToInput = (text: string, itemId: string) => {
  // Add space if there's already content
  if (message.value.trim()) {
    message.value += " ";
  }

  message.value += text;

  // Set copied state for visual feedback (using same animation)
  copiedItem.value = itemId;

  // Clear previous timeout if exists
  if (copyTimeout) {
    clearTimeout(copyTimeout);
  }

  // Reset after 2 seconds
  copyTimeout = setTimeout(() => {
    copiedItem.value = null;
    copyTimeout = null;
  }, 2000);

  // Focus the textarea
  nextTick(() => {
    textareaRef.value?.focus();
  });

  console.log(`[GlobalCommandInput] Appended to input: ${text}`);
};

// Copy to clipboard function with visual feedback (kept for session ID and CWD)
const copyToClipboard = async (text: string, itemId: string) => {
  try {
    await navigator.clipboard.writeText(text);

    // Set copied state for visual feedback
    copiedItem.value = itemId;

    // Clear previous timeout if exists
    if (copyTimeout) {
      clearTimeout(copyTimeout);
    }

    // Reset after 2 seconds
    copyTimeout = setTimeout(() => {
      copiedItem.value = null;
      copyTimeout = null;
    }, 2000);

    console.log(`[GlobalCommandInput] Copied to clipboard: ${text}`);
  } catch (error) {
    console.error("[GlobalCommandInput] Failed to copy to clipboard:", error);
  }
};

// Global escape key handler (works even when not focused on textarea)
const handleGlobalEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape" && props.visible) {
    handleEscape();
  }
};

// Watch for visibility changes to handle focus and refetch data
watch(
  () => props.visible,
  async (newValue) => {
    if (newValue) {
      // Refetch orchestrator info to get latest data from filesystem
      console.log("[GlobalCommandInput] Component opened - refetching data...");
      await fetchOrchestratorInfo();

      // Wait for DOM update then focus
      await nextTick();
      textareaRef.value?.focus();
    }
  }
);

// Register global escape handler and fetch info on mount
onMounted(() => {
  document.addEventListener("keydown", handleGlobalEscape);
  fetchOrchestratorInfo(); // NEW: Fetch on mount
});

// Clean up event listener on unmount
onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalEscape);
});
</script>

<style scoped>
/* Container that covers the bottom area */
.global-command-input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
  backdrop-filter: blur(10px);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
}

/* Wrapper that controls the actual width */
.command-input-wrapper {
  max-width: 100vw; /* Full width */
  margin-left: 0; /* No left margin */
  padding: var(--spacing-lg) var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* Mobile responsive - keep full width */
@media (max-width: 768px) {
  .command-input-wrapper {
    margin-left: 0;
    max-width: 100vw;
  }
}

/* The textarea itself */
.command-input {
  width: 100%;
  min-height: 100px;
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border: 2px solid var(--accent-primary);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.5;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s ease;
}

.command-input:focus {
  outline: none;
  border-color: var(--accent-hover);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
  background: var(--bg-primary);
}

.command-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.command-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

/* Actions bar - pills on left, controls on right */
.command-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

/* Center spacer to push right content to the right */
.center-spacer {
  flex: 1;
  min-width: var(--spacing-md);
}

/* Right actions group (hint + button only) */
.right-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

/* Keyboard shortcut hints */
.shortcut-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.shortcut-hint kbd {
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85em;
  color: var(--text-secondary);
}

/* Send button */
.btn-send {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-send:hover:not(:disabled) {
  background: var(--accent-hover);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
  transform: translateY(-1px);
}

.btn-send:active:not(:disabled) {
  transform: translateY(0);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  font-size: 0.9rem;
}

/* Transition animations */
.command-input-enter-active,
.command-input-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.command-input-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.command-input-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Responsive adjustments - full width across all breakpoints */
@media (max-width: 1400px) {
  .command-input-wrapper {
    margin-left: 0;
    max-width: 100vw;
  }
}

@media (max-width: 1200px) {
  .command-input-wrapper {
    margin-left: 0;
    max-width: 100vw;
  }
}

@media (max-width: 1024px) {
  .command-input-wrapper {
    margin-left: 0;
    max-width: 100vw;
    padding: var(--spacing-md) var(--spacing-lg);
  }
}

@media (max-width: 768px) {
  .command-input-wrapper {
    margin-left: 0;
    max-width: 100vw;
    padding: var(--spacing-md);
  }

  .command-input {
    font-size: 0.9rem;
    min-height: 80px;
  }

  /* Stack elements on mobile */
  .command-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-sm);
  }

  /* Pills take full width on mobile */
  .autocomplete-pills {
    width: 100%;
    justify-content: flex-start;
  }

  /* Hide spacer on mobile */
  .center-spacer {
    display: none;
  }

  /* Right actions centered on mobile */
  .right-actions {
    gap: var(--spacing-sm);
    justify-content: center;
  }

  .shortcut-hint {
    font-size: 0.7rem;
  }

  .btn-send {
    font-size: 0.9rem;
    padding: var(--spacing-xs) var(--spacing-md);
  }
}

/* System Information Panel */
.system-info-panel {
  padding: 1rem 1.5rem;
  background: rgba(6, 182, 212, 0.05);
  border-top: 1px solid rgba(6, 182, 212, 0.2);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 100vw; /* Full width */
  margin-left: 0; /* No left margin */
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  font-size: 0.875rem;
}

.info-label {
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 180px;
  flex-shrink: 0;
}

.info-value {
  color: var(--text-primary);
  font-family: "Courier New", monospace;
  word-break: break-all;
  padding-left: 0.5rem;
  border-left: 2px solid rgba(6, 182, 212, 0.3);
}

/* Clickable value styles */
.clickable-value {
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  padding: 0.25rem 0.5rem;
  margin-left: 0.25rem;
  border-radius: 4px;
}

.clickable-value:hover {
  background: rgba(6, 182, 212, 0.15);
  border-left-color: rgba(6, 182, 212, 0.6);
}

.clickable-value.copied {
  background: rgba(16, 185, 129, 0.2);
  border-left-color: rgba(16, 185, 129, 0.8);
  animation: copyPulse 0.4s ease;
}

.clickable-value.copied::after {
  content: "✓ Copied";
  position: absolute;
  top: -25px;
  right: 0;
  background: rgba(16, 185, 129, 0.9);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  white-space: nowrap;
  animation: fadeInOut 2s ease;
}

@keyframes copyPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes fadeInOut {
  0% {
    opacity: 0;
    transform: translateY(5px);
  }
  20% {
    opacity: 1;
    transform: translateY(0);
  }
  80% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-5px);
  }
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.info-tags .badge {
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.info-tags .badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

/* Clickable badge styles */
.clickable-badge {
  position: relative;
}

.clickable-badge.copied {
  animation: copyPulse 0.4s ease;
  filter: brightness(1.3);
}

.clickable-badge.copied::after {
  content: "✓";
  position: absolute;
  top: -8px;
  right: -8px;
  background: rgba(16, 185, 129, 0.9);
  color: white;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  animation: fadeInOut 2s ease;
}

/* Agent badge with dynamic border color */
.agent-badge {
  border-width: 2px;
  border-style: solid;
  /* borderColor set via :style binding to match agent color */
  background: rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
}

.agent-badge:hover {
  background: rgba(0, 0, 0, 0.5);
  filter: brightness(1.2);
}

/* ADW Workflow Badge - Purple/Magenta theme */
.badge-adw {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.3);
  transition: all 0.2s ease;
}

.badge-adw:hover {
  background: rgba(168, 85, 247, 0.3);
  border-color: rgba(168, 85, 247, 0.6);
  filter: brightness(1.2);
}

/* Responsive adjustments for system info panel */
@media (max-width: 768px) {
  .system-info-panel {
    margin-left: 0;
    max-width: 100vw;
  }

  .info-row {
    flex-direction: column;
    gap: 0.25rem;
  }

  .info-label {
    min-width: unset;
  }

  .info-value {
    padding-left: 0;
    border-left: none;
    border-top: 2px solid rgba(6, 182, 212, 0.3);
    padding-top: 0.25rem;
  }
}

/* Autocomplete Section - Container for loading + pills */
.autocomplete-section {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: nowrap; /* Prevent wrapping to maintain fixed height */
  height: 41px; /* FIXED height - never changes, eliminates all jitter */
  overflow: hidden; /* Prevent content from breaking out of fixed height */
  animation: slideDown 0.2s ease-out;
}

/* Autocomplete Pills - Left Aligned */
.autocomplete-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.autocomplete-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--gray-800, #1f2937);
  border: 1px solid var(--gray-700, #374151);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.autocomplete-pill:hover {
  background: var(--gray-700, #374151);
  border-color: var(--cyan-500, #06b6d4);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.pill-hotkey {
  font-size: 11px;
  font-weight: 600;
  color: var(--cyan-400, #22d3ee);
  padding: 2px 6px;
  background: var(--gray-900, #111827);
  border-radius: 4px;
  font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code",
    "Droid Sans Mono", "Source Code Pro", monospace;
}

.pill-text {
  font-size: 13px;
  color: var(--gray-200, #e5e7eb);
  font-weight: 500;
}

/* Loading state */
.autocomplete-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: var(--gray-400, #9ca3af);
  font-size: 12px;
  font-style: italic;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--gray-700, #374151);
  border-top-color: var(--cyan-400, #22d3ee);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  color: var(--cyan-400, #22d3ee);
  font-size: 13px;
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
