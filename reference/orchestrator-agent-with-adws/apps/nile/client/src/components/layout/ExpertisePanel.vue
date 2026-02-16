<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { marked } from 'marked';
import { useExpertiseStore } from '../../stores/expertise';

const expertiseStore = useExpertiseStore();

// Toggle for raw vs pretty markdown
const showRawPrompt = ref(false);

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
});

// Render system prompt as HTML
const renderedSystemPrompt = computed(() => {
  if (!expertiseStore.liveSystemPrompt?.system_prompt) return '';
  return marked(expertiseStore.liveSystemPrompt.system_prompt) as string;
});

// Render user prompt as HTML
const renderedUserPrompt = computed(() => {
  if (!expertiseStore.liveSystemPrompt?.user_prompt) return '';
  return marked(expertiseStore.liveSystemPrompt.user_prompt) as string;
});

// Format expertise data as JSON blob
const expertiseJson = computed(() => {
  const data = expertiseStore.expertiseData;
  return JSON.stringify({
    checked_out: data.checked_out || [],
    added_to_cart: data.added_to_cart || [],
    viewed_products: data.viewed_products || []
  }, null, 2);
});

// Format timestamp for action log
function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// Get phase color
function getPhaseColor(phase: string): string {
  switch (phase) {
    case 'ACT': return '#f59e0b';    // amber
    case 'LEARN': return '#10b981';  // emerald
    case 'REUSE': return '#6366f1';  // indigo
    default: return '#9ca3af';
  }
}

// Fetch expertise when panel opens
watch(() => expertiseStore.panelOpen, (isOpen) => {
  if (isOpen) {
    expertiseStore.fetchExpertise();
  }
});

// Fetch live system prompt when switching to that tab
watch(() => expertiseStore.showSystemPrompt, (showPrompt) => {
  if (showPrompt) {
    expertiseStore.fetchLiveSystemPrompt();
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition name="slide">
      <div v-if="expertiseStore.panelOpen" class="expertise-panel">
        <div class="panel-header">
          <h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            Agent Expert Mind
          </h3>
          <div class="header-actions">
            <button class="clear-btn" @click="expertiseStore.clearExpertise" title="Clear Expertise (Ctrl+Shift+C)">
              Clear
            </button>
            <button class="close-btn" @click="expertiseStore.closePanel">
              &times;
            </button>
          </div>
        </div>

        <!-- ACT → LEARN → REUSE Cycle Indicator -->
        <div class="cycle-indicator">
          <div class="cycle-step">
            <span class="cycle-icon act">ACT</span>
            <span class="cycle-label">User Action</span>
          </div>
          <span class="cycle-arrow">→</span>
          <div class="cycle-step">
            <span class="cycle-icon learn">LEARN</span>
            <span class="cycle-label">Store Expertise</span>
          </div>
          <span class="cycle-arrow">→</span>
          <div class="cycle-step">
            <span class="cycle-icon reuse">REUSE</span>
            <span class="cycle-label">Personalize</span>
          </div>
        </div>

        <div class="panel-stats">
          <div class="stat">
            <span class="stat-value">{{ expertiseStore.totalImprovements }}</span>
            <span class="stat-label">Total Improvements</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ expertiseStore.expertiseData.viewed_products?.length || 0 }}</span>
            <span class="stat-label">Views</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ expertiseStore.expertiseData.added_to_cart?.length || 0 }}</span>
            <span class="stat-label">Cart</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ expertiseStore.expertiseData.checked_out?.length || 0 }}</span>
            <span class="stat-label">Purchased</span>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-nav">
          <button
            class="tab-btn"
            :class="{ active: !expertiseStore.showSystemPrompt }"
            @click="expertiseStore.showSystemPrompt = false"
          >
            Expertise
          </button>
          <button
            class="tab-btn"
            :class="{ active: expertiseStore.showSystemPrompt }"
            @click="expertiseStore.showSystemPrompt = true"
          >
            System Prompt
          </button>
        </div>

        <div class="panel-content">
          <!-- Expertise Tab -->
          <template v-if="!expertiseStore.showSystemPrompt">
            <!-- Simple SQL Query -->
            <div class="expertise-section" v-if="expertiseStore.totalImprovements > 0">
              <div class="expertise-header">
                <span class="expertise-title">Source Table</span>
                <span class="expertise-badge">{{ expertiseStore.totalImprovements }} signals</span>
              </div>
              <pre class="sql-block">SELECT expertise_data FROM user_expertise
