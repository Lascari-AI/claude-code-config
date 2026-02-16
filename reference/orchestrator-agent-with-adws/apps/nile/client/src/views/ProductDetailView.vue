<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../services/api';
import { useCartStore } from '../stores/cart';
import { useExpertiseStore } from '../stores/expertise';
import LoadingSpinner from '../components/common/LoadingSpinner.vue';
import type { Product } from '../types';

const route = useRoute();
const router = useRouter();
const cartStore = useCartStore();
const expertiseStore = useExpertiseStore();

const product = ref<Product | null>(null);
const loading = ref(true);
const error = ref('');
const quantity = ref(1);
const addingToCart = ref(false);

const productId = computed(() => Number(route.params.id));

async function fetchProduct() {
  loading.value = true;
  error.value = '';
  try {
    product.value = await api.getProduct(productId.value);
    // Track view action with product name for better logging
    await expertiseStore.trackView(productId.value, product.value.name);
  } catch (e: any) {
    error.value = e.message || 'Failed to load product';
  } finally {
    loading.value = false;
  }
}

async function addToCart() {
  if (!product.value) return;
  addingToCart.value = true;
  try {
    // Track add to cart for expertise (ACT → LEARN)
    await expertiseStore.trackAddToCart(product.value.id, product.value.name);
    await cartStore.addItem(product.value.id, quantity.value);
    quantity.value = 1;
    // Navigate to cart page after successful add
    router.push('/cart');
  } catch (e) {
    console.error('Failed to add to cart:', e);
  } finally {
    addingToCart.value = false;
  }
}

function goBack() {
  router.back();
}

onMounted(fetchProduct);
</script>

<template>
  <div class="product-detail-page">
    <button class="back-btn" @click="goBack">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m15 18-6-6 6-6"/>
      </svg>
      Back
    </button>

    <LoadingSpinner v-if="loading" />

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="fetchProduct">Try Again</button>
    </div>

    <div v-else-if="product" class="product-container">
      <div class="product-image-section">
        <img :src="product.image_file_path" :alt="product.name" class="main-image" />
        <span class="shipping-badge">{{ product.shipping_speed }} shipping</span>
      </div>

      <div class="product-info-section">
        <div class="breadcrumb">
          <span>{{ product.category }}</span>
          <span class="separator">›</span>
          <span>{{ product.brand }}</span>
        </div>

        <h1 class="product-name">{{ product.name }}</h1>

        <div class="rating-row">
          <div class="rating">
            <span class="stars">★★★★★</span>
            <span class="rating-value">{{ product.rating.toFixed(1) }}</span>
          </div>
          <span class="reviews-count">{{ product.reviews?.length || 0 }} reviews</span>
        </div>

        <p class="price">${{ product.price.toFixed(2) }}</p>

        <p class="description">{{ product.description }}</p>

        <div class="action-section">
          <div class="quantity-selector">
            <button @click="quantity = Math.max(1, quantity - 1)">-</button>
            <span>{{ quantity }}</span>
            <button @click="quantity++">+</button>
          </div>
          <button
            class="add-to-cart-btn"
            @click="addToCart"
            :disabled="addingToCart"
          >
            <span v-if="addingToCart" class="spinner-small"></span>
            <span v-else>Add to Cart</span>
          </button>
        </div>

        <div class="specs">
          <div class="spec-item">
            <span class="spec-label">Category</span>
            <span class="spec-value">{{ product.category }}</span>
          </div>
          <div class="spec-item">
            <span class="spec-label">Brand</span>
            <span class="spec-value">{{ product.brand }}</span>
          </div>
          <div class="spec-item">
            <span class="spec-label">Shipping</span>
            <span class="spec-value">{{ product.shipping_speed }}</span>
          </div>
        </div>
      </div>

      <div v-if="product.reviews?.length" class="reviews-section">
        <h2>Customer Reviews</h2>
        <div class="reviews-list">
          <div v-for="review in product.reviews" :key="review.id" class="review-card">
            <div class="review-header">
              <span class="reviewer-name">{{ review.reviewer_name }}</span>
              <span class="review-rating">
                {{ '★'.repeat(review.rating) }}{{ '☆'.repeat(5 - review.rating) }}
              </span>
            </div>
            <p class="review-text">{{ review.review_text }}</p>
            <span class="review-date">{{ review.review_date }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: none;
  color: #6b7280;
  font-size: 0.95rem;
  cursor: pointer;
  margin-bottom: 1.5rem;
  transition: color 0.2s;
}

.back-btn:hover {
  color: #1a1a2e;
}

.error-state {
  text-align: center;
  padding: 4rem;
}

.product-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
}

.product-image-section {
  position: relative;
}

.main-image {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.shipping-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #10b981;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.product-info-section {
  display: flex;
  flex-direction: column;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.separator {
  color: #d1d5db;
}

.product-name {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1rem;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stars {
  color: #f59e0b;
}

.rating-value {
  font-weight: 600;
}

.reviews-count {
  color: #6b7280;
  font-size: 0.9rem;
}

.price {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.description {
  color: #4b5563;
  line-height: 1.7;
  margin-bottom: 2rem;
}

.action-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.quantity-selector {
  display: flex;
  align-items: center;
  gap: 0;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}

.quantity-selector button {
  background: #f5f7fa;
  border: none;
  width: 45px;
  height: 45px;
  font-size: 1.25rem;
  cursor: pointer;
  transition: background 0.2s;
}

.quantity-selector button:hover {
  background: #e5e7eb;
}

.quantity-selector span {
  width: 50px;
  text-align: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.add-to-cart-btn {
  flex: 1;
  background: linear-gradient(135deg, #ff9900 0%, #ffaa22 100%);
  color: #1a1a2e;
  border: none;
  padding: 0 2rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.add-to-cart-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 153, 0, 0.4);
}

.add-to-cart-btn:disabled {
  opacity: 0.7;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(26, 26, 46, 0.2);
  border-top-color: #1a1a2e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.specs {
  display: flex;
  gap: 2rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
}

.spec-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.spec-label {
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.spec-value {
  font-weight: 600;
  color: #1a1a2e;
}

.reviews-section {
  grid-column: 1 / -1;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.reviews-section h2 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  color: #1a1a2e;
}

.reviews-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.review-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.reviewer-name {
  font-weight: 600;
  color: #1a1a2e;
}

.review-rating {
  color: #f59e0b;
}

.review-text {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.review-date {
  font-size: 0.8rem;
  color: #9ca3af;
}

@media (max-width: 900px) {
  .product-container {
    grid-template-columns: 1fr;
  }
}
</style>
