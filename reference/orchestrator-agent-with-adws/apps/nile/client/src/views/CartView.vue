<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCartStore } from '../stores/cart';
import LoadingSpinner from '../components/common/LoadingSpinner.vue';

const router = useRouter();
const cartStore = useCartStore();

const isEmpty = computed(() => cartStore.items.length === 0);

async function updateQuantity(itemId: number, quantity: number) {
  await cartStore.updateItem(itemId, quantity);
}

async function removeItem(itemId: number) {
  await cartStore.removeItem(itemId);
}

function goToProduct(productId: number) {
  router.push(`/product/${productId}`);
}

function goToCheckout() {
  router.push('/checkout');
}

function continueShopping() {
  router.push('/');
}

onMounted(() => {
  cartStore.fetchCart();
});
</script>

<template>
  <div class="cart-page">
    <h1>Shopping Cart</h1>

    <LoadingSpinner v-if="cartStore.loading && !cartStore.items.length" />

    <div v-else-if="isEmpty" class="empty-cart">
      <div class="empty-icon">🛒</div>
      <h2>Your cart is empty</h2>
      <p>Looks like you haven't added anything to your cart yet.</p>
      <button class="btn btn-primary" @click="continueShopping">
        Continue Shopping
      </button>
    </div>

    <div v-else class="cart-content">
      <div class="cart-items">
        <div
          v-for="item in cartStore.items"
          :key="item.id"
          class="cart-item"
        >
          <img
            :src="item.product.image_file_path"
            :alt="item.product.name"
            class="item-image"
            @click="goToProduct(item.product.id)"
          />
          <div class="item-details">
            <h3 @click="goToProduct(item.product.id)">{{ item.product.name }}</h3>
            <p class="brand">{{ item.product.brand }}</p>
            <p class="shipping">{{ item.product.shipping_speed }} shipping</p>
          </div>
          <div class="item-quantity">
            <button @click="updateQuantity(item.id, item.quantity - 1)">-</button>
            <span>{{ item.quantity }}</span>
            <button @click="updateQuantity(item.id, item.quantity + 1)">+</button>
          </div>
          <div class="item-price">
            <p class="unit-price">${{ item.product.price.toFixed(2) }} each</p>
            <p class="total-price">${{ (item.product.price * item.quantity).toFixed(2) }}</p>
          </div>
          <button class="remove-btn" @click="removeItem(item.id)">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"/>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="cart-summary">
        <h2>Order Summary</h2>
        <div class="summary-row">
          <span>Items ({{ cartStore.totalItems }})</span>
          <span>${{ cartStore.totalPrice.toFixed(2) }}</span>
        </div>
        <div class="summary-row">
          <span>Shipping</span>
          <span class="free">FREE</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-row total">
          <span>Total</span>
          <span>${{ cartStore.totalPrice.toFixed(2) }}</span>
        </div>
        <button class="checkout-btn" @click="goToCheckout">
          Proceed to Checkout
        </button>
        <button class="continue-btn" @click="continueShopping">
          Continue Shopping
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cart-page {
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 2rem;
}

.empty-cart {
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

.empty-cart h2 {
  font-size: 1.5rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.empty-cart p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.cart-content {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
}

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.item-image {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
}

.item-details {
  flex: 1;
}

.item-details h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
  cursor: pointer;
}

.item-details h3:hover {
  color: #0066cc;
}

.brand {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.shipping {
  font-size: 0.85rem;
  color: #10b981;
}

.item-quantity {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.item-quantity button {
  background: #f5f7fa;
  border: none;
  width: 35px;
  height: 35px;
  cursor: pointer;
  transition: background 0.2s;
}

.item-quantity button:hover {
  background: #e5e7eb;
}

.item-quantity span {
  width: 40px;
  text-align: center;
  font-weight: 600;
}

.item-price {
  text-align: right;
  min-width: 100px;
}

.unit-price {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.total-price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}

.remove-btn {
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.5rem;
  transition: color 0.2s;
}

.remove-btn:hover {
  color: #ef4444;
}

.cart-summary {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  height: fit-content;
  position: sticky;
  top: 100px;
}

.cart-summary h2 {
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

.checkout-btn {
  width: 100%;
  background: linear-gradient(135deg, #ff9900 0%, #ffaa22 100%);
  color: #1a1a2e;
  border: none;
  padding: 1rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 0.75rem;
}

.checkout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 153, 0, 0.4);
}

.continue-btn {
  width: 100%;
  background: transparent;
  border: 2px solid #e5e7eb;
  color: #6b7280;
  padding: 0.75rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.continue-btn:hover {
  border-color: #0066cc;
  color: #0066cc;
}

@media (max-width: 900px) {
  .cart-content {
    grid-template-columns: 1fr;
  }

  .cart-summary {
    position: static;
  }
}
</style>
