<template>
  <div
    class="file-changes-display"
    :class="{ 'layout-two-column': layout === 'two-column' }"
  >
    <!-- Two-column layout: Left = Consumed, Right = Produced -->
    <div v-if="layout === 'two-column'" class="two-column-grid">
      <!-- Left Column: Consumed (Read Files) -->
      <div v-if="readFiles.length > 0" class="read-files-section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <span class="section-title">Consumed</span>
          <span class="section-count">{{ readFiles.length }} files</span>
        </div>

        <div class="file-cards-stack">
          <div
            v-for="file in readFiles"
            :key="file.path"
            class="file-card read-file-card"
            @click="handleFileClick(file.absolute_path)"
            :title="`Click to open ${file.path} in IDE\nRead for context`"
          >
            <div class="file-path">{{ file.path }}</div>
            <div class="line-count-badge">
              {{ formatLineCount(file.line_count) }} Read
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Produced (Modified Files) -->
      <div v-if="fileChanges.length > 0" class="modified-files-section">
        <div class="section-header">
          <span class="section-icon">📝</span>
          <span class="section-title">Produced</span>
          <span class="section-count">{{ fileChanges.length }} files</span>
        </div>

        <div class="file-cards-stack">
          <div
            v-for="file in fileChanges"
            :key="file.path"
            class="file-card modified-file-card"
            :class="`status-${file.status}`"
            @click="handleFileClick(file.absolute_path)"
            :title="`Click to open ${file.path} in IDE`"
          >
            <div class="file-header">
              <div class="file-path">{{ file.path }}</div>
              <div class="file-badges">
                <span class="status-badge" :class="`status-${file.status}`">
                  <span v-if="file.status === 'created'">✓ Created</span>
                  <span v-else-if="file.status === 'modified'">✎ Modified</span>
                  <span v-else>✗ Deleted</span>
                </span>
              </div>
            </div>

            <div class="line-changes-summary">
              <span class="line-stats">
                <span v-if="file.lines_added >= 0" class="added"
                  >+{{ file.lines_added }} Added</span
                >
                <span v-if="file.lines_removed >= 0" class="removed"
                  >-{{ file.lines_removed }} Removed</span
                >
              </span>
            </div>

            <div v-if="file.summary" class="file-summary">
              {{ file.summary }}
            </div>

            <div v-if="file.diff" class="diff-section">
              <button
                class="expand-button"
                @click.stop="toggleDiff(file.path)"
                :title="
                  expandedDiffs.has(file.path) ? 'Collapse diff' : 'Expand diff'
                "
              >
                {{
                  expandedDiffs.has(file.path) ? "▼ Hide Diff" : "▶ Show Diff"
                }}
              </button>

              <div v-if="expandedDiffs.has(file.path)" class="diff-viewer">
                <pre><code class="language-diff" v-html="formatDiff(file.diff)"></code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Button (spans both columns) -->
      <div
        v-if="fileChanges.length > 0 || readFiles.length > 0"
        class="export-section full-width"
      >
        <button
          class="export-button"
          @click="exportFileActivity"
          title="Export file activity to JSON"
        >
          ⬇ Export File Activity
        </button>
      </div>
    </div>

    <!-- Default stacked layout (for backwards compatibility) -->
    <template v-else>
      <!-- Modified Files Section (Green/Yellow/Red) -->
      <div v-if="fileChanges.length > 0" class="modified-files-section">
        <div class="section-header">
          <span class="section-icon">📝</span>
          <span class="section-title">Produced</span>
          <span class="section-count">{{ fileChanges.length }} files</span>
        </div>

        <div class="file-cards-grid">
          <div
            v-for="file in fileChanges"
            :key="file.path"
            class="file-card modified-file-card"
            :class="`status-${file.status}`"
            @click="handleFileClick(file.absolute_path)"
            :title="`Click to open ${file.path} in IDE`"
          >
            <div class="file-header">
              <div class="file-path">{{ file.path }}</div>
              <div class="file-badges">
                <span class="status-badge" :class="`status-${file.status}`">
                  <span v-if="file.status === 'created'">✓ Created</span>
                  <span v-else-if="file.status === 'modified'">✎ Modified</span>
                  <span v-else>✗ Deleted</span>
                </span>
              </div>
            </div>

            <div class="line-changes-summary">
              <span class="line-stats">
                <span v-if="file.lines_added >= 0" class="added"
                  >+{{ file.lines_added }} Added</span
                >
                <span v-if="file.lines_removed >= 0" class="removed"
                  >-{{ file.lines_removed }} Removed</span
                >
              </span>
            </div>

            <div v-if="file.summary" class="file-summary">
              {{ file.summary }}
            </div>

            <div v-if="file.diff" class="diff-section">
              <button
                class="expand-button"
                @click.stop="toggleDiff(file.path)"
                :title="
                  expandedDiffs.has(file.path) ? 'Collapse diff' : 'Expand diff'
                "
              >
                {{
                  expandedDiffs.has(file.path) ? "▼ Hide Diff" : "▶ Show Diff"
                }}
              </button>

              <div v-if="expandedDiffs.has(file.path)" class="diff-viewer">
                <pre><code class="language-diff" v-html="formatDiff(file.diff)"></code></pre>
              </div>
            </div>

            <div class="file-open-icon" title="Open in IDE">📂</div>
          </div>
        </div>
      </div>

      <!-- Read Files Section (Blue) -->
      <div v-if="readFiles.length > 0" class="read-files-section">
        <div class="section-header">
          <span class="section-icon">📖</span>
          <span class="section-title">Consumed</span>
          <span class="section-count">{{ readFiles.length }} files</span>
        </div>

        <div class="file-cards-grid compact">
          <div
            v-for="file in readFiles"
            :key="file.path"
            class="file-card read-file-card"
            @click="handleFileClick(file.absolute_path)"
            :title="`Click to open ${file.path} in IDE\nRead for context`"
          >
            <div class="file-path">{{ file.path }}</div>
            <div class="line-count-badge">
              {{ formatLineCount(file.line_count) }} lines
            </div>
          </div>
        </div>
      </div>

      <!-- Export Button -->
      <div
        v-if="fileChanges.length > 0 || readFiles.length > 0"
        class="export-section"
      >
        <button
          class="export-button"
          @click="exportFileActivity"
          title="Export file activity to JSON"
        >
          ⬇ Export File Activity
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { FileChange, FileRead } from "@/types";
import { openFileInIDE } from "@/services/fileService";

