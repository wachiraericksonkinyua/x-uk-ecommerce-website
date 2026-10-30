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
  created_at?: string;
}

export interface DeliveryLocation {
  id: string;
  name: string;
  cost: number;
  active: boolean;
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
  checkout_request_id?: string | null;
  items: OrderItem[];
  created_at?: string;
}

export interface DashboardSummary {
  total_revenue: number;
  daily_revenue: number;
  total_orders: number;
  paid_orders: number;
  pending_orders: number;
  total_customers: number;
  low_stock_threshold: number;
  low_stock_products: LowStockProduct[];
}

export interface LowStockProduct {
  id: string;
  name: string;
  brand?: string | null;
  stock_quantity: number;
  price?: number;
}

export interface Customer {
  id?: string;
  user_id: string;
  full_name?: string | null;
  phone_number?: string | null;
  address?: string | null;
  avatar_url?: string | null;
  role?: string | null;
  created_at?: string;
}

export interface Review {
  id: string;
  product_id: string;
  user_id?: string;
  rating: number;
  comment: string;
  is_approved?: boolean;
  created_at?: string;
}

export interface Lead {
  id: string;
  phone: string;
  name?: string | null;
  source?: string | null;
  interest?: string | null;
  budget?: number | null;
  location?: string | null;
  timeline?: string | null;
  status: string;
  score: number;
  assigned_to?: string | null;
  last_message_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface WhatsAppMessage {
  id: string;
  lead_id: string;
  direction: "inbound" | "outbound";
  body: string;
  wa_message_id?: string | null;
  created_at?: string;
}

export interface LeadStats {
  success: boolean;
  total: number;
  by_status: Record<string, number>;
  hot_leads: Lead[];
}

export interface Paginated<T> {
  success: boolean;
  page: number;
  page_size: number;
  total: number;
  data: T[];
}

export interface Profile {
  id?: string;
  user_id?: string;
  full_name?: string | null;
  phone_number?: string | null;
  address?: string | null;
  avatar_url?: string | null;
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
