<script setup lang="ts">
import { onMounted, ref, onUnmounted, markRaw, type Component } from 'vue';
import { useRouter } from 'vue-router';
import { useProductsStore } from '../stores/products';
import { useCartStore } from '../stores/cart';
import { useExpertiseStore } from '../stores/expertise';
import api from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner.vue';
import GenericSlogan from '../components/products/GenericSlogan.vue';
import SpecificSlogan from '../components/products/SpecificSlogan.vue';
import SpecificUpsell from '../components/products/SpecificUpsell.vue';
import BasicSquare from '../components/products/BasicSquare.vue';
import ProductCarousel from '../components/products/ProductCarousel.vue';
import ProductCard from '../components/products/ProductCard.vue';
import SuperCard from '../components/products/SuperCard.vue';
import type { ComponentType } from '../types';

const router = useRouter();
const productsStore = useProductsStore();
const cartStore = useCartStore();
const expertiseStore = useExpertiseStore();

// Live timer state
const elapsedTime = ref<number>(0);
let timerInterval: ReturnType<typeof setInterval> | null = null;

// Start the live timer
function startTimer() {
  elapsedTime.value = 0;
  timerInterval = setInterval(() => {
    if (productsStore.loadStartTime) {
      elapsedTime.value = Date.now() - productsStore.loadStartTime;
    }
  }, 100);
}

// Stop the timer
function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

// Format milliseconds to readable string
function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  const seconds = (ms / 1000).toFixed(1);
  return `${seconds}s`;
}

// Component map for dynamic rendering
const componentMap: Record<ComponentType, Component> = {
  'generic-slogan': markRaw(GenericSlogan),
  'specific-slogan': markRaw(SpecificSlogan),
  'specific-upsell': markRaw(SpecificUpsell),
  'basic-square': markRaw(BasicSquare),
  'carousel': markRaw(ProductCarousel),
  'card': markRaw(ProductCard),
  'super-card': markRaw(SuperCard)
};

function getComponent(type: ComponentType): Component {
  return componentMap[type] || GenericSlogan;
}

function handleViewProduct(productId: number) {
  router.push(`/product/${productId}`);
}

async function handleAddToCart(productId: number) {
  try {
    await cartStore.addItem(productId);
  } catch (e) {
    console.error('Failed to add to cart:', e);
  }
}

onMounted(async () => {
  // Start timer before fetching
  startTimer();

  // Fetch expertise and cart in parallel
  await Promise.all([
    expertiseStore.fetchExpertise(),
    cartStore.fetchCart()
  ]);

  // Use WebSocket streaming for home page - sections appear progressively!
  const userId = api.getUserId();
  if (userId) {
    try {
      await productsStore.fetchHomePageStreaming(userId);
    } catch (e) {
      console.warn('[HomeView] Streaming failed, falling back to HTTP:', e);
      // Fallback to HTTP if WebSocket fails
      await productsStore.fetchHomePage();
    }
  } else {
    // No user ID - use HTTP fallback
    await productsStore.fetchHomePage();
  }

  // Stop timer after fetch completes
  stopTimer();

  // Log the REUSE phase when home page is personalized by the agent
  if (productsStore.isPersonalized && productsStore.homeSections.length) {
    expertiseStore.logReuse(productsStore.homeSections.length, productsStore.isPersonalized);
  }
});

onUnmounted(() => {
  stopTimer();
  productsStore.closeStreaming();  // Cleanup WebSocket
});
</script>

<template>
  <div class="home-page">
    <!-- Loading State with Timer (before first section arrives) -->
    <div v-if="productsStore.loading && !productsStore.homeSections.length" class="loading-container">
      <LoadingSpinner message="Agent is building your personalized experience..." />
      <div class="loading-timer">
        <span class="timer-value">{{ formatDuration(elapsedTime) }}</span>
      </div>
    </div>

    <!-- Show sections as they stream in -->
    <template v-if="productsStore.homeSections.length">
      <!-- Streaming indicator while more sections coming -->
      <div
        v-if="productsStore.streaming"
        class="streaming-indicator"
      >
        <span class="streaming-pulse"></span>
        Streaming sections... {{ productsStore.homeSections.length }} received
        <span class="timer-badge">⏱️ {{ formatDuration(elapsedTime) }}</span>
      </div>

      <!-- Personalization indicator (shown after streaming completes) -->
      <div
        v-else-if="productsStore.isPersonalized"
        class="personalization-indicator"
      >
        <span class="pulse"></span>
        Personalized experience based on {{ expertiseStore.totalImprovements }} interactions
        <span v-if="productsStore.loadDuration" class="load-time-badge">
          ⏱️ {{ formatDuration(productsStore.loadDuration) }}
        </span>
      </div>

      <!-- Render sections with fade-in animation -->
      <div
        v-for="(section, index) in productsStore.homeSections"
        :key="index"
        class="section section-fade-in"
      >
        <component
          :is="getComponent(section.component_type)"
          v-bind="section"
          @view-product="handleViewProduct"
          @add-to-cart="handleAddToCart"
        />
      </div>
    </template>

    <div v-else-if="!productsStore.loading" class="empty-state">
      <p>No products available. Please try again later.</p>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* Loading Container with Timer */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1.5rem;
}

.loading-timer {
  text-align: center;
}

.timer-value {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 2.5rem;
  font-weight: 700;
  color: #ff9900;
  text-shadow: 0 0 20px rgba(255, 153, 0, 0.3);
}

.personalization-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  padding: 0.75rem 1.25rem;
  border-radius: 30px;
  margin-bottom: 2rem;
  font-size: 0.9rem;
  color: #059669;
  font-weight: 500;
}

.load-time-badge {
  background: rgba(255, 153, 0, 0.15);
  border: 1px solid rgba(255, 153, 0, 0.3);
  color: #d97706;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
  margin-left: 0.5rem;
}

.pulse {
  width: 10px;
  height: 10px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
}

.section {
  margin-bottom: 1rem;
}

/* Fade-in animation for streamed sections */
.section-fade-in {
  animation: fadeSlideIn 0.4s ease-out;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Streaming indicator */
.streaming-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  padding: 0.75rem 1.25rem;
  border-radius: 30px;
  margin-bottom: 2rem;
  font-size: 0.9rem;
  color: #3b82f6;
  font-weight: 500;
}

.streaming-pulse {
  width: 10px;
  height: 10px;
  background: #3b82f6;
  border-radius: 50%;
  animation: streamPulse 0.8s ease-in-out infinite;
}

@keyframes streamPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.6;
  }
}

.timer-badge {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #2563eb;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
  margin-left: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}
</style>
