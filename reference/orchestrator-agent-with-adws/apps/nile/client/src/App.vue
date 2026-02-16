<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useUserStore } from './stores/user';
import { useExpertiseStore } from './stores/expertise';
import AppHeader from './components/layout/AppHeader.vue';
import ExpertisePanel from './components/layout/ExpertisePanel.vue';

const userStore = useUserStore();
const expertiseStore = useExpertiseStore();

// Keyboard shortcuts
function handleKeydown(e: KeyboardEvent) {
  // Ctrl+K to toggle expertise panel
  if (e.ctrlKey && e.key === 'k') {
    e.preventDefault();
    expertiseStore.togglePanel();
  }
  // Cmd/Ctrl+Shift+C to clear expertise
  if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'C') {
    e.preventDefault();
    expertiseStore.clearExpertise();
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div class="app">
    <AppHeader v-if="userStore.isLoggedIn" />
    <main class="main-content">
      <router-view />
    </main>
    <ExpertisePanel v-if="userStore.isLoggedIn" />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #0066cc;
  --primary-dark: #004c99;
  --secondary: #ff9900;
  --background: #f5f7fa;
  --surface: #ffffff;
  --text: #1a1a2e;
  --text-light: #6b7280;
  --border: #e5e7eb;
  --success: #10b981;
  --error: #ef4444;
  --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--background);
  color: var(--text);
  line-height: 1.6;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* Utility classes */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--secondary);
  color: var(--text);
}

.btn-secondary:hover {
  filter: brightness(1.1);
}

.btn-outline {
  background: transparent;
  border: 2px solid var(--border);
  color: var(--text);
}

.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.card {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

/* Loading spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