WHERE user_id = :current_user_id;</pre>
            </div>

            <!-- Expertise JSON Blob -->
            <div class="expertise-section" v-if="expertiseStore.totalImprovements > 0">
              <div class="expertise-header">
                <span class="expertise-title">expertise_data</span>
                <span class="expertise-badge json-badge">JSONB</span>
              </div>
              <pre class="json-block">{{ expertiseJson }}</pre>
            </div>

            <!-- Empty State -->
            <div v-if="expertiseStore.totalImprovements === 0" class="empty-state">
              <p>No expertise data yet.</p>
              <p>Browse products to build the agent's mental model.</p>
            </div>

            <!-- Action Log (collapsed) -->
            <details v-if="expertiseStore.actionLog.length" class="action-log-details">
              <summary>Recent Actions ({{ expertiseStore.actionLog.length }})</summary>
              <div class="action-log">
                <div
                  v-for="(entry, index) in expertiseStore.actionLog"
                  :key="index"
                  class="log-entry"
                >
                  <span
                    class="log-phase"
                    :style="{ backgroundColor: getPhaseColor(entry.phase) }"
                  >
                    {{ entry.phase }}
                  </span>
                  <span class="log-time">{{ formatTime(entry.timestamp) }}</span>
                  <span class="log-details">{{ entry.details }}</span>
                </div>
              </div>
            </details>
          </template>

          <!-- System Prompt Tab -->
          <template v-else>
            <div class="system-prompt-section">
              <!-- Loading State -->
              <div v-if="expertiseStore.systemPromptLoading" class="prompt-loading">
                <div class="loading-spinner"></div>
                <p>Loading live system prompt...</p>
              </div>

              <!-- Error State -->
              <div v-else-if="expertiseStore.systemPromptError" class="prompt-error">
                <p>{{ expertiseStore.systemPromptError }}</p>
                <button class="retry-btn" @click="expertiseStore.fetchLiveSystemPrompt">Retry</button>
              </div>

              <!-- Live System Prompt -->
              <template v-else-if="expertiseStore.liveSystemPrompt">
                <div class="prompt-header">
                  <h4>System Prompt</h4>
                  <!-- Pretty/Raw Toggle -->
                  <div class="view-toggle">
                    <button
                      class="toggle-btn"
                      :class="{ active: !showRawPrompt }"
                      @click="showRawPrompt = false"
                    >
                      Pretty
                    </button>
                    <button
                      class="toggle-btn"
                      :class="{ active: showRawPrompt }"
                      @click="showRawPrompt = true"
                    >
                      Raw
                    </button>
                  </div>
                </div>
                <p class="prompt-note">
                  This is the exact system prompt sent to Claude, with all template variables populated from your current expertise data.
                </p>

                <!-- System Prompt -->
                <div class="prompt-block">
                  <div class="prompt-block-header">
                    <span>System Prompt</span>
                    <span class="char-count">{{ expertiseStore.liveSystemPrompt.system_prompt.length.toLocaleString() }} chars</span>
                  </div>
                  <!-- Pretty View -->
                  <div v-if="!showRawPrompt" class="markdown-content system-prompt" v-html="renderedSystemPrompt"></div>
                  <!-- Raw View -->
                  <pre v-else class="raw-content system-prompt">{{ expertiseStore.liveSystemPrompt.system_prompt }}</pre>
                </div>

                <!-- User Prompt -->
                <div class="prompt-block">
                  <div class="prompt-block-header">
                    <span>User Prompt</span>
                    <span class="char-count">{{ expertiseStore.liveSystemPrompt.user_prompt.length }} chars</span>
                  </div>
                  <!-- Pretty View -->
                  <div v-if="!showRawPrompt" class="markdown-content user-prompt" v-html="renderedUserPrompt"></div>
                  <!-- Raw View -->
                  <pre v-else class="raw-content user-prompt">{{ expertiseStore.liveSystemPrompt.user_prompt }}</pre>
                </div>
              </template>

              <!-- No Data State -->
              <div v-else class="empty-state">
                <p>Click to load the live system prompt.</p>
                <button class="load-btn" @click="expertiseStore.fetchLiveSystemPrompt">Load Prompt</button>
              </div>
            </div>
          </template>
        </div>

        <div class="panel-footer">
          <p class="hint">
            <kbd>Ctrl+K</kbd> Toggle Panel &nbsp;|&nbsp;
            <kbd>Ctrl+Shift+C</kbd> Clear Expertise
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.expertise-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 630px;
  height: 100vh;
  background: #1a1a2e;
  color: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  color: #ff9900;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.clear-btn {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.close-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 0.5rem;
  line-height: 1;
}

