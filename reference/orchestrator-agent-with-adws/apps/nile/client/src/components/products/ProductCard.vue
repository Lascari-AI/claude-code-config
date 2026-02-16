<script setup lang="ts">
import type { Product } from '../../types';

defineProps<{
  title?: string;
  products?: Product[];
}>();

const emit = defineEmits<{
  (e: 'view-product', id: number): void;
  (e: 'add-to-cart', id: number): void;
}>();
</script>

<template>
  <section class="card-section">
    <h2 v-if="title" class="section-title">{{ title }}</h2>
    <div class="cards-grid">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-card"
        @click="emit('view-product', product.id)"
      >
        <div class="image-container">
          <img :src="product.image_file_path" :alt="product.name" class="product-image" />
          <span class="shipping-badge">{{ product.shipping_speed }}</span>
        </div>
        <div class="card-content">
          <h3>{{ product.name }}</h3>
          <p class="brand">{{ product.brand }}</p>
          <p class="description">{{ product.description.slice(0, 80) }}...</p>
          <div class="card-footer">
            <div class="rating">
              <span class="stars">★</span>
              <span>{{ product.rating.toFixed(1) }}</span>
            </div>
            <p class="price">${{ product.price.toFixed(2) }}</p>
          </div>
          <button class="add-btn" @click.stop="emit('add-to-cart', product.id)">
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s;
}

.product-card:hover {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.image-container {
  position: relative;
  height: 200px;
  background: #f5f7fa;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.product-card:hover .product-image {
  transform: scale(1.05);
}

.shipping-badge {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: #10b981;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.card-content {
  padding: 1.25rem;
}

.card-content h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.brand {
  font-size: 0.85rem;
  color: #0066cc;
  margin-bottom: 0.5rem;
}

.description {
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.4;
  margin-bottom: 1rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.9rem;
  color: #6b7280;
}

.stars {
  color: #f59e0b;
}

.price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}

.add-btn {
  width: 100%;
  background: #0066cc;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #004c99;
}
</style>
