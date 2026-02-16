<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import api from '../../services/api';
import type { SearchSuggestion } from '../../types';

const router = useRouter();
const query = ref('');
const suggestions = ref<SearchSuggestion[]>([]);
const showSuggestions = ref(false);
const loading = ref(false);
let debounceTimer: ReturnType<typeof setTimeout>;

async function fetchSuggestions() {
  if (query.value.length < 2) {
    suggestions.value = [];
    return;
  }

  loading.value = true;
  try {
    const result = await api.getSearchAutocomplete(query.value);
    suggestions.value = result.suggestions;
  } catch (e) {
    console.error('Failed to fetch suggestions:', e);
  } finally {
    loading.value = false;
  }
}

watch(query, () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchSuggestions, 300);
});

function handleSearch() {
  if (query.value.trim()) {
    router.push({ path: '/', query: { search: query.value } });
    showSuggestions.value = false;
  }
}

function selectSuggestion(suggestion: SearchSuggestion) {
  router.push(`/product/${suggestion.product_id}`);
  query.value = '';
  showSuggestions.value = false;
}

function handleBlur() {
  // Delay to allow click on suggestion
  setTimeout(() => {
    showSuggestions.value = false;
  }, 200);
}
</script>

<template>
  <div class="search-container">
    <div class="search-input-wrapper">
      <input
        v-model="query"
        type="text"
        placeholder="Search products..."
        class="search-input"
        @focus="showSuggestions = true"
        @blur="handleBlur"
        @keydown.enter="handleSearch"
      />
      <button class="search-btn" @click="handleSearch">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
      </button>
    </div>

    <Transition name="fade">
      <div v-if="showSuggestions && (suggestions.length > 0 || loading)" class="suggestions">
        <div v-if="loading" class="loading-suggestions">
          <span class="spinner-small"></span>
          Finding products just for you...
        </div>
        <div
          v-else
          v-for="suggestion in suggestions"
          :key="suggestion.product_id"
          class="suggestion-item"
          @click="selectSuggestion(suggestion)"
        >
          <span class="suggestion-text">{{ suggestion.text }}</span>
          <span class="suggestion-category">{{ suggestion.category }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.search-container {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  display: flex;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.search-input-wrapper:focus-within {
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 2px rgba(255, 153, 0, 0.3);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 0.75rem 1rem;
  color: white;
  font-size: 0.95rem;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-input:focus {
  outline: none;
}

.search-btn {
  background: #ff9900;
  border: none;
  padding: 0.75rem 1rem;
  color: #1a1a2e;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  background: #ffaa22;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  margin-top: 0.5rem;
  overflow: hidden;
  z-index: 50;
}

.loading-suggestions {
  padding: 1rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.suggestion-item {
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s;
}

.suggestion-item:hover {
  background: #f5f7fa;
}

.suggestion-text {
  color: #1a1a2e;
  font-weight: 500;
}

.suggestion-category {
  font-size: 0.75rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
