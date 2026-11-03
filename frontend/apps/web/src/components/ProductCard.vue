<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Heart, ShoppingCart } from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import { api, errorMessage } from "../lib/api";
import type { Product } from "../lib/types";
import { cn, formatKES, productImage } from "../lib/utils";
import { useRequireAuth } from "../hooks/useRequireAuth";
import { useWishlist } from "../hooks/queries";
import { useAuthStore } from "../store/auth";
import StarRating from "./StarRating.vue";

const props = defineProps<{ product: Product }>();

const router = useRouter();
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

const buyNow = useMutation({
  mutationFn: () =>
    api.post("/cart/add", { product_id: props.product.id, quantity: 1 }),
  onSuccess: async () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    toast.success("Added to cart");
    await router.push("/checkout");
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
const category = computed(
  () => props.product.category || props.product.brand || "Electronics"
);
const reviewCount = computed(() => props.product.review_count ?? 0);
const rating = computed(() => {
  const value = props.product.average_rating;
  return typeof value === "number" && value > 0 ? value : 5;
});

function handleWishlist() {
  if (requireAuth()) toggleWishlist.mutate();
}

function handleAddToCart() {
  if (requireAuth()) addToCart.mutate();
}

function handleBuyNow() {
  if (requireAuth()) buyNow.mutate();
}
</script>

<template>
  <div class="card-lift group flex flex-col rounded-2xl border border-slate-100 bg-slate-50 p-3 sm:p-4">
    <div class="relative">
      <RouterLink :to="`/products/${product.id}`" class="block">
        <div
          class="flex aspect-square items-center justify-center overflow-hidden rounded-xl bg-white p-3"
        >
          <img
            v-if="image"
            :src="image"
            :alt="product.name"
            loading="lazy"
            class="h-full w-full object-contain transition-transform duration-500 group-hover:scale-105"
          />
          <span v-else class="text-sm text-slate-400">No image</span>
        </div>
      </RouterLink>

      <span class="absolute left-2 top-2 flex flex-col gap-1">
        <span
          v-if="outOfStock"
          class="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-white"
        >
          Out of stock
        </span>
        <span
          v-else-if="lowStock"
          class="rounded-full bg-rose-500 px-2 py-0.5 text-[10px] font-semibold text-white"
        >
          Only {{ stock }} left
        </span>
      </span>

      <span
        class="absolute right-2 top-2 max-w-[60%] truncate rounded-full bg-white/95 px-2.5 py-1 text-[10px] font-semibold text-slate-600 shadow-sm backdrop-blur"
      >
        {{ category }}
      </span>

      <button
        type="button"
        aria-label="Toggle wishlist"
        :class="
          cn(
            'absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-white/95 shadow-sm backdrop-blur transition hover:scale-105',
            isWished ? 'text-rose-500' : 'text-slate-400'
          )
        "
        @click="handleWishlist"
      >
        <Heart :size="16" :class="isWished ? 'fill-rose-500' : ''" />
      </button>
    </div>

    <div class="mt-3 flex-1">
      <div class="flex items-start justify-between gap-2">
        <RouterLink :to="`/products/${product.id}`" class="min-w-0 flex-1">
          <h3 class="line-clamp-2 text-sm font-semibold leading-snug text-slate-900 transition hover:text-brand-orange">
            {{ product.name }}
          </h3>
        </RouterLink>
        <p class="shrink-0 text-sm font-black text-slate-900">
          {{ formatKES(product.price) }}
        </p>
      </div>

      <div class="mt-2 flex items-center gap-1.5">
        <StarRating :value="rating" />
        <span class="text-[10px] text-slate-400">
          {{ reviewCount }} review{{ reviewCount === 1 ? "" : "s" }}
        </span>
      </div>
    </div>

    <div class="mt-3 grid grid-cols-2 gap-2">
      <button
        type="button"
        :disabled="outOfStock || addToCart.isPending.value"
        class="inline-flex items-center justify-center gap-1.5 rounded-full border border-slate-300 bg-white px-3 py-2 text-[11px] font-semibold text-slate-700 transition hover:border-brand-orange hover:text-brand-orange disabled:cursor-not-allowed disabled:opacity-40"
        @click="handleAddToCart"
      >
        <ShoppingCart :size="14" /> Add
      </button>
      <button
        type="button"
        :disabled="outOfStock || buyNow.isPending.value"
        class="inline-flex items-center justify-center rounded-full bg-slate-900 px-3 py-2 text-[11px] font-semibold text-white transition hover:bg-brand-orange disabled:cursor-not-allowed disabled:bg-slate-300"
        @click="handleBuyNow"
      >
        Buy Now
      </button>
    </div>
  </div>
</template>
