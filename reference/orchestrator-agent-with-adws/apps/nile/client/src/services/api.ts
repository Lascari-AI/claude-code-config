// API service for Nile
import axios, { type AxiosInstance } from 'axios';
import type {
  User,
  Product,
  CartResponse,
  CartItem,
  OrderResponse,
  Expertise,
  HomePageResponse,
  SearchSuggestion
} from '../types';

// Use relative URL so Vite proxy handles routing to backend
const API_BASE = import.meta.env.VITE_API_URL || '';

class ApiService {
  private client: AxiosInstance;
  private userId: number | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE}/api`,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add user ID to requests
    this.client.interceptors.request.use((config) => {
      if (this.userId) {
        config.headers['X-User-Id'] = String(this.userId);
      }
      return config;
    });
  }

  setUserId(id: number) {
    this.userId = id;
  }

  getUserId(): number | null {
    return this.userId;
  }

  // Auth
  async login(name: string): Promise<User> {
    const { data } = await this.client.post<User>('/auth/login', { name });
    this.userId = data.id;
    return data;
  }

  // Products
  async getProducts(params?: {
    category?: string;
    brand?: string;
    min_price?: number;
    max_price?: number;
    limit?: number;
  }): Promise<Product[]> {
    const { data } = await this.client.get<Product[]>('/products', { params });
    return data;
  }

  async getProduct(id: number): Promise<Product> {
    const { data } = await this.client.get<Product>(`/products/${id}`);
    return data;
  }

  async searchProducts(query: string): Promise<Product[]> {
    const { data } = await this.client.get<Product[]>('/products/search', {
      params: { q: query }
    });
    return data;
  }

  async getCategories(): Promise<string[]> {
    const { data } = await this.client.get<string[]>('/products/categories');
    return data;
  }

  // Cart
  async getCart(): Promise<CartResponse> {
    const { data } = await this.client.get<CartResponse>('/cart');
    return data;
  }

  async addToCart(productId: number, quantity = 1): Promise<CartItem> {
    const { data } = await this.client.post<CartItem>('/cart/add', {
      product_id: productId,
      quantity
    });
    return data;
  }

  async updateCartItem(itemId: number, quantity: number): Promise<CartItem> {
    const { data } = await this.client.put<CartItem>(`/cart/${itemId}`, {
      quantity
    });
    return data;
  }

  async removeFromCart(itemId: number): Promise<void> {
    await this.client.delete(`/cart/${itemId}`);
  }

  // Orders
  async checkout(): Promise<OrderResponse> {
    const { data } = await this.client.post<OrderResponse>('/orders/checkout');
    return data;
  }

  async getOrders(): Promise<OrderResponse[]> {
    const { data } = await this.client.get<OrderResponse[]>('/orders');
    return data;
  }

  async getOrder(orderId: string): Promise<OrderResponse> {
    const { data } = await this.client.get<OrderResponse>(`/orders/${orderId}`);
    return data;
  }

  // Expertise
  async getExpertise(): Promise<Expertise> {
    const { data } = await this.client.get<Expertise>('/expertise');
    return data;
  }

  async trackAction(actionType: 'view_product_details' | 'add_to_cart' | 'checkout', productId: number): Promise<void> {
    await this.client.post('/expertise/action', {
      action_type: actionType,
      product_id: productId
    });
  }

  async clearExpertise(): Promise<void> {
    await this.client.delete('/expertise');
  }

  async getLiveSystemPrompt(): Promise<{
    system_prompt: string;
    user_prompt: string;
    total_improvements: number;
    prefetched_products: {
      checked_out: any[];
      added_to_cart: any[];
      viewed_products: any[];
    };
  }> {
    const { data } = await this.client.get('/expertise/live-prompt');
    return data;
  }

  // Home
  async getHomePage(): Promise<HomePageResponse> {
    const { data } = await this.client.get<HomePageResponse>('/home');
    return data;
  }

  async getSearchAutocomplete(query: string): Promise<{ suggestions: SearchSuggestion[]; query: string }> {
    const { data } = await this.client.get('/home/autocomplete', {
      params: { q: query }
    });
    return data;
  }
}

export const api = new ApiService();
export default api;
