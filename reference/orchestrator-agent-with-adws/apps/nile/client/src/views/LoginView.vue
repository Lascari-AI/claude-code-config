<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const username = ref('');
const loading = ref(false);
const error = ref('');

async function handleLogin() {
  if (!username.value.trim()) {
    error.value = 'Please enter your name';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    await userStore.login(username.value.trim());
    const redirect = route.query.redirect as string || '/';
    router.push(redirect);
  } catch (e: any) {
    error.value = e.message || 'Login failed';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <span class="logo-text">NILE</span>
        <span class="logo-tagline">Flow into savings</span>
      </div>

      <h1>Welcome</h1>
      <p class="subtitle">Enter your name to continue</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <input
            v-model="username"
            type="text"
            placeholder="Your name"
            class="input"
            :disabled="loading"
            autofocus
          />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="spinner-small"></span>
          <span v-else>Continue</span>
        </button>
      </form>

      <div class="demo-note">
        <p>This is a demo. Enter any name to create or access your account.</p>
        <p class="hint">Try: "Alex" or "Developer"</p>
      </div>
    </div>

    <div class="features">
      <div class="feature">
        <span class="feature-icon">🧠</span>
        <h3>Agent Expert</h3>
        <p>Experience adaptive shopping powered by AI that learns from your preferences</p>
      </div>
      <div class="feature">
        <span class="feature-icon">📈</span>
        <h3>Personalization</h3>
        <p>Watch your homepage evolve as you browse, cart, and purchase products</p>
      </div>
      <div class="feature">
        <span class="feature-icon">🔍</span>
        <h3>Expertise Panel</h3>
        <p>Press Ctrl+K to see how the agent learns from your actions in real-time</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4rem;
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%);
}

.login-card {
  background: white;
  padding: 3rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 420px;
}

.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
}

.logo-text {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 4px;
}

.logo-tagline {
  font-size: 0.85rem;
  color: #6b7280;
  letter-spacing: 2px;
}

h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a1a2e;
  text-align: center;
  margin-bottom: 0.5rem;
}

.subtitle {
  text-align: center;
  color: #6b7280;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-group {
  position: relative;
}

.input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.2s;
}

.input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.1);
}

.error {
  color: #ef4444;
  font-size: 0.9rem;
  text-align: center;
}

.login-btn {
  background: linear-gradient(135deg, #ff9900 0%, #ffaa22 100%);
  color: #1a1a2e;
  border: none;
  padding: 1rem;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 153, 0, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(26, 26, 46, 0.2);
  border-top-color: #1a1a2e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.demo-note {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.demo-note p {
  font-size: 0.85rem;
  color: #9ca3af;
}

.demo-note .hint {
  margin-top: 0.5rem;
  color: #6b7280;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 300px;
}

.feature {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feature-icon {
  font-size: 2rem;
}

.feature h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a1a2e;
}

.feature p {
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .login-page {
    flex-direction: column;
    gap: 3rem;
  }

  .features {
    flex-direction: row;
    max-width: none;
    gap: 2rem;
  }

  .feature {
    flex: 1;
    text-align: center;
  }
}
</style>
