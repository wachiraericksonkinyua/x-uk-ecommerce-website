<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Heart, ShoppingCart, Trash2 } from "@lucide/vue";
import { RouterLink } from "vue-router";
import { toast } from "vue-sonner";

import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useWishlist } from "../hooks/queries";
import { formatKES, productImage } from "../lib/utils";

const queryClient = useQueryClient();
const { data: items, isLoading } = useWishlist(true);
const wishlistItems = computed(() =>
  (items.value ?? []).filter((item) => item.products)
);

const remove = useMutation({
  mutationFn: (productId: string) => api.del(`/wishlist/${productId}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    toast.success("Removed from wishlist");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const addToCart = useMutation({
  mutationFn: (productId: string) =>
    api.post("/cart/add", { product_id: productId, quantity: 1 }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    toast.success("Added to cart");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading wishlist…" />

  <div v-else-if="wishlistItems.length === 0" class="mx-auto max-w-3xl px-4 py-16">
    <EmptyState
      title="Your wishlist is empty"
      description="Tap the heart on any product to save it here."
    >
      <template #icon>
        <Heart class="text-slate-300" :size="40" />
      </template>
      <template #action>
        <RouterLink
          to="/shop"
          class="mt-2 rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Browse products
        </RouterLink>
      </template>
    </EmptyState>
  </div>

  <div v-else class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-slate-900">My Wishlist</h1>

    <div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="item in wishlistItems"
        :key="item.id"
        class="flex gap-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
      >
        <RouterLink
          :to="`/products/${item.products!.id}`"
          class="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-slate-50"
        >
          <img
            v-if="productImage(item.products)"
            :src="productImage(item.products)"
            :alt="item.products!.name"
            class="h-full w-full object-contain"
          />
          <Heart v-else class="text-slate-300" :size="22" />
        </RouterLink>
        <div class="flex flex-1 flex-col">
          <RouterLink
            :to="`/products/${item.products!.id}`"
            class="line-clamp-2 text-sm font-semibold text-slate-800 hover:text-blue-700"
          >
            {{ item.products!.name }}
          </RouterLink>
          <p class="text-xs text-slate-500">
            {{ item.products!.brand || "UK Used" }}
          </p>
          <p class="mt-1 text-base font-bold text-slate-900">
            {{ formatKES(item.products!.price) }}
          </p>
          <div class="mt-auto flex items-center gap-2 pt-2">
            <button
              class="inline-flex flex-1 items-center justify-center gap-1.5 rounded-full bg-blue-700 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-800"
              @click="addToCart.mutate(item.products!.id)"
            >
              <ShoppingCart :size="14" /> Add
            </button>
            <button
              class="rounded-full p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-500"
              aria-label="Remove from wishlist"
              @click="remove.mutate(item.products!.id)"
            >
              <Trash2 :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
