<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import {
  Heart,
  Minus,
  Package,
  Palette,
  Plus,
  ShieldCheck,
  ShoppingCart,
  Tag,
} from "@lucide/vue";
import { useRoute } from "vue-router";
import { toast } from "vue-sonner";

import PageLoader from "../components/PageLoader.vue";
import EmptyState from "../components/EmptyState.vue";
import StarRating from "../components/StarRating.vue";
import { api, errorMessage } from "../lib/api";
import { useProduct, useReviews } from "../hooks/queries";
import { useRequireAuth } from "../hooks/useRequireAuth";
import { cn, formatDate, formatKES, productImage } from "../lib/utils";

const route = useRoute();
const requireAuth = useRequireAuth();
const queryClient = useQueryClient();

const id = computed(() => route.params.id as string | undefined);

const { data: product, isLoading, isError } = useProduct(id);
const { data: reviews } = useReviews(id);
const reviewList = computed(() => reviews.value ?? []);

const activeImage = ref(0);
const quantity = ref(1);
const rating = ref(5);
const comment = ref("");

const addToCart = useMutation({
  mutationFn: () => api.post("/cart/add", { product_id: id.value, quantity: quantity.value }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    toast.success("Added to cart");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const addReview = useMutation({
  mutationFn: () =>
    api.post("/reviews/", {
      product_id: id.value,
      rating: rating.value,
      comment: comment.value.trim(),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["reviews", id.value] });
    comment.value = "";
    rating.value = 5;
    toast.success("Thanks for your review!");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const images = computed(() => {
  const current = product.value;
  if (!current) return [];
  if (current.product_images && current.product_images.length > 0) {
    return current.product_images.map((image) => image.image_url);
  }
  return productImage(current) ? [productImage(current)] : [];
});

const stock = computed(() => product.value?.stock_quantity ?? 0);
const outOfStock = computed(() => stock.value <= 0);
const averageRating = computed(() =>
  reviewList.value.length > 0
    ? reviewList.value.reduce((sum, review) => sum + review.rating, 0) /
      reviewList.value.length
    : 5
);

const infoPills = computed(() => [
  { icon: Tag, label: "Brand", value: product.value?.brand || "UK Used" },
  { icon: Palette, label: "Color", value: product.value?.color || "Standard" },
  { icon: Package, label: "Stock", value: `${stock.value} available` },
  {
    icon: ShieldCheck,
    label: "Category",
    value: product.value?.category || "Smartphones",
  },
]);

function decreaseQuantity() {
  quantity.value = Math.max(1, quantity.value - 1);
}

function increaseQuantity() {
  quantity.value = Math.min(Math.max(1, stock.value), quantity.value + 1);
}

function handleAddToCart() {
  if (requireAuth()) addToCart.mutate();
}

function handleAddReview() {
  if (requireAuth()) addReview.mutate();
}

async function addToWishlist() {
  if (!requireAuth() || !product.value) return;
  try {
    await api.post("/wishlist/", { product_id: product.value.id });
    queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    toast.success("Saved to wishlist");
  } catch (error) {
    toast.error(errorMessage(error));
  }
}
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading product…" />

  <div v-else-if="isError || !product" class="mx-auto max-w-3xl px-4 py-16">
    <EmptyState
      title="Product not found"
      description="This product may have been removed."
    />
  </div>

  <div v-else class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
    <div class="grid gap-10 lg:grid-cols-2">
      <div class="flex gap-4">
        <div class="flex w-20 shrink-0 flex-col gap-3">
          <button
            v-for="(image, index) in images"
            :key="index"
            :class="
              cn(
                'flex aspect-square items-center justify-center overflow-hidden rounded-xl border bg-white p-1 transition',
                activeImage === index
                  ? 'border-blue-600 ring-1 ring-blue-600'
                  : 'border-slate-200 hover:border-slate-300'
              )
            "
            @click="activeImage = index"
          >
            <img
              :src="image"
              :alt="`${product.name} view ${index + 1}`"
              class="h-full w-full object-contain"
            />
          </button>
        </div>

        <div
          class="flex flex-1 items-center justify-center rounded-2xl border border-slate-100 bg-white p-6 shadow-sm"
        >
          <img
            v-if="images.length > 0"
            :src="images[activeImage]"
            :alt="product.name"
            class="max-h-[26rem] w-full object-contain"
          />
          <span v-else class="text-slate-400">No image available</span>
        </div>
      </div>

      <div>
        <h1 class="text-2xl font-bold text-slate-900 sm:text-3xl">
          {{ product.name }}
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          {{ product.brand || "UK Used" }} &bull; {{ product.color || "Standard" }}
        </p>

        <div class="mt-3 flex items-center gap-2">
          <StarRating :value="averageRating" />
          <span class="text-sm text-slate-500">
            ({{ reviewList.length }} review{{ reviewList.length === 1 ? "" : "s" }})
          </span>
        </div>

        <p class="mt-4 text-3xl font-bold text-slate-900">
          {{ formatKES(product.price) }}
        </p>

        <p class="mt-4 whitespace-pre-line text-sm leading-relaxed text-slate-600">
          {{ product.description || "No description provided for this product." }}
        </p>

        <div class="mt-6 grid grid-cols-2 gap-3">
          <div
            v-for="pill in infoPills"
            :key="pill.label"
            class="flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2"
          >
            <span class="text-blue-700">
              <component :is="pill.icon" :size="16" />
            </span>
            <div>
              <p class="text-[11px] uppercase tracking-wide text-slate-400">
                {{ pill.label }}
              </p>
              <p class="text-sm font-medium text-slate-700">{{ pill.value }}</p>
            </div>
          </div>
        </div>

        <div class="mt-8 flex flex-wrap items-center gap-4">
          <div class="flex items-center rounded-full border border-slate-200 bg-white">
            <button
              class="flex h-11 w-11 items-center justify-center rounded-l-full text-slate-600 hover:bg-slate-50"
              aria-label="Decrease quantity"
              @click="decreaseQuantity"
            >
              <Minus :size="16" />
            </button>
            <span class="w-10 text-center text-sm font-semibold">
              {{ quantity }}
            </span>
            <button
              class="flex h-11 w-11 items-center justify-center rounded-r-full text-slate-600 hover:bg-slate-50"
              aria-label="Increase quantity"
              @click="increaseQuantity"
            >
              <Plus :size="16" />
            </button>
          </div>

          <button
            :disabled="outOfStock || addToCart.isPending.value"
            class="inline-flex items-center gap-2 rounded-full bg-blue-700 px-8 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            @click="handleAddToCart"
          >
            <ShoppingCart :size="18" />
            {{ outOfStock ? "Out of stock" : "Add to Cart" }}
          </button>

          <button
            class="flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:border-rose-200 hover:text-rose-500"
            aria-label="Add to wishlist"
            @click="addToWishlist"
          >
            <Heart :size="18" />
          </button>
        </div>
      </div>
    </div>

    <section class="mt-14">
      <h2 class="text-xl font-bold text-slate-900">Customer Reviews</h2>

      <div class="mt-5 grid gap-8 lg:grid-cols-[1fr_20rem]">
        <div class="space-y-4">
          <p
            v-if="reviewList.length === 0"
            class="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500"
          >
            No reviews yet. Be the first verified buyer to review this product.
          </p>
          <template v-else>
            <div
              v-for="review in reviewList"
              :key="review.id"
              class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"
            >
              <div class="flex items-center justify-between">
                <StarRating :value="review.rating" />
                <span class="text-xs text-slate-400">
                  {{ formatDate(review.created_at) }}
                </span>
              </div>
              <p class="mt-2 text-sm text-slate-600">{{ review.comment }}</p>
            </div>
          </template>
        </div>

        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <h3 class="text-sm font-bold text-slate-900">Write a Review</h3>
          <p class="mt-1 text-xs text-slate-500">
            Only verified buyers can review this product.
          </p>

          <div class="mt-4">
            <label class="text-xs font-semibold uppercase text-slate-500">
              Rating
            </label>
            <div class="mt-2 flex gap-1">
              <button
                v-for="value in [1, 2, 3, 4, 5]"
                :key="value"
                type="button"
                :class="
                  cn(
                    'flex h-9 w-9 items-center justify-center rounded-lg border text-sm font-semibold transition',
                    value <= rating
                      ? 'border-amber-300 bg-amber-50 text-amber-600'
                      : 'border-slate-200 text-slate-400'
                  )
                "
                @click="rating = value"
              >
                {{ value }}
              </button>
            </div>
          </div>

          <textarea
            v-model="comment"
            rows="4"
            placeholder="Share your experience…"
            class="mt-4 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-blue-500"
          />
          <button
            :disabled="!comment.trim() || addReview.isPending.value"
            class="mt-3 w-full rounded-full bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            @click="handleAddReview"
          >
            {{ addReview.isPending.value ? "Submitting…" : "Submit Review" }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
