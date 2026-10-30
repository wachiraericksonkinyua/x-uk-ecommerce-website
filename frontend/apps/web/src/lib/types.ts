export interface ProductImage {
  id?: string;
  image_url: string;
}

export interface Product {
  id: string;
  name: string;
  price: number;
  brand?: string | null;
  description?: string | null;
  color?: string | null;
  category?: string | null;
  category_id?: string | null;
  stock_quantity?: number | null;
  image_url?: string | null;
  product_images?: ProductImage[] | null;
  created_at?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  image_url?: string | null;
  active: boolean;
}

export interface DeliveryLocation {
  id: string;
  name: string;
  cost: number;
  active: boolean;
}

export interface Review {
  id?: string;
  product_id: string;
  user_id?: string;
  rating: number;
  comment: string;
  created_at?: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  quantity: number;
  products?: Product | null;
}

export interface WishlistItem {
  id: string;
  created_at?: string;
  products?: Product | null;
}

export interface OrderItem {
  id: string;
  name: string;
  price: number;
  qty: number;
  image?: string | null;
}

export interface Order {
  id: string;
  order_reference: string;
  user_id?: string;
  customer_phone?: string | null;
  customer_email?: string | null;
  fulfillment?: string | null;
  location_name?: string | null;
  delivery_cost?: number | null;
  delivery_address?: string | null;
  payment_method?: string | null;
  total_amount: number;
  status: string;
  receipt_number?: string | null;
  items: OrderItem[];
  created_at?: string;
}

export interface Profile {
  id?: string;
  user_id?: string;
  full_name?: string | null;
  phone_number?: string | null;
  address?: string | null;
  avatar_url?: string | null;
  banner_url?: string | null;
  date_of_birth?: string | null;
  role?: string | null;
  created_at?: string;
}

export interface Session {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
}

export interface AuthUser {
  id: string;
  email?: string;
}

export type OrderStatus =
  | "Pending PIN"
  | "Paid"
  | "Processing"
  | "Shipped"
  | "Delivered"
  | "Cancelled"
  | "Payment Failed";
