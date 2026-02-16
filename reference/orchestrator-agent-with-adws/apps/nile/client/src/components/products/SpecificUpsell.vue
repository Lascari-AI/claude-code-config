<script setup lang="ts">
import type { Product } from '../../types';

defineProps<{
  title?: string;
  subtitle?: string;
  product?: Product;
}>();

const emit = defineEmits<{
  (e: 'view-product', id: number): void;
  (e: 'add-to-cart', id: number): void;
}>();
</script>

<template>
  <div v-if="product" class="specific-upsell">
    <div class="upsell-content">
      <span class="recommendation-badge">Recommended for you</span>
      <h3 class="title">{{ title || 'Complete Your Setup' }}</h3>
      <p class="subtitle">{{ subtitle || 'Based on your recent activity' }}</p>
    </div>
    <div class="product-card" @click="emit('view-product', product.id)">
      <img :src="product.image_file_path" :alt="product.name" class="product-image" />
      <div class="product-details">
        <h4>{{ product.name }}</h4>
        <p class="brand">{{ product.brand }}</p>
        <div class="rating">
          <span class="stars">★</span>
          <span>{{ product.rating.toFixed(1) }}</span>
        </div>
        <p class="price">${{ product.price.toFixed(2) }}</p>
        <button class="add-btn" @click.stop="emit('add-to-cart', product.id)">
          Add to Cart
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.specific-upsell {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f3460 100%);
  padding: 2rem;
  border-radius: 16px;
  margin-bottom: 2rem;
  display: flex;
  gap: 2rem;
  align-items: center;
}

.upsell-content {
  flex: 1;
}

.recommendation-badge {
  display: inline-block;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
}

.product-card {
  display: flex;
  gap: 1.5rem;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  max-width: 400px;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.product-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
}

.product-details {
  flex: 1;
}

.product-details h4 {
  font-size: 1rem;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.brand {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.stars {
  color: #f59e0b;
}

.price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.75rem;
}

.add-btn {
  background: #ff9900;
  color: #1a1a2e;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #ffaa22;
}
</style>
