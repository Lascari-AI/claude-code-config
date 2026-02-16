<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useCartStore } from '../stores/cart';
import api from '../services/api';

const router = useRouter();
const cartStore = useCartStore();

const processing = ref(false);
const error = ref('');

async function placeOrder() {
  processing.value = true;
  error.value = '';

  try {
    const order = await api.checkout();
    cartStore.clearCart();
    router.push(`/order-confirmation/${order.order_id}`);
  } catch (e: any) {
    error.value = e.message || 'Failed to place order';
  } finally {
    processing.value = false;
  }
}

function goBack() {
  router.push('/cart');
}

onMounted(() => {
  if (cartStore.items.length === 0) {
    cartStore.fetchCart();
  }
});
</script>

<template>
  <div class="checkout-page">
    <button class="back-btn" @click="goBack">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m15 18-6-6 6-6"/>
      </svg>
      Back to Cart
    </button>

    <h1>Checkout</h1>

    <div class="checkout-content">
      <div class="order-review">
        <h2>Order Review</h2>
        <div class="items-list">
          <div v-for="item in cartStore.items" :key="item.id" class="checkout-item">
            <img :src="item.product.image_file_path" :alt="item.product.name" class="item-image" />
            <div class="item-info">
              <h3>{{ item.product.name }}</h3>
              <p class="quantity">Qty: {{ item.quantity }}</p>
            </div>
            <p class="item-total">${{ (item.product.price * item.quantity).toFixed(2) }}</p>
          </div>
        </div>

        <div class="shipping-info">
          <h3>Shipping</h3>
          <p class="shipping-note">Demo mode - no actual shipping</p>
        </div>
      </div>

      <div class="order-summary">
        <h2>Order Summary</h2>
        <div class="summary-details">
          <div class="summary-row">
            <span>Subtotal ({{ cartStore.totalItems }} items)</span>
            <span>${{ cartStore.totalPrice.toFixed(2) }}</span>
          </div>
          <div class="summary-row">
            <span>Shipping</span>
            <span class="free">FREE</span>
          </div>
          <div class="summary-row">
            <span>Tax</span>
            <span>$0.00</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-row total">
            <span>Total</span>
            <span>${{ cartStore.totalPrice.toFixed(2) }}</span>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button
          class="place-order-btn"
          @click="placeOrder"
          :disabled="processing || cartStore.items.length === 0"
        >
          <span v-if="processing" class="spinner-small"></span>
          <span v-else>Place Order</span>
        </button>

        <p class="demo-notice">
          This is a demo. No actual payment will be processed.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.checkout-page {
  max-width: 1000px;
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

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 2rem;
}

.checkout-content {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 2rem;
}

.order-review {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.order-review h2 {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.checkout-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.checkout-item:last-child {
  border-bottom: none;
}

.item-image {
  width: 70px;
  height: 70px;
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

.quantity {
  font-size: 0.9rem;
  color: #6b7280;
}

.item-total {
  font-weight: 700;
  color: #1a1a2e;
}

.shipping-info {
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.shipping-info h3 {
  font-size: 1rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.shipping-note {
  color: #6b7280;
  font-size: 0.9rem;
}

.order-summary {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  height: fit-content;
}

.order-summary h2 {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.95rem;
}

.summary-row.total {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}

.free {
  color: #10b981;
  font-weight: 600;
}

.summary-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 1rem 0;
}

.error {
  color: #ef4444;
  font-size: 0.9rem;
  text-align: center;
  margin-bottom: 1rem;
}

.place-order-btn {
  width: 100%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 1rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.place-order-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.demo-notice {
  font-size: 0.8rem;
  color: #9ca3af;
  text-align: center;
}

@media (max-width: 900px) {
  .checkout-content {
    grid-template-columns: 1fr;
  }
}
</style>
