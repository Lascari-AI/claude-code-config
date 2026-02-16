<script setup lang="ts">
import type { Product } from '../../types';

defineProps<{
  slogan_text?: string;
  subtitle?: string;
  product?: Product;
}>();

const emit = defineEmits<{
  (e: 'view-product', id: number): void;
}>();
</script>

<template>
  <div class="specific-slogan" :class="{ 'with-product': product }">
    <div class="content">
      <span class="personalized-badge">Personalized for you</span>
      <h2 class="slogan">{{ slogan_text || 'Welcome back!' }}</h2>
      <p class="subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="product" class="featured-product" @click="emit('view-product', product.id)">
      <img :src="product.image_file_path" :alt="product.name" class="product-image" />
      <div class="product-info">
        <h3>{{ product.name }}</h3>
        <p class="price">${{ product.price.toFixed(2) }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.specific-slogan {
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
  padding: 3rem 2rem;
  border-radius: 16px;
  margin-bottom: 2rem;
  position: relative;
  overflow: hidden;
}

.specific-slogan.with-product {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.content {
  flex: 1;
}

.personalized-badge {
  display: inline-block;
  background: rgba(255, 153, 0, 0.2);
  color: #ff9900;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.slogan {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.75rem;
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
}

.featured-product {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.featured-product:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
}

.product-info h3 {
  color: white;
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.price {
  color: #ff9900;
  font-weight: 700;
  font-size: 1.1rem;
}
</style>
