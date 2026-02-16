<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../stores/user';
import { useCartStore } from '../../stores/cart';
import { useExpertiseStore } from '../../stores/expertise';
import SearchBar from '../common/SearchBar.vue';

const router = useRouter();
const userStore = useUserStore();
const cartStore = useCartStore();
const expertiseStore = useExpertiseStore();

const cartCount = computed(() => cartStore.totalItems);

function handleLogout() {
  userStore.logout();
  router.push('/login');
}

function goToCart() {
  router.push('/cart');
}

function goHome() {
  router.push('/');
}
</script>

<template>
  <header class="header">
    <div class="header-content">
      <div class="logo" @click="goHome">
        <span class="logo-text">NILE</span>
        <span class="logo-tagline">Flow into savings</span>
      </div>

      <SearchBar class="search" />

      <nav class="nav">
        <router-link to="/" class="nav-link">Home</router-link>
        <router-link to="/orders" class="nav-link">Orders</router-link>
        <router-link to="/profile" class="nav-link">Profile</router-link>
      </nav>

      <div class="header-actions">
        <button class="cart-btn" @click="goToCart">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="9" cy="21" r="1"/>
            <circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
          </svg>
          <span v-if="cartCount > 0" class="cart-badge">{{ cartCount }}</span>
        </button>

        <button class="expertise-btn" @click="expertiseStore.togglePanel" title="Toggle Expertise Panel (Ctrl+K)">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          <span class="improvements-count">{{ expertiseStore.totalImprovements }}</span>
        </button>

        <div class="user-menu">
          <span class="user-name">{{ userStore.user?.name }}</span>
          <button class="logout-btn" @click="handleLogout">Logout</button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo {
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.logo-text {
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #ff9900 0%, #ffcc00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 2px;
}

.logo-tagline {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 1px;
}

.search {
  flex: 1;
  max-width: 600px;
}

.nav {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: #ff9900;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.cart-btn,
.expertise-btn {
  position: relative;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  padding: 0.6rem;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.cart-btn:hover,
.expertise-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.cart-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ff9900;
  color: #1a1a2e;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
}

.improvements-count {
  font-size: 0.75rem;
  background: rgba(255, 153, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-left: 1rem;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
}

.user-name {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.logout-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.8);
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}
</style>
