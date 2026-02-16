// User store
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types';
import api from '../services/api';

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isLoggedIn = computed(() => !!user.value);
  const userId = computed(() => user.value?.id ?? null);

  async function login(name: string) {
    loading.value = true;
    error.value = null;
    try {
      const userData = await api.login(name);
      user.value = userData;
      localStorage.setItem('nile_user', JSON.stringify(userData));
      return userData;
    } catch (e: any) {
      error.value = e.message || 'Login failed';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    user.value = null;
    localStorage.removeItem('nile_user');
  }

  function restoreSession() {
    const stored = localStorage.getItem('nile_user');
    if (stored) {
      try {
        const userData = JSON.parse(stored) as User;
        user.value = userData;
        api.setUserId(userData.id);
      } catch {
        localStorage.removeItem('nile_user');
      }
    }
  }

  return {
    user,
    loading,
    error,
    isLoggedIn,
    userId,
    login,
    logout,
    restoreSession
  };
});
