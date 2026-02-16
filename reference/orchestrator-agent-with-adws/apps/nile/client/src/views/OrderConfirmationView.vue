<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../services/api';
import type { OrderResponse } from '../types';

const route = useRoute();
const router = useRouter();

const order = ref<OrderResponse | null>(null);
const loading = ref(true);
const error = ref('');

async function fetchOrder() {
  loading.value = true;
  try {
    const orderId = route.params.orderId as string;
    order.value = await api.getOrder(orderId);
  } catch (e: any) {
    error.value = e.message || 'Failed to load order';
  } finally {
    loading.value = false;
  }
}

function continueShopping() {
  router.push('/');
}

function viewOrders() {
  router.push('/orders');
}

onMounted(fetchOrder);
</script>

<template>
  <div class="confirmation-page">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="continueShopping">Go Home</button>
    </div>

    <div v-else-if="order" class="confirmation-content">
      <div class="success-header">
        <div class="success-icon">✓</div>
        <h1>Order Confirmed!</h1>
        <p class="order-id">Order #{{ order.order_id }}</p>
      </div>

      <div class="order-details">
        <h2>Order Details</h2>
        <div class="items-list">
          <div v-for="item in order.items" :key="item.id" class="order-item">
            <img :src="item.product.image_file_path" :alt="item.product.name" class="item-image" />
            <div class="item-info">
              <h3>{{ item.product.name }}</h3>
              <p class="brand">{{ item.product.brand }}</p>
              <p class="quantity">Qty: {{ item.quantity }}</p>
            </div>
            <p class="item-price">${{ (item.price_at_purchase * item.quantity).toFixed(2) }}</p>
          </div>
        </div>

        <div class="order-total">
          <span>Total</span>
          <span>${{ order.total_price.toFixed(2) }}</span>
        </div>
      </div>

      <div class="actions">
        <button class="primary-btn" @click="continueShopping">
          Continue Shopping
        </button>
        <button class="secondary-btn" @click="viewOrders">
          View All Orders
        </button>
      </div>

      <div class="expertise-reminder">
        <p>
          <strong>Tip:</strong> Press <kbd>Ctrl+K</kbd> to see how your purchase has improved the Agent Expert's understanding of your preferences!
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirmation-page {
  max-width: 700px;
  margin: 0 auto;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  text-align: center;
  padding: 4rem;
}

.confirmation-content {
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.success-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  padding: 3rem 2rem;
  text-align: center;
  color: white;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: white;
  color: #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
  margin: 0 auto 1.5rem;
}

.success-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.order-id {
  opacity: 0.9;
  font-size: 0.95rem;
}

.order-details {
  padding: 2rem;
}

.order-details h2 {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.order-item:last-child {
  border-bottom: none;
}

.item-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
}

.item-info {
  flex: 1;
}

.item-info h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.brand {
  font-size: 0.85rem;
  color: #6b7280;
}

.quantity {
  font-size: 0.85rem;
  color: #6b7280;
}

.item-price {
  font-weight: 700;
  color: #1a1a2e;
}

.order-total {
  display: flex;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 2px solid #e5e7eb;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}

.actions {
  padding: 0 2rem 2rem;
  display: flex;
  gap: 1rem;
}

.primary-btn {
  flex: 1;
  background: linear-gradient(135deg, #ff9900 0%, #ffaa22 100%);
  color: #1a1a2e;
  border: none;
  padding: 1rem;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 153, 0, 0.4);
}

.secondary-btn {
  flex: 1;
  background: transparent;
  border: 2px solid #e5e7eb;
  color: #6b7280;
  padding: 1rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  border-color: #0066cc;
  color: #0066cc;
}

.expertise-reminder {
  background: #f0fdf4;
  padding: 1.5rem 2rem;
  border-top: 1px solid #bbf7d0;
}

.expertise-reminder p {
  color: #166534;
  font-size: 0.9rem;
  text-align: center;
}

kbd {
  background: #dcfce7;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}
</style>