const props = withDefaults(
  defineProps<{
    fileChanges: FileChange[];
    readFiles: FileRead[];
    layout?: "default" | "two-column";
  }>(),
  {
    layout: "default",
  }
);

const expandedDiffs = ref<Set<string>>(new Set());

const toggleDiff = (filePath: string) => {
  if (expandedDiffs.value.has(filePath)) {
    expandedDiffs.value.delete(filePath);
  } else {
    expandedDiffs.value.add(filePath);
  }
};

const handleFileClick = async (absolutePath: string) => {
  try {
    const result = await openFileInIDE(absolutePath);

    if (result.status === "success") {
      console.log("✓ File opened in IDE:", absolutePath);
    } else {
      console.error("✗ Failed to open file:", result.message);
      // Could show a toast notification here
    }
  } catch (error) {
    console.error("Failed to open file:", error);
  }
};

const formatLineCount = (count: number): string => {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
};

const formatDiff = (diff: string | undefined): string => {
  if (!diff) return "";

  // Escape HTML to prevent XSS
  const escapeHtml = (text: string) => {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  };

  // Split diff into lines and wrap each with appropriate styling
  const lines = diff.split("\n");
  const formattedLines = lines.map((line) => {
    const escapedLine = escapeHtml(line);

    // Addition line (starts with +)
    if (line.startsWith("+") && !line.startsWith("+++")) {
      return `<span class="addition">${escapedLine}</span>`;
    }

    // Deletion line (starts with -)
    if (line.startsWith("-") && !line.startsWith("---")) {
      return `<span class="deletion">${escapedLine}</span>`;
    }

    // Chunk header line (starts with @@)
    if (line.startsWith("@@")) {
      return `<span class="chunk-header">${escapedLine}</span>`;
    }

    // File header lines (+++ or ---)
    if (line.startsWith("+++") || line.startsWith("---")) {
      return `<span class="file-header">${escapedLine}</span>`;
    }

    // Context line (no special prefix)
    return escapedLine;
  });

  return formattedLines.join("\n");
};

