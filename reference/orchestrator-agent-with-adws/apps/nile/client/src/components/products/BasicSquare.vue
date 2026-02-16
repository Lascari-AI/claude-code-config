<script setup lang="ts">
import type { Product } from '../../types';

defineProps<{
  title?: string;
  products?: Product[];
}>();

const emit = defineEmits<{
  (e: 'view-product', id: number): void;
}>();
</script>

<template>
  <section class="basic-square-section">
    <h2 v-if="title" class="section-title">{{ title }}</h2>
    <div class="grid">
      <div
        v-for="product in products"
        :key="product.id"
        class="square-item"
        @click="emit('view-product', product.id)"
      >
        <img :src="product.image_file_path" :alt="product.name" class="product-image" />
        <div class="overlay">
          <h3>{{ product.name }}</h3>
          <p class="price">${{ product.price.toFixed(2) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.basic-square-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.square-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  background: #f5f7fa;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.square-item:hover .product-image {
  transform: scale(1.05);
}

.overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  padding: 1.5rem 1rem 1rem;
  color: white;
}

.overlay h3 {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price {
  font-size: 1rem;
  font-weight: 700;
  color: #ff9900;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
