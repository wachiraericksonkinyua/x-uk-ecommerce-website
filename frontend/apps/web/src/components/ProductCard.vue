<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Heart, ShoppingCart } from "@lucide/vue";
import { RouterLink } from "vue-router";
import { toast } from "vue-sonner";

import { api, errorMessage } from "../lib/api";
import type { Product } from "../lib/types";
import { cn, formatKES, productImage } from "../lib/utils";
import { useRequireAuth } from "../hooks/useRequireAuth";
import { useWishlist } from "../hooks/queries";
import { useAuthStore } from "../store/auth";
import StarRating from "./StarRating.vue";

const props = defineProps<{ product: Product }>();

const requireAuth = useRequireAuth();
const queryClient = useQueryClient();
const auth = useAuthStore();
const { data: wishlist } = useWishlist(() => Boolean(auth.token));

const isWished = computed(() =>
  (wishlist.value ?? []).some((w) => w.products?.id === props.product.id)
);

const addToCart = useMutation({
  mutationFn: () =>
    api.post("/cart/add", { product_id: props.product.id, quantity: 1 }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    toast.success(`${props.product.name} added to cart`);
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const toggleWishlist = useMutation({
  mutationFn: () =>
    isWished.value
      ? api.del(`/wishlist/${props.product.id}`)
      : api.post("/wishlist/", { product_id: props.product.id }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    toast.success(isWished.value ? "Removed from wishlist" : "Saved to wishlist");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const image = computed(() => productImage(props.product));
const stock = computed(() => props.product.stock_quantity ?? 0);
const lowStock = computed(() => stock.value > 0 && stock.value <= 5);
const outOfStock = computed(() => stock.value <= 0);

function handleWishlist() {
  if (requireAuth()) toggleWishlist.mutate();
}

function handleAddToCart() {
  if (requireAuth()) addToCart.mutate();
}
</script>

<template>
  <div
    class="group flex flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-md"
  >
    <div class="relative">
      <RouterLink :to="`/products/${product.id}`" class="block">
        <div
          class="flex aspect-square items-center justify-center overflow-hidden bg-slate-50 p-4"
        >
          <img
            v-if="image"
            :src="image"
            :alt="product.name"
            loading="lazy"
            class="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
          />
          <span v-else class="text-sm text-slate-400">No image</span>
        </div>
      </RouterLink>

      <span class="absolute left-3 top-3">
        <span
          v-if="outOfStock"
          class="rounded-full bg-slate-800 px-2.5 py-1 text-xs font-semibold text-white"
        >
          Out of stock
        </span>
        <span
          v-else-if="lowStock"
          class="rounded-full bg-rose-500 px-2.5 py-1 text-xs font-semibold text-white"
        >
          Only {{ stock }} left
        </span>
        <span
          v-else
          class="rounded-full bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white"
        >
          Best Seller
        </span>
      </span>

      <button
        type="button"
        aria-label="Toggle wishlist"
        :class="
          cn(
            'absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 shadow-sm backdrop-blur transition hover:bg-white',
            isWished ? 'text-rose-500' : 'text-slate-400'
          )
        "
        @click="handleWishlist"
      >
        <Heart :size="18" :class="isWished ? 'fill-rose-500' : ''" />
      </button>
    </div>

    <div class="flex flex-1 flex-col p-4">
      <RouterLink :to="`/products/${product.id}`">
        <h3
          class="line-clamp-2 text-sm font-semibold text-slate-800 hover:text-blue-700"
        >
          {{ product.name }}
        </h3>
      </RouterLink>
      <p class="mt-1 text-xs text-slate-500">
        {{ product.brand || "UK Used" }} &bull; {{ product.color || "Standard" }}
      </p>

      <div class="mt-2 flex items-center gap-1.5">
        <StarRating :value="5" />
      </div>

      <p class="mt-3 text-base font-bold text-slate-900">
        {{ formatKES(product.price) }}
      </p>

      <button
        type="button"
        :disabled="outOfStock || addToCart.isPending.value"
        class="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        @click="handleAddToCart"
      >
        <ShoppingCart :size="16" />
        {{ outOfStock ? "Out of stock" : "Add to Cart" }}
      </button>
    </div>
  </div>
</template>