const exportFileActivity = () => {
  const exportData = {
    timestamp: new Date().toISOString(),
    file_changes: props.fileChanges,
    read_files: props.readFiles,
    summary: {
      total_files_modified: props.fileChanges.length,
      total_files_read: props.readFiles.length,
    },
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `file-activity-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

// Note: Diff syntax highlighting is now handled by the formatDiff() function
// which parses diff lines and wraps them with appropriate CSS classes
</script>

<style scoped>
.file-changes-display {
  margin-top: var(--spacing-md, 1rem);
  padding: var(--spacing-md, 1rem);
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Two-column layout modifications */
.file-changes-display.layout-two-column {
  margin-top: 0;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
}

.layout-two-column .section-header {
  font-size: 0.9rem;
  margin-bottom: var(--spacing-sm, 0.5rem);
}

.layout-two-column .section-icon {
  font-size: 1.2rem;
}

.layout-two-column .section-count {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
}

.two-column-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg, 1.5rem);
  align-items: start;
}

.file-cards-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm, 0.5rem);
}

/* Remove backgrounds from two-column layout file cards */
.layout-two-column .file-card {
  background: transparent;
  padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
}

/* Consumed section: blue gradient left to dark */
.layout-two-column .read-file-card {
  background: linear-gradient(
    to right,
    rgba(6, 182, 212, 0.2),
    rgba(0, 0, 0, 0.1)
  );
  border-left-color: var(--status-info, #06b6d4);
  border-left-width: 3px;
  border-radius: 4px;
}

/* Produced section: color gradients based on status */
.layout-two-column .modified-file-card {
  border-left-width: 3px;
  border-radius: 4px;
}

/* Created: green gradient */
.layout-two-column .modified-file-card.status-created {
  background: linear-gradient(
    to right,
    rgba(16, 185, 129, 0.2),
    rgba(0, 0, 0, 0.1)
  );
  border-left-color: var(--status-success, #10b981);
}

/* Modified: yellow gradient */
.layout-two-column .modified-file-card.status-modified {
  background: linear-gradient(
    to right,
    rgba(251, 191, 36, 0.2),
    rgba(0, 0, 0, 0.1)
  );
  border-left-color: var(--status-warning, #fbbf24);
}

/* Deleted: red gradient */
.layout-two-column .modified-file-card.status-deleted {
  background: linear-gradient(
    to right,
    rgba(239, 68, 68, 0.2),
    rgba(0, 0, 0, 0.1)
  );
  border-left-color: var(--status-error, #ef4444);
}

/* Make sure file badges are visible */
.layout-two-column .file-badges {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-shrink: 0;
}

/* Ensure line stats are visible in two-column layout */
.layout-two-column .line-stats {
  display: flex;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.layout-two-column .line-stats .added,
.layout-two-column .line-stats .removed {
  font-weight: 600;
}

.export-section.full-width {
  grid-column: 1 / -1;
  margin-top: var(--spacing-md, 1rem);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 0.5rem);
  margin-bottom: var(--spacing-md, 1rem);
  font-size: 1.1rem;
  font-weight: 600;
}

.section-icon {
  font-size: 1.5rem;
}

.section-title {
  color: var(--text-primary, #e2e8f0);
}

.section-count {
  padding: 0.25rem 0.75rem;
  background: rgba(6, 182, 212, 0.2);
  color: var(--status-info, #06b6d4);
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
}

/* Modified Files Section */
.modified-files-section {
  margin-bottom: var(--spacing-lg, 1.5rem);
}

.file-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-md, 1rem);
}

.file-cards-grid.compact {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--spacing-sm, 0.5rem);
}

.file-card {
  position: relative;
  padding: var(--spacing-md, 1rem);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 4px solid;
}

.file-card:hover {
  transform: translateX(2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Modified file cards */
.modified-file-card {
  background: rgba(255, 255, 255, 0.05);
}

.modified-file-card.status-created {
  border-left-color: var(--status-success, #10b981);
}

.modified-file-card.status-modified {
  border-left-color: var(--status-warning, #f59e0b);
}

.modified-file-card.status-deleted {
  border-left-color: var(--status-error, #ef4444);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm, 0.5rem);
}

.file-path {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.9rem;
  color: var(--text-primary, #e2e8f0);
  word-break: break-all;
  flex: 1;
}

.file-badges {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  align-items: flex-end;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.status-created {
  background: rgba(16, 185, 129, 0.2);
  color: var(--status-success, #10b981);
}

.status-badge.status-modified {
  background: rgba(245, 158, 11, 0.2);
  color: var(--status-warning, #f59e0b);
}

.status-badge.status-deleted {
  background: rgba(239, 68, 68, 0.2);
  color: var(--status-error, #ef4444);
}

.line-stats {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.75rem;
  display: flex;
  gap: 0.5rem;
}

.line-stats .added {
  color: var(--status-success, #10b981);
}

.line-stats .removed {
  color: var(--status-error, #ef4444);
}

.file-summary {
  margin-top: var(--spacing-sm, 0.5rem);
  padding: var(--spacing-sm, 0.5rem);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--text-secondary, #94a3b8);
  font-style: italic;
}

.diff-section {
  margin-top: var(--spacing-sm, 0.5rem);
}

.expand-button {
  padding: 0.4rem 1rem;
  background: linear-gradient(
    135deg,
    rgba(6, 182, 212, 0.25),
    rgba(6, 182, 212, 0.15)
  );
  color: #22d3ee;
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.expand-button:hover {
  background: linear-gradient(
    135deg,
    rgba(6, 182, 212, 0.35),
    rgba(6, 182, 212, 0.25)
  );
  border-color: rgba(6, 182, 212, 0.7);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(6, 182, 212, 0.2);
}

.expand-button:active {
  transform: translateY(0);
}

.diff-viewer {
  margin-top: var(--spacing-md, 1rem);
  max-height: 600px;
  overflow: auto;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.5));
  border-radius: 8px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5), 0 4px 12px rgba(0, 0, 0, 0.3);
}

.diff-viewer pre {
  margin: 0;
  padding: var(--spacing-md, 1rem);
  font-family: "JetBrains Mono", "Consolas", monospace;
  font-size: 0.8rem;
  line-height: 1.3;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.diff-viewer code {
  color: var(--text-primary, #e2e8f0);
  display: block;
  white-space: pre-wrap;
  background: transparent;
}

/* ═══════════════════════════════════════════════════════════
   DIFF SYNTAX HIGHLIGHTING
   Style individual diff lines based on their prefix characters
   Git-style color coding for easy visual scanning
   ═══════════════════════════════════════════════════════════ */

/* Diff viewer: Style for added lines (green) */
.diff-viewer :deep(.addition),
.diff-viewer code :deep(.addition),
.diff-viewer pre code :deep(.addition) {
  background-color: rgba(16, 185, 129, 0.2) !important;
  color: #4ede80 !important;
  padding: 0.05rem 0.75rem !important;
  margin: 0 !important;
  border-left: 4px solid #22c55e !important;
  font-weight: 500 !important;
  text-shadow: 0 0 8px rgba(16, 185, 129, 0.1) !important;
  line-height: 1.3 !important;
}

/* Diff viewer: Style for deleted lines (red) */
.diff-viewer :deep(.deletion),
.diff-viewer code :deep(.deletion),
.diff-viewer pre code :deep(.deletion) {
  background-color: rgba(239, 68, 68, 0.2) !important;
  color: #fca5a5 !important;
  padding: 0.05rem 0.75rem !important;
  margin: 0 !important;
  border-left: 4px solid #dc2626 !important;
  font-weight: 500 !important;
  text-shadow: 0 0 8px rgba(239, 68, 68, 0.1) !important;
  line-height: 1.3 !important;
}

/* Diff viewer: Style for chunk headers (@@ lines) */
.diff-viewer :deep(.chunk-header),
.diff-viewer code :deep(.chunk-header),
.diff-viewer pre code :deep(.chunk-header) {
  display: block !important;
  background-color: rgba(59, 130, 246, 0.15) !important;
  color: #60a5fa !important;
  padding: 0.2rem 0.75rem !important;
  margin: 0.4rem 0 0.2rem 0 !important;
  border-left: 4px solid #3b82f6 !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  border-top: 1px solid rgba(59, 130, 246, 0.2) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  line-height: 1.3 !important;
}

/* Diff viewer: Style for file headers (+++ and ---) */
.diff-viewer :deep(.file-header),
.diff-viewer code :deep(.file-header),
.diff-viewer pre code :deep(.file-header) {
  display: block !important;
  color: var(--text-muted, #9ca3af) !important;
  padding: 0.05rem 0.75rem !important;
  margin: 0 !important;
  font-style: italic !important;
  opacity: 0.85 !important;
  font-size: 0.75rem !important;
  background-color: rgba(255, 255, 255, 0.02) !important;
  border-left: 4px solid rgba(255, 255, 255, 0.1) !important;
  line-height: 1.3 !important;
}

/* Hover effect on diff lines for better interaction */
.diff-viewer :deep(.addition:hover) {
  background-color: rgba(16, 185, 129, 0.3) !important;
  cursor: text;
  box-shadow: inset 0 0 8px rgba(16, 185, 129, 0.1);
}

.diff-viewer :deep(.deletion:hover) {
  background-color: rgba(239, 68, 68, 0.3) !important;
  cursor: text;
  box-shadow: inset 0 0 8px rgba(239, 68, 68, 0.1);
}

.diff-viewer :deep(.chunk-header:hover) {
  background-color: rgba(59, 130, 246, 0.18) !important;
}

/* Selection styling for copying diff content */
.diff-viewer ::selection {
  background-color: rgba(6, 182, 212, 0.3);
  color: var(--text-primary, #ffffff);
}

/* Scrollbar styling for diff viewer - enhanced for better visibility */
.diff-viewer::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.diff-viewer::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 0 8px 8px 0;
  margin-right: 2px;
}

.diff-viewer::-webkit-scrollbar-thumb {
  background: linear-gradient(
    180deg,
    rgba(6, 182, 212, 0.4),
    rgba(6, 182, 212, 0.3)
  );
  border-radius: 6px;
  border: 3px solid transparent;
  background-clip: padding-box;
  transition: all 0.2s ease;
}

.diff-viewer::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(
    180deg,
    rgba(6, 182, 212, 0.6),
    rgba(6, 182, 212, 0.5)
  );
  background-clip: padding-box;
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);
}

.file-open-icon {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  font-size: 1.2rem;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.file-card:hover .file-open-icon {
  opacity: 1;
}

/* Read Files Section */
.read-files-section {
}

.read-file-card {
  background: rgba(59, 130, 246, 0.1);
  border-left-color: var(--status-info, #3b82f6);
  padding: var(--spacing-sm, 0.5rem) var(--spacing-md, 1rem);
}

.read-file-card:hover {
  background: rgba(59, 130, 246, 0.15);
}

.read-file-card .file-path {
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}

.line-count-badge {
  color: var(--status-info, #3b82f6);
  font-size: 0.75rem;
  font-weight: 600;
  font-family: "JetBrains Mono", monospace;
}

/* Export Section */
.export-section {
  margin-top: var(--spacing-md, 1rem);
  display: flex;
  justify-content: flex-end;
}

.export-button {
  padding: 0.5rem 1rem;
  background: rgba(6, 182, 212, 0.2);
  color: var(--status-info, #06b6d4);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s;
}

.export-button:hover {
  background: rgba(6, 182, 212, 0.3);
  transform: translateY(-1px);
}
</style>
