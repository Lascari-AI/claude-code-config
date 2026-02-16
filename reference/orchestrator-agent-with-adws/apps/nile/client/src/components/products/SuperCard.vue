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
  <section class="super-card-section">
    <h2 v-if="title" class="section-title">{{ title }}</h2>
    <div class="super-cards">
      <div
        v-for="product in products"
        :key="product.id"
        class="super-card"
        @click="emit('view-product', product.id)"
      >
        <div class="image-section">
          <img :src="product.image_file_path" :alt="product.name" class="product-image" />
          <div class="badges">
            <span class="featured-badge">Featured for You</span>
            <span class="shipping-badge">{{ product.shipping_speed }} shipping</span>
          </div>
        </div>
        <div class="content-section">
          <div class="header">
            <h3>{{ product.name }}</h3>
            <span class="brand">{{ product.brand }}</span>
          </div>
          <p class="description">{{ product.description }}</p>
          <div class="specs">
            <div class="spec">
              <span class="spec-label">Category</span>
              <span class="spec-value">{{ product.category }}</span>
            </div>
            <div class="spec">
              <span class="spec-label">Rating</span>
              <span class="spec-value rating">
                <span class="stars">★</span> {{ product.rating.toFixed(1) }}
              </span>
            </div>
          </div>
          <div class="reviews-preview" v-if="product.reviews?.length">
            <h4>Top Review</h4>
            <p class="review-text">"{{ product.reviews[0].review_text }}"</p>
            <span class="reviewer">— {{ product.reviews[0].reviewer_name }}</span>
          </div>
          <div class="action-row">
            <div class="price-container">
              <span class="price">${{ product.price.toFixed(2) }}</span>
            </div>
            <button class="add-btn" @click.stop="emit('add-to-cart', product.id)">
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.super-card-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.super-cards {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.super-card {
  display: flex;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.super-card:hover {
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
  transform: translateY(-6px);
}

.image-section {
  position: relative;
  width: 350px;
  flex-shrink: 0;
  background: #f5f7fa;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.super-card:hover .product-image {
  transform: scale(1.05);
}

.badges {
  position: absolute;
  top: 1rem;
  left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.featured-badge {
  background: linear-gradient(135deg, #ff9900 0%, #ffcc00 100%);
  color: #1a1a2e;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
}

.shipping-badge {
  background: #10b981;
  color: white;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.content-section {
  flex: 1;
  padding: 2rem;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: 1rem;
}

.header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.brand {
  color: #0066cc;
  font-weight: 500;
}

.description {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.specs {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.spec {
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

.spec-value.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.stars {
  color: #f59e0b;
}

.reviews-preview {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.reviews-preview h4 {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.review-text {
  font-style: italic;
  color: #4b5563;
  margin-bottom: 0.5rem;
}

.reviewer {
  font-size: 0.85rem;
  color: #9ca3af;
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.price {
  font-size: 2rem;
  font-weight: 800;
  color: #1a1a2e;
}

.add-btn {
  background: linear-gradient(135deg, #ff9900 0%, #ffaa22 100%);
  color: #1a1a2e;
  border: none;
  padding: 1rem 2rem;
  border-radius: 10px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 153, 0, 0.4);
}

@media (max-width: 900px) {
  .super-card {
    flex-direction: column;
  }

  .image-section {
    width: 100%;
    height: 250px;
  }
}
</style>
