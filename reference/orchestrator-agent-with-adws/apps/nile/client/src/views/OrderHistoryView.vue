<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner.vue';
import type { OrderResponse } from '../types';

const router = useRouter();

const orders = ref<OrderResponse[]>([]);
const loading = ref(true);
const error = ref('');

async function fetchOrders() {
  loading.value = true;
  try {
    orders.value = await api.getOrders();
  } catch (e: any) {
    error.value = e.message || 'Failed to load orders';
  } finally {
    loading.value = false;
  }
}

function goToProduct(productId: number) {
  router.push(`/product/${productId}`);
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

onMounted(fetchOrders);
</script>

<template>
  <div class="orders-page">
    <h1>Order History</h1>

    <LoadingSpinner v-if="loading" />

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="fetchOrders">Try Again</button>
    </div>

    <div v-else-if="orders.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <h2>No orders yet</h2>
      <p>Start shopping to see your orders here.</p>
      <router-link to="/" class="btn btn-primary">Start Shopping</router-link>
    </div>

    <div v-else class="orders-list">
      <div v-for="order in orders" :key="order.order_id" class="order-card">
        <div class="order-header">
          <div class="order-info">
            <h3>Order #{{ order.order_id }}</h3>
            <p class="order-date">{{ formatDate(order.created_at) }}</p>
          </div>
          <div class="order-total">
            <span class="label">Total</span>
            <span class="amount">${{ order.total_price.toFixed(2) }}</span>
          </div>
        </div>
        <div class="order-items">
          <div
            v-for="item in order.items"
            :key="item.id"
            class="order-item"
            @click="goToProduct(item.product.id)"
          >
            <img :src="item.product.image_file_path" :alt="item.product.name" class="item-image" />
            <div class="item-details">
              <h4>{{ item.product.name }}</h4>
              <p class="item-meta">{{ item.product.brand }} • Qty: {{ item.quantity }}</p>
            </div>
            <p class="item-price">${{ (item.price_at_purchase * item.quantity).toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.orders-page {
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 2rem;
}

.error-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h2 {
  font-size: 1.5rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.order-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.order-info h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.order-date {
  font-size: 0.85rem;
  color: #6b7280;
}

.order-total {
  text-align: right;
}

.order-total .label {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.order-total .amount {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}

.order-items {
  padding: 1rem;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.order-item:hover {
  background: #f5f7fa;
}

.item-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
}

.item-details {
  flex: 1;
}

.item-details h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.item-meta {
  font-size: 0.85rem;
  color: #6b7280;
}

.item-price {
  font-weight: 600;
  color: #1a1a2e;
}
</style>