.close-btn:hover {
  color: white;
}

/* ACT → LEARN → REUSE Cycle */
.cycle-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.cycle-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.cycle-icon {
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.cycle-icon.act {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.cycle-icon.learn {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.cycle-icon.reuse {
  background: rgba(99, 102, 241, 0.2);
  color: #6366f1;
  border: 1px solid rgba(99, 102, 241, 0.4);
}

.cycle-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.cycle-arrow {
  color: rgba(255, 255, 255, 0.3);
  font-size: 1rem;
}

.panel-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: #ff9900;
}

.stat-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Tab Navigation */
.tab-nav {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.tab-btn.active {
  background: rgba(255, 153, 0, 0.1);
  color: #ff9900;
  border-bottom: 2px solid #ff9900;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

/* Action Log */
.action-log {
  margin-bottom: 1.5rem;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 0.75rem;
}

.log-phase {
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.6rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.log-time {
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
  font-family: monospace;
}

.log-details {
  color: rgba(255, 255, 255, 0.8);
  flex: 1;
}

.section {
  margin-bottom: 1.5rem;
}

.section h4 {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.code-block {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-family: 'Monaco', 'Menlo', monospace;
  overflow-x: auto;
  color: #10b981;
  white-space: pre-wrap;
  word-break: break-word;
}

.code-block.system-prompt {
  color: #9ca3af;
  font-size: 0.75rem;
  line-height: 1.5;
}

.system-prompt-section h4 {
  color: #ff9900;
  margin-bottom: 0.5rem;
}

.prompt-note {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 1rem;
  line-height: 1.4;
}

/* Live System Prompt Styles */
.prompt-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 153, 0, 0.2);
  border-top-color: #ff9900;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.prompt-loading p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
}

.prompt-error {
  padding: 2rem;
  text-align: center;
  color: #ef4444;
}

.prompt-error p {
  margin-bottom: 1rem;
}

.retry-btn,
.load-btn {
  background: rgba(255, 153, 0, 0.2);
  border: 1px solid rgba(255, 153, 0, 0.4);
  color: #ff9900;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.retry-btn:hover,
.load-btn:hover {
  background: rgba(255, 153, 0, 0.3);
}

.prompt-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.prompt-header h4 {
  margin: 0;
}

/* View Toggle */
.view-toggle {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.toggle-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:first-child {
  border-radius: 4px 0 0 4px;
}

.toggle-btn:last-child {
  border-radius: 0 4px 4px 0;
}

.toggle-btn.active {
  background: rgba(255, 153, 0, 0.2);
  border-color: rgba(255, 153, 0, 0.4);
  color: #ff9900;
}

.toggle-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

/* Raw Content */
.raw-content {
  background: rgba(0, 0, 0, 0.4);
  padding: 1rem;
  border-radius: 0 0 8px 8px;
  max-height: 500px;
  overflow-y: auto;
  font-size: 0.75rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.5;
  color: #9ca3af;
  white-space: pre-wrap;
  word-break: break-word;
}

.raw-content.user-prompt {
  color: #a5b4fc;
}

/* Expertise Section Styles */
.expertise-section {
  margin-bottom: 1.5rem;
}

.expertise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.expertise-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #ff9900;
}

.expertise-badge {
  background: rgba(255, 153, 0, 0.2);
  border: 1px solid rgba(255, 153, 0, 0.3);
  color: #ff9900;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 600;
}

.sql-block {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #10b981;
  overflow-x: auto;
  white-space: pre-wrap;
}

/* JSON Block Styles */
.json-block {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  color: #a5b4fc;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

.json-badge {
  background: rgba(99, 102, 241, 0.2) !important;
  border-color: rgba(99, 102, 241, 0.4) !important;
  color: #a5b4fc !important;
}

/* Action Log Details */
.action-log-details {
  margin-top: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.action-log-details summary {
  padding: 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.action-log-details[open] summary {
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.action-log-details .action-log {
  padding: 0.5rem;
  margin: 0;
}

.prompt-block {
  margin-bottom: 1rem;
}

.prompt-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px 8px 0 0;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

.char-count {
  color: rgba(255, 255, 255, 0.4);
  font-weight: 400;
  font-family: monospace;
}

/* Markdown Content Styles */
.markdown-content {
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 0 0 8px 8px;
  max-height: 500px;
  overflow-y: auto;
  font-size: 0.8rem;
  line-height: 1.6;
  color: #e5e7eb;
}

.markdown-content.user-prompt {
  color: #a5b4fc;
}

/* Headings */
.markdown-content :deep(h1) {
  font-size: 1.3rem;
  color: #ff9900;
  margin: 1.5rem 0 0.75rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 153, 0, 0.3);
}

.markdown-content :deep(h2) {
  font-size: 1.1rem;
  color: #fbbf24;
  margin: 1.25rem 0 0.5rem 0;
}

.markdown-content :deep(h3) {
  font-size: 0.95rem;
  color: #fcd34d;
  margin: 1rem 0 0.5rem 0;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 0.85rem;
  color: #fde68a;
  margin: 0.75rem 0 0.4rem 0;
}

/* Paragraphs */
.markdown-content :deep(p) {
  margin: 0.5rem 0;
}

/* Lists */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(li) {
  margin: 0.25rem 0;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
}

/* Code blocks */
.markdown-content :deep(pre) {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 6px;
  padding: 0.75rem;
  margin: 0.75rem 0;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #10b981;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.75rem;
}

/* Inline code */
.markdown-content :deep(code) {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 0.75rem;
}

/* Tables */
.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 0.75rem;
}

.markdown-content :deep(th) {
  background: rgba(255, 153, 0, 0.2);
  color: #ff9900;
  padding: 0.5rem;
  text-align: left;
  border: 1px solid rgba(255, 153, 0, 0.3);
  font-weight: 600;
}

.markdown-content :deep(td) {
  padding: 0.4rem 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: rgba(255, 255, 255, 0.03);
}

/* Blockquotes */
.markdown-content :deep(blockquote) {
  border-left: 3px solid #6366f1;
  margin: 0.75rem 0;
  padding: 0.5rem 1rem;
  background: rgba(99, 102, 241, 0.1);
  color: #c7d2fe;
}

/* Horizontal rules */
.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  margin: 1rem 0;
}

/* Strong and emphasis */
.markdown-content :deep(strong) {
  color: #fbbf24;
  font-weight: 600;
}

.markdown-content :deep(em) {
  color: #a5b4fc;
  font-style: italic;
}

/* Links */
.markdown-content :deep(a) {
  color: #60a5fa;
  text-decoration: underline;
}

.markdown-content :deep(a:hover) {
  color: #93c5fd;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.5);
}

.panel-footer {
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.hint {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}

kbd {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

/* Transition */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
