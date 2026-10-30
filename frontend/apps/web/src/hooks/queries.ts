import { computed, toValue, type MaybeRefOrGetter } from "vue";
import { useQuery } from "@tanstack/vue-query";

import { api } from "../lib/api";
import type {
  CartItem,
  Category,
  DeliveryLocation,
  Order,
  Product,
  Profile,
  Review,
  WishlistItem,
} from "../lib/types";

export interface ProductFilters {
  search?: string;
  category?: string;
  brand?: string;
  color?: string;
  min_price?: string | number;
  max_price?: string | number;
  sort_by?: string;
  order?: string;
}

export function useProducts(filters: MaybeRefOrGetter<ProductFilters> = {}) {
  return useQuery({
    queryKey: computed(() => ["products", toValue(filters)]),
    queryFn: async (): Promise<Product[]> => {
      const current = toValue(filters);
      const res = await api.get<{ data: Product[] }>("/products/", {
        ...current,
        min_price: current.min_price || undefined,
        max_price: current.max_price || undefined,
        search: current.search || undefined,
        category: current.category || undefined,
        brand: current.brand || undefined,
        color: current.color || undefined,
      });
      return res.data ?? [];
    },
  });
}

export function useProduct(id: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["product", toValue(id)]),
    enabled: () => Boolean(toValue(id)),
    queryFn: async (): Promise<Product> => {
      const res = await api.get<{ data: Product }>(`/products/${toValue(id)}`);
      return res.data;
    },
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    staleTime: 5 * 60_000,
    queryFn: async (): Promise<Category[]> => {
      const res = await api.get<{ data: Category[] }>("/categories/");
      return res.data ?? [];
    },
  });
}

export function useReviews(productId: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["reviews", toValue(productId)]),
    enabled: () => Boolean(toValue(productId)),
    queryFn: async (): Promise<Review[]> => {
      const res = await api.get<{ data: Review[] }>(
        `/reviews/${toValue(productId)}`
      );
      return res.data ?? [];
    },
  });
}

export function useDeliveryLocations() {
  return useQuery({
    queryKey: ["delivery-locations"],
    staleTime: 5 * 60_000,
    queryFn: async (): Promise<DeliveryLocation[]> => {
      const res = await api.get<{ data: DeliveryLocation[] }>(
        "/delivery/locations"
      );
      return res.data ?? [];
    },
  });
}

export function useCart(enabled: MaybeRefOrGetter<boolean>) {
  return useQuery({
    queryKey: ["cart"],
    enabled: () => Boolean(toValue(enabled)),
    queryFn: async (): Promise<CartItem[]> => {
      const res = await api.get<{ data: CartItem[] }>("/cart/");
      return res.data ?? [];
    },
  });
}

export function useWishlist(enabled: MaybeRefOrGetter<boolean>) {
  return useQuery({
    queryKey: ["wishlist"],
    enabled: () => Boolean(toValue(enabled)),
    queryFn: async (): Promise<WishlistItem[]> => {
      const res = await api.get<{ data: WishlistItem[] }>("/wishlist/");
      return res.data ?? [];
    },
  });
}

export function useMyOrders(enabled: MaybeRefOrGetter<boolean>) {
  return useQuery({
    queryKey: ["my-orders"],
    enabled: () => Boolean(toValue(enabled)),
    queryFn: async (): Promise<Order[]> => {
      const res = await api.get<{ data: Order[] }>("/orders/me");
      return res.data ?? [];
    },
  });
}

export function useTrackOrder(ref: MaybeRefOrGetter<string | undefined>) {
  return useQuery({
    queryKey: computed(() => ["track", toValue(ref)]),
    enabled: () => Boolean(toValue(ref)),
    refetchInterval: (query) => {
      const data = query.state.data as Order | undefined;
      return data?.status === "Pending PIN" ? 3000 : false;
    },
    queryFn: async (): Promise<Order> => {
      const res = await api.get<{ data: Order }>(
        `/orders/track/${toValue(ref)}`
      );
      return res.data;
    },
  });
}

export function useMyProfile(enabled: MaybeRefOrGetter<boolean>) {
  return useQuery({
    queryKey: ["profile"],
    enabled: () => Boolean(toValue(enabled)),
    queryFn: async (): Promise<Profile | null> => {
      const res = await api.get<{ data: Profile }>("/profiles/me");
      return res.data;
    },
  });
}
