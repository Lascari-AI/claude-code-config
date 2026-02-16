// Type definitions for Nile

export interface User {
  id: number;
  name: string;
  created_at: string;
}

export interface Review {
  id: number;
  review_text: string;
  rating: number;
  reviewer_name: string;
  review_date: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  image_file_path: string;
  category: string;
  brand: string;
  rating: number;
  shipping_speed: string;
  reviews: Review[];
}

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
}

export interface CartResponse {
  items: CartItem[];
  total_items: number;
  total_price: number;
}

export interface OrderItem {
  id: number;
  product: Product;
  quantity: number;
  price_at_purchase: number;
  created_at: string;
}

export interface OrderResponse {
  order_id: string;
  items: OrderItem[];
  total_price: number;
  created_at: string;
}

// Expertise types
export interface ViewedProduct {
  product_id: number;
  viewed_at: string;
  view_count: number;
}

export interface AddedToCart {
  product_id: number;
  added_at: string;
  add_count: number;
}

export interface CheckedOut {
  product_id: number;
  checked_out_at: string;
  purchase_count: number;
}

export interface ExpertiseData {
  viewed_products: ViewedProduct[];
  added_to_cart: AddedToCart[];
  checked_out: CheckedOut[];
}

export interface Expertise {
  id: number;
  user_id: number;
  total_improvements: number;
  last_improvement_at: string | null;
  expertise_data: ExpertiseData;
}

// Home page types
export type ComponentType =
  | 'generic-slogan'
  | 'specific-slogan'
  | 'specific-upsell'
  | 'basic-square'
  | 'carousel'
  | 'card'
  | 'super-card';

export interface HomeSection {
  component_type: ComponentType;
  title?: string;
  subtitle?: string;
  products?: Product[];
  product?: Product;
  slogan_text?: string;
}

export interface HomePageResponse {
  sections: HomeSection[];
  is_personalized: boolean;
}

export interface SearchSuggestion {
  text: string;
  product_id: number;
  category: string;
}
