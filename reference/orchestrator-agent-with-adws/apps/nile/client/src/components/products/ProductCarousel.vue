<script setup lang="ts">
import { ref } from 'vue';
import type { Product } from '../../types';

defineProps<{
  title?: string;
  products?: Product[];
}>();

const emit = defineEmits<{
  (e: 'view-product', id: number): void;
  (e: 'add-to-cart', id: number): void;
}>();

const scrollContainer = ref<HTMLElement | null>(null);

function scroll(direction: 'left' | 'right') {
  if (scrollContainer.value) {
    const scrollAmount = 300;
    scrollContainer.value.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth'
    });
  }
}
</script>

<template>
  <section class="carousel-section">
    <div class="section-header">
      <h2 v-if="title" class="section-title">{{ title }}</h2>
      <div class="scroll-buttons">
        <button class="scroll-btn" @click="scroll('left')">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <button class="scroll-btn" @click="scroll('right')">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </button>
      </div>
    </div>
    <div ref="scrollContainer" class="carousel">
      <div
        v-for="product in products"
        :key="product.id"
        class="carousel-item"
        @click="emit('view-product', product.id)"
      >
        <div class="image-container">
          <img :src="product.image_file_path" :alt="product.name" class="product-image" />
        </div>
        <div class="product-info">
          <h3>{{ product.name }}</h3>
          <p class="brand">{{ product.brand }}</p>
          <div class="rating">
            <span class="stars">★</span>
            <span>{{ product.rating.toFixed(1) }}</span>
          </div>
          <p class="price">${{ product.price.toFixed(2) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.carousel-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
}

.scroll-buttons {
  display: flex;
  gap: 0.5rem;
}

.scroll-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #6b7280;
}

.scroll-btn:hover {
  background: #f5f7fa;
  border-color: #0066cc;
  color: #0066cc;
}

.carousel {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 0.5rem;
}

.carousel::-webkit-scrollbar {
  display: none;
}

.carousel-item {
  flex: 0 0 220px;
  scroll-snap-align: start;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s;
}

.carousel-item:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.image-container {
  height: 180px;
  background: #f5f7fa;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.carousel-item:hover .product-image {
  transform: scale(1.05);
}

.product-info {
  padding: 1rem;
}

.product-info h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.stars {
  color: #f59e0b;
}

.price {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a1a2e;
}
</style>
