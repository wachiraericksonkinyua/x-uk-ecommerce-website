import { computed, toValue, type MaybeRefOrGetter } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { api } from "../lib/api";
import type {
  Category,
  Customer,
  DashboardSummary,
  DeliveryLocation,
  Lead,
  LeadStats,
  LowStockProduct,
  Order,
  Paginated,
  Product,
  Review,
  WhatsAppMessage,
} from "../lib/types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.get<DashboardSummary>("/admin/dashboard/summary"),
    refetchInterval: 15000,
    refetchOnWindowFocus: true,
  });
}

export function useLowStock(threshold = 5) {
  return useQuery({
    queryKey: ["admin-low-stock", threshold],
    queryFn: () =>
      api.get<{ success: boolean; threshold: number; data: LowStockProduct[] }>(
        "/admin/inventory/low-stock",
        { threshold }
      ),
  });
}

export interface ProductQuery {
  page: number;
  pageSize: number;
  search?: string;
  lowStock?: boolean;
}

export function useAdminProducts(query: MaybeRefOrGetter<ProductQuery>) {
  return useQuery({
    queryKey: computed(() => {
      const { page, pageSize, search, lowStock } = toValue(query);
      return ["admin-products", page, pageSize, search, lowStock];
    }),
    queryFn: () => {
      const { page, pageSize, search, lowStock } = toValue(query);
      return api.get<Paginated<Product>>("/admin/products", {
        page,
        page_size: pageSize,
        search: search || undefined,
        low_stock: lowStock || undefined,
      });
    },
  });
}

export function useAdminProduct(id: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["admin-product", toValue(id)]),
    enabled: () => Boolean(toValue(id)),
    queryFn: async () => {
      const res = await api.get<{ success: boolean; data: Product }>(
        `/admin/products/${toValue(id)}`
      );
      return res.data;
    },
  });
}

export interface OrderQuery {
  page: number;
  pageSize: number;
  status?: string;
  search?: string;
}

export function useAdminOrders(query: MaybeRefOrGetter<OrderQuery>) {
  return useQuery({
    queryKey: computed(() => {
      const { page, pageSize, status, search } = toValue(query);
      return ["admin-orders", page, pageSize, status, search];
    }),
    queryFn: () => {
      const { page, pageSize, status, search } = toValue(query);
      return api.get<Paginated<Order>>("/admin/orders", {
        page,
        page_size: pageSize,
        status: status || undefined,
        search: search || undefined,
      });
    },
  });
}

export function useAdminCategories() {
  return useQuery({
    queryKey: ["admin-categories"],
    queryFn: async () => {
      const res = await api.get<{ success: boolean; data: Category[] }>(
        "/admin/categories"
      );
      return res.data ?? [];
    },
  });
}

export function useAdminLocations() {
  return useQuery({
    queryKey: ["admin-locations"],
    queryFn: async () => {
      const res = await api.get<{ success: boolean; data: DeliveryLocation[] }>(
        "/admin/delivery-locations"
      );
      return res.data ?? [];
    },
  });
}

export function useAdminCustomers(
  query: MaybeRefOrGetter<{ page: number; pageSize: number; search?: string }>
) {
  return useQuery({
    queryKey: computed(() => {
      const { page, pageSize, search } = toValue(query);
      return ["admin-customers", page, pageSize, search];
    }),
    queryFn: () => {
      const { page, pageSize, search } = toValue(query);
      return api.get<Paginated<Customer>>("/admin/customers", {
        page,
        page_size: pageSize,
        search: search || undefined,
      });
    },
  });
}

export function useCustomerDetail(userId: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["admin-customer", toValue(userId)]),
    enabled: () => Boolean(toValue(userId)),
    queryFn: () =>
      api.get<{
        success: boolean;
        profile: Customer | null;
        orders: Order[];
      }>(`/admin/customers/${toValue(userId)}`),
  });
}

export function useAdminReviews(
  query: MaybeRefOrGetter<{
    page: number;
    pageSize: number;
    productId?: string;
  }>
) {
  return useQuery({
    queryKey: computed(() => {
      const { page, pageSize, productId } = toValue(query);
      return ["admin-reviews", page, pageSize, productId];
    }),
    queryFn: () => {
      const { page, pageSize, productId } = toValue(query);
      return api.get<Paginated<Review>>("/admin/reviews", {
        page,
        page_size: pageSize,
        product_id: productId || undefined,
      });
    },
  });
}

export function useLeadStats() {
  return useQuery({
    queryKey: ["admin-lead-stats"],
    queryFn: () => api.get<LeadStats>("/admin/leads/stats"),
  });
}

export function useLeads(
  query: MaybeRefOrGetter<{
    page: number;
    pageSize: number;
    status?: string;
    search?: string;
  }>
) {
  return useQuery({
    queryKey: computed(() => {
      const { page, pageSize, status, search } = toValue(query);
      return ["admin-leads", page, pageSize, status, search];
    }),
    queryFn: () => {
      const { page, pageSize, status, search } = toValue(query);
      return api.get<Paginated<Lead>>("/admin/leads", {
        page,
        page_size: pageSize,
        status: status || undefined,
        search: search || undefined,
      });
    },
  });
}

export function useLeadMessages(leadId: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["admin-lead-messages", toValue(leadId)]),
    enabled: () => Boolean(toValue(leadId)),
    refetchInterval: () => (toValue(leadId) ? 5000 : false),
    queryFn: async () => {
      const res = await api.get<{ success: boolean; data: WhatsAppMessage[] }>(
        `/admin/leads/${toValue(leadId)}/messages`
      );
      return res.data ?? [];
    },
  });
}
