// Cart store
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CartItem, CartResponse } from '../types';
import api from '../services/api';

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const totalItems = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0));
  const totalPrice = computed(() =>
    items.value.reduce((sum, item) => sum + item.product.price * item.quantity, 0)
  );

  async function fetchCart() {
    loading.value = true;
    error.value = null;
    try {
      const cart = await api.getCart();
      items.value = cart.items;
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch cart';
    } finally {
      loading.value = false;
    }
  }

  async function addItem(productId: number, quantity = 1) {
    loading.value = true;
    error.value = null;
    try {
      await api.addToCart(productId, quantity);
      await fetchCart();
    } catch (e: any) {
      error.value = e.message || 'Failed to add item';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function updateItem(itemId: number, quantity: number) {
    loading.value = true;
    error.value = null;
    try {
      if (quantity <= 0) {
        await api.removeFromCart(itemId);
      } else {
        await api.updateCartItem(itemId, quantity);
      }
      await fetchCart();
    } catch (e: any) {
      error.value = e.message || 'Failed to update item';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function removeItem(itemId: number) {
    loading.value = true;
    error.value = null;
    try {
      await api.removeFromCart(itemId);
      await fetchCart();
    } catch (e: any) {
      error.value = e.message || 'Failed to remove item';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function clearCart() {
    items.value = [];
  }

  return {
    items,
    loading,
    error,
    totalItems,
    totalPrice,
    fetchCart,
    addItem,
    updateItem,
    removeItem,
    clearCart
  };
});
