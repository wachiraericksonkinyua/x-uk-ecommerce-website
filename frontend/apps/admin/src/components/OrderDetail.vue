<script setup lang="ts">
import type { Order } from "../lib/types";
import { formatKES } from "../lib/utils";

defineProps<{ order: Order }>();
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-3 sm:grid-cols-2">
      <div class="rounded-xl bg-slate-50 p-3">
        <p class="text-xs uppercase text-slate-400">Customer</p>
        <p class="text-sm font-medium text-slate-800">
          {{ order.customer_email || "—" }}
        </p>
        <p class="text-sm text-slate-500">{{ order.customer_phone || "—" }}</p>
      </div>
      <div class="rounded-xl bg-slate-50 p-3">
        <p class="text-xs uppercase text-slate-400">Fulfillment</p>
        <p class="text-sm font-medium text-slate-800">
          {{ order.fulfillment || "Delivery" }} — {{ order.location_name || "—" }}
        </p>
        <p class="text-sm text-slate-500">
          {{ order.delivery_address || "No address" }}
        </p>
      </div>
    </div>

    <div>
      <p class="mb-2 text-xs font-semibold uppercase text-slate-500">Items</p>
      <div class="space-y-2">
        <div
          v-for="item in order.items ?? []"
          :key="item.id"
          class="flex items-center justify-between rounded-xl border border-slate-100 p-3 text-sm"
        >
          <span class="text-slate-700">{{ item.name }} × {{ item.qty }}</span>
          <span class="font-medium text-slate-900">
            {{ formatKES(item.price * item.qty) }}
          </span>
        </div>
      </div>
    </div>

    <div class="space-y-1 border-t border-slate-100 pt-3 text-sm">
      <div class="flex justify-between text-slate-600">
        <span>Delivery</span>
        <span>{{ formatKES(order.delivery_cost ?? 0) }}</span>
      </div>
      <div class="flex justify-between font-bold text-slate-900">
        <span>Total</span>
        <span>{{ formatKES(order.total_amount) }}</span>
      </div>
      <div v-if="order.receipt_number" class="flex justify-between text-slate-600">
        <span>M-Pesa Receipt</span>
        <span class="font-mono">{{ order.receipt_number }}</span>
      </div>
    </div>

    <div class="rounded-xl border border-slate-100 bg-slate-50 p-3 text-sm">
      <p class="text-xs font-semibold uppercase text-slate-400">Risk review</p>
      <p class="mt-1 text-slate-700">
        {{ order.is_verified ? "Verified by admin" : "Not verified yet" }}
      </p>
      <p v-if="order.verification_note" class="mt-1 text-xs text-slate-500">
        Note: {{ order.verification_note }}
      </p>
      <p v-if="order.verified_at" class="mt-1 text-xs text-slate-400">
        Verified {{ order.verified_at }}
      </p>
    </div>

    <div v-if="order.status === 'Refunded'" class="rounded-xl border border-brand-blue-200 bg-brand-blue-50 p-3 text-sm">
      <p class="text-xs font-semibold uppercase text-brand-blue-700">Refund</p>
      <p class="mt-1 text-slate-700">
        Amount: {{ formatKES(order.refund_amount ?? order.total_amount) }}
      </p>
      <p v-if="order.refund_reason" class="mt-1 text-xs text-slate-500">
        Reason: {{ order.refund_reason }}
      </p>
    </div>
  </div>
</template>
