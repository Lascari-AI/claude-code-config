// Products store
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Product, HomeSection } from '../types';
import api from '../services/api';

export const useProductsStore = defineStore('products', () => {
  const products = ref<Product[]>([]);
  const homeSections = ref<HomeSection[]>([]);
  const isPersonalized = ref(false);
  const categories = ref<string[]>([]);
  const searchResults = ref<Product[]>([]);
  const loading = ref(false);
  const streaming = ref(false);  // New: streaming in progress
  const error = ref<string | null>(null);

  // Timer state for home page load
  const loadStartTime = ref<number | null>(null);
  const loadDuration = ref<number | null>(null);

  // WebSocket reference
  let ws: WebSocket | null = null;

  async function fetchProducts(params?: {
    category?: string;
    brand?: string;
    limit?: number;
  }) {
    loading.value = true;
    error.value = null;
    try {
      products.value = await api.getProducts(params);
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch products';
    } finally {
      loading.value = false;
    }
  }

  // OLD: HTTP fetch (kept for fallback)
  async function fetchHomePage() {
    loading.value = true;
    error.value = null;
    loadStartTime.value = Date.now();
    loadDuration.value = null;
    try {
      const response = await api.getHomePage();
      homeSections.value = response.sections;
      isPersonalized.value = response.is_personalized;
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch home page';
    } finally {
      if (loadStartTime.value) {
        loadDuration.value = Date.now() - loadStartTime.value;
      }
      loading.value = false;
    }
  }

  // NEW: WebSocket streaming - sections appear as they're generated
  function fetchHomePageStreaming(userId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      // Reset state
      homeSections.value = [];
      isPersonalized.value = false;
      loading.value = true;
      streaming.value = true;
      error.value = null;
      loadStartTime.value = Date.now();
      loadDuration.value = null;

      // Build WebSocket URL - handle both dev proxy and direct
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/home/${userId}`;

      console.log('[HomeStream] Connecting to:', wsUrl);

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[HomeStream] Connected, sending start...');
        ws?.send(JSON.stringify({ action: 'start' }));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[HomeStream] Received:', message.type, message.data?.component_type || '');

          if (message.type === 'section') {
            // Append section immediately - user sees it right away!
            homeSections.value = [...homeSections.value, message.data];
            isPersonalized.value = true;
            // First section arrived - no longer "loading" (but still streaming)
            if (homeSections.value.length === 1) {
              loading.value = false;
            }
          } else if (message.type === 'complete') {
            // All sections received
            streaming.value = false;
            loading.value = false;
            if (loadStartTime.value) {
              loadDuration.value = Date.now() - loadStartTime.value;
            }
            console.log('[HomeStream] Complete!', homeSections.value.length, 'sections');
            ws?.close();
            resolve();
          } else if (message.type === 'error') {
            error.value = message.data?.message || 'Streaming error';
            streaming.value = false;
            loading.value = false;
            ws?.close();
            reject(new Error(error.value));
          } else if (message.type === 'ping') {
            // Keep-alive, ignore
          }
        } catch (e) {
          console.error('[HomeStream] Parse error:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('[HomeStream] WebSocket error:', event);
        error.value = 'WebSocket connection failed';
        streaming.value = false;
        loading.value = false;
        reject(new Error('WebSocket error'));
      };

      ws.onclose = (event) => {
        console.log('[HomeStream] Closed:', event.code, event.reason);
        streaming.value = false;
        if (loading.value) {
          // Closed before complete - might be an error
          loading.value = false;
        }
      };
    });
  }

  // Cleanup WebSocket on unmount
  function closeStreaming() {
    if (ws) {
      ws.close();
      ws = null;
    }
    streaming.value = false;
  }

  async function fetchCategories() {
    try {
      categories.value = await api.getCategories();
    } catch (e: any) {
      console.error('Failed to fetch categories:', e);
    }
  }

  async function search(query: string) {
    loading.value = true;
    error.value = null;
    try {
      searchResults.value = await api.searchProducts(query);
    } catch (e: any) {
      error.value = e.message || 'Search failed';
    } finally {
      loading.value = false;
    }
  }

  return {
    products,
    homeSections,
    isPersonalized,
    categories,
    searchResults,
    loading,
    streaming,  // New: streaming in progress
    error,
    // Timer state
    loadStartTime,
    loadDuration,
    // Methods
    fetchProducts,
    fetchHomePage,
    fetchHomePageStreaming,  // New: WebSocket streaming
    closeStreaming,          // New: cleanup
    fetchCategories,
    search
  };
});
