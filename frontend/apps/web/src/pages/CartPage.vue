<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Minus, Plus, ShoppingBag, Trash2 } from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useCart } from "../hooks/queries";
import { formatKES, productImage } from "../lib/utils";

const router = useRouter();
const queryClient = useQueryClient();
const { data: cart, isLoading } = useCart(true);

const cartItems = computed(() => cart.value ?? []);

const updateItem = useMutation({
  mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
    api.patch(`/cart/${itemId}`, { quantity }),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
  onError: (error) => toast.error(errorMessage(error)),
});

const removeItem = useMutation({
  mutationFn: (itemId: string) => api.del(`/cart/${itemId}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    toast.success("Removed from cart");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const subtotal = computed(() =>
  cartItems.value.reduce(
    (sum, item) => sum + (item.products?.price ?? 0) * item.quantity,
    0
  )
);
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading your cart…" />

  <div v-else-if="cartItems.length === 0" class="mx-auto max-w-3xl px-4 py-16">
    <EmptyState
      title="Your cart is empty"
      description="Browse our catalogue and add your favourite smartphones."
    >
      <template #icon>
        <ShoppingBag class="text-slate-300" :size="40" />
      </template>
      <template #action>
        <RouterLink
          to="/shop"
          class="mt-2 inline-flex rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Start shopping
        </RouterLink>
      </template>
    </EmptyState>
  </div>

  <div v-else class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-slate-900">Your Cart</h1>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_22rem]">
      <div class="space-y-4">
        <div
          v-for="item in cartItems"
          :key="item.id"
          class="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
        >
          <div
            class="flex h-20 w-20 items-center justify-center overflow-hidden rounded-xl bg-slate-50"
          >
            <img
              v-if="productImage(item.products)"
              :src="productImage(item.products)"
              :alt="item.products?.name ?? 'Product'"
              class="h-full w-full object-contain"
            />
            <ShoppingBag v-else class="text-slate-300" :size="24" />
          </div>

          <div class="min-w-[8rem] flex-1">
            <RouterLink
              :to="`/products/${item.product_id}`"
              class="text-sm font-semibold text-slate-800 hover:text-blue-700"
            >
              {{ item.products?.name ?? "Product" }}
            </RouterLink>
            <p class="text-xs text-slate-500">
              {{ item.products?.brand || "UK Used" }} &bull;
              {{ item.products?.color || "Standard" }}
            </p>
            <p class="mt-1 text-sm font-bold text-slate-900">
              {{ formatKES(item.products?.price ?? 0) }}
            </p>
          </div>

          <div class="flex items-center rounded-full border border-slate-200">
            <button
              class="flex h-9 w-9 items-center justify-center rounded-l-full text-slate-600 hover:bg-slate-50"
              aria-label="Decrease"
              @click="
                updateItem.mutate({
                  itemId: item.id,
                  quantity: Math.max(1, item.quantity - 1),
                })
              "
            >
              <Minus :size="15" />
            </button>
            <span class="w-9 text-center text-sm font-semibold">
              {{ item.quantity }}
            </span>
            <button
              class="flex h-9 w-9 items-center justify-center rounded-r-full text-slate-600 hover:bg-slate-50"
              aria-label="Increase"
              @click="
                updateItem.mutate({ itemId: item.id, quantity: item.quantity + 1 })
              "
            >
              <Plus :size="15" />
            </button>
          </div>

          <p class="w-24 text-right text-sm font-bold text-slate-900">
            {{ formatKES((item.products?.price ?? 0) * item.quantity) }}
          </p>

          <button
            class="rounded-full p-2 text-slate-400 transition hover:bg-rose-50 hover:text-rose-500"
            aria-label="Remove item"
            @click="removeItem.mutate(item.id)"
          >
            <Trash2 :size="18" />
          </button>
        </div>
      </div>

      <div class="lg:sticky lg:top-20 lg:h-fit">
        <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 class="text-sm font-bold text-slate-900">Order Summary</h2>
          <div class="mt-4 space-y-2 text-sm">
            <div class="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span class="font-medium text-slate-900">{{ formatKES(subtotal) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>Delivery</span>
              <span class="text-slate-500">Calculated at checkout</span>
            </div>
          </div>
          <div
            class="mt-4 flex justify-between border-t border-slate-100 pt-4 text-base font-bold text-slate-900"
          >
            <span>Estimated total</span>
            <span>{{ formatKES(subtotal) }}</span>
          </div>
          <button
            class="mt-5 w-full rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
            @click="router.push('/checkout')"
          >
            Proceed to Checkout
          </button>
          <RouterLink
            to="/shop"
            class="mt-3 block text-center text-sm font-medium text-blue-700 hover:underline"
          >
            Continue shopping
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
