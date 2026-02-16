// Expertise store - Agent Expert Mental Model
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Expertise } from '../types';
import api from '../services/api';

// Action log entry for the ACT → LEARN → REUSE cycle visibility
interface ActionLogEntry {
  timestamp: Date;
  phase: 'ACT' | 'LEARN' | 'REUSE';
  action: string;
  productId?: number;
  productName?: string;
  details: string;
}

// Live system prompt data from the backend
interface LiveSystemPrompt {
  system_prompt: string;
  user_prompt: string;
  total_improvements: number;
  prefetched_products: {
    checked_out: any[];
    added_to_cart: any[];
    viewed_products: any[];
  };
}

export const useExpertiseStore = defineStore('expertise', () => {
  const expertise = ref<Expertise | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const panelOpen = ref(false);
  const showSystemPrompt = ref(false);

  // Live system prompt state
  const liveSystemPrompt = ref<LiveSystemPrompt | null>(null);
  const systemPromptLoading = ref(false);
  const systemPromptError = ref<string | null>(null);

  // Action log to show the ACT → LEARN → REUSE cycle
  const actionLog = ref<ActionLogEntry[]>([]);
  const maxLogEntries = 20;

  const totalImprovements = computed(() => expertise.value?.total_improvements ?? 0);
  const expertiseData = computed(() => expertise.value?.expertise_data ?? {
    viewed_products: [],
    added_to_cart: [],
    checked_out: []
  });

  // Add entry to action log
  function logAction(entry: Omit<ActionLogEntry, 'timestamp'>) {
    actionLog.value.unshift({
      ...entry,
      timestamp: new Date()
    });
    // Keep log size manageable
    if (actionLog.value.length > maxLogEntries) {
      actionLog.value = actionLog.value.slice(0, maxLogEntries);
    }
  }

  async function fetchExpertise() {
    loading.value = true;
    error.value = null;
    try {
      expertise.value = await api.getExpertise();
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch expertise';
    } finally {
      loading.value = false;
    }
  }

  async function fetchLiveSystemPrompt() {
    systemPromptLoading.value = true;
    systemPromptError.value = null;
    try {
      liveSystemPrompt.value = await api.getLiveSystemPrompt();
    } catch (e: any) {
      systemPromptError.value = e.message || 'Failed to fetch live system prompt';
    } finally {
      systemPromptLoading.value = false;
    }
  }

  async function trackView(productId: number, productName?: string) {
    try {
      // Log the ACT phase
      logAction({
        phase: 'ACT',
        action: 'view_product_details',
        productId,
        productName,
        details: `User viewed product: ${productName || `#${productId}`}`
      });

      await api.trackAction('view_product_details', productId);

      // Log the LEARN phase
      logAction({
        phase: 'LEARN',
        action: 'expertise_updated',
        productId,
        productName,
        details: `Agent learned: User interested in ${productName || `product #${productId}`}`
      });

      await fetchExpertise();
    } catch (e) {
      console.error('Failed to track view:', e);
    }
  }

  async function trackAddToCart(productId: number, productName?: string) {
    try {
      // Log the ACT phase
      logAction({
        phase: 'ACT',
        action: 'add_to_cart',
        productId,
        productName,
        details: `User added to cart: ${productName || `#${productId}`}`
      });

      await api.trackAction('add_to_cart', productId);

      // Log the LEARN phase
      logAction({
        phase: 'LEARN',
        action: 'expertise_updated',
        productId,
        productName,
        details: `Agent learned: Strong intent signal for ${productName || `product #${productId}`}`
      });

      await fetchExpertise();
    } catch (e) {
      console.error('Failed to track add to cart:', e);
    }
  }

  async function trackCheckout(productIds: number[]) {
    try {
      // Log the ACT phase
      logAction({
        phase: 'ACT',
        action: 'checkout',
        details: `User purchased ${productIds.length} item(s)`
      });

      for (const productId of productIds) {
        await api.trackAction('checkout', productId);
      }

      // Log the LEARN phase
      logAction({
        phase: 'LEARN',
        action: 'expertise_updated',
        details: `Agent learned: Highest signal - purchase confirms preferences`
      });

      await fetchExpertise();
    } catch (e) {
      console.error('Failed to track checkout:', e);
    }
  }

  // Log when home page uses expertise (REUSE phase)
  function logReuse(sectionCount: number, isPersonalized: boolean) {
    if (isPersonalized) {
      logAction({
        phase: 'REUSE',
        action: 'home_page_personalized',
        details: `Agent generated ${sectionCount} personalized sections using expertise`
      });
    }
  }

  async function clearExpertise() {
    loading.value = true;
    error.value = null;
    try {
      await api.clearExpertise();
      expertise.value = null;
      actionLog.value = [];
      logAction({
        phase: 'ACT',
        action: 'expertise_cleared',
        details: 'User cleared all expertise - Agent reset to fresh state'
      });
      await fetchExpertise();
    } catch (e: any) {
      error.value = e.message || 'Failed to clear expertise';
    } finally {
      loading.value = false;
    }
  }

  function togglePanel() {
    panelOpen.value = !panelOpen.value;
  }

  function closePanel() {
    panelOpen.value = false;
  }

  function toggleSystemPrompt() {
    showSystemPrompt.value = !showSystemPrompt.value;
  }

  return {
    expertise,
    loading,
    error,
    panelOpen,
    showSystemPrompt,
    actionLog,
    totalImprovements,
    expertiseData,
    // Live system prompt state
    liveSystemPrompt,
    systemPromptLoading,
    systemPromptError,
    // Methods
    fetchExpertise,
    fetchLiveSystemPrompt,
    trackView,
    trackAddToCart,
    trackCheckout,
    logReuse,
    clearExpertise,
    togglePanel,
    closePanel,
    toggleSystemPrompt
  };
});
