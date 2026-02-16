<script setup lang="ts">
defineProps<{
  slogan_text?: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="generic-slogan">
    <h1 class="slogan">{{ slogan_text || 'Welcome to Nile' }}</h1>
    <p class="subtitle">{{ subtitle || 'Discover amazing products' }}</p>
  </div>
</template>

<style scoped>
.generic-slogan {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 4rem 2rem;
  border-radius: 16px;
  text-align: center;
  margin-bottom: 2rem;
}

.slogan {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #ff9900 0%, #ffcc00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 1rem;
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
}
</style>
