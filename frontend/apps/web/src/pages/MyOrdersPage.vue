<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Package } from "@lucide/vue";
import { RouterLink } from "vue-router";
import { toast } from "vue-sonner";

import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useMyOrders } from "../hooks/queries";
import { cn, formatDate, formatKES, statusColor } from "../lib/utils";

const queryClient = useQueryClient();
const { data: orders, isLoading } = useMyOrders(true);
const orderList = computed(() => orders.value ?? []);

const cancelOrder = useMutation({
  mutationFn: (orderId: string) => api.post(`/orders/${orderId}/cancel`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    toast.success("Order cancelled");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function isCancellable(status: string) {
  return ["Pending PIN", "Paid"].includes(status);
}
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading your orders…" />

  <div v-else-if="orderList.length === 0" class="mx-auto max-w-3xl px-4 py-16">
    <EmptyState
      title="No orders yet"
      description="When you place an order it will appear here."
    >
      <template #icon>
        <Package class="text-slate-300" :size="40" />
      </template>
      <template #action>
        <RouterLink
          to="/shop"
          class="mt-2 rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Start shopping
        </RouterLink>
      </template>
    </EmptyState>
  </div>

  <div v-else class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-slate-900">My Orders</h1>

    <div class="mt-6 space-y-4">
      <div
        v-for="order in orderList"
        :key="order.id"
        class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"
      >
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <RouterLink
              :to="`/track/${order.order_reference}`"
              class="font-semibold text-slate-900 hover:text-blue-700"
            >
              {{ order.order_reference }}
            </RouterLink>
            <p class="text-sm text-slate-500">
              {{ formatDate(order.created_at) }}
            </p>
          </div>
          <span
            :class="
              cn(
                'rounded-full px-3 py-1 text-xs font-semibold',
                statusColor(order.status)
              )
            "
          >
            {{ order.status }}
          </span>
        </div>

        <div class="mt-4 space-y-2">
          <div
            v-for="item in order.items ?? []"
            :key="item.id"
            class="flex items-center justify-between text-sm"
          >
            <span class="text-slate-600">{{ item.name }} × {{ item.qty }}</span>
            <span class="font-medium text-slate-800">
              {{ formatKES(item.price * item.qty) }}
            </span>
          </div>
        </div>

        <div
          class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4"
        >
          <p class="text-base font-bold text-slate-900">
            {{ formatKES(order.total_amount) }}
          </p>
          <div class="flex gap-2">
            <RouterLink
              :to="`/track/${order.order_reference}`"
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-blue-200 hover:text-blue-700"
            >
              Track
            </RouterLink>
            <button
              v-if="isCancellable(order.status)"
              :disabled="cancelOrder.isPending.value"
              class="rounded-full border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
              @click="cancelOrder.mutate(order.id)"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
