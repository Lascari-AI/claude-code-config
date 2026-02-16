<script setup lang="ts">
import { computed } from 'vue';
import { useUserStore } from '../stores/user';
import { useExpertiseStore } from '../stores/expertise';

const userStore = useUserStore();
const expertiseStore = useExpertiseStore();

const memberSince = computed(() => {
  if (!userStore.user?.created_at) return '';
  return new Date(userStore.user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
});
</script>

<template>
  <div class="profile-page">
    <div class="profile-header">
      <div class="avatar">
        {{ userStore.user?.name?.charAt(0).toUpperCase() }}
      </div>
      <div class="user-info">
        <h1>{{ userStore.user?.name }}</h1>
        <p class="member-since">Member since {{ memberSince }}</p>
      </div>
    </div>

    <div class="profile-sections">
      <div class="section">
        <h2>Account Information</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">Name</span>
            <span class="value">{{ userStore.user?.name }}</span>
          </div>
          <div class="info-item">
            <span class="label">User ID</span>
            <span class="value">{{ userStore.user?.id }}</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>Agent Expert Stats</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-value">{{ expertiseStore.totalImprovements }}</span>
            <span class="stat-label">Total Interactions</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ expertiseStore.expertiseData.viewed_products?.length || 0 }}</span>
            <span class="stat-label">Products Viewed</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ expertiseStore.expertiseData.added_to_cart?.length || 0 }}</span>
            <span class="stat-label">Added to Cart</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ expertiseStore.expertiseData.checked_out?.length || 0 }}</span>
            <span class="stat-label">Purchases</span>
          </div>
        </div>
        <p class="stats-note">
          These interactions help the Agent Expert personalize your shopping experience.
          Press <kbd>Ctrl+K</kbd> to see the full expertise data.
        </p>
      </div>

      <div class="section">
        <h2>Quick Links</h2>
        <div class="links-grid">
          <router-link to="/orders" class="link-card">
            <span class="link-icon">📦</span>
            <span class="link-text">Order History</span>
          </router-link>
          <router-link to="/cart" class="link-card">
            <span class="link-icon">🛒</span>
            <span class="link-text">Shopping Cart</span>
          </router-link>
          <router-link to="/" class="link-card">
            <span class="link-icon">🏠</span>
            <span class="link-text">Home</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.avatar {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #ff9900 0%, #ffcc00 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 700;
  color: #1a1a2e;
}

.user-info h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.member-since {
  color: #6b7280;
}

.profile-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.section h2 {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 1.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  font-size: 0.8rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-weight: 600;
  color: #1a1a2e;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.8rem;
  color: #6b7280;
}

.stats-note {
  font-size: 0.9rem;
  color: #6b7280;
  text-align: center;
}

kbd {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.link-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.2s;
}

.link-card:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
}

.link-icon {
  font-size: 2rem;
}

.link-text {
  font-weight: 600;
  color: #1a1a2e;
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>
