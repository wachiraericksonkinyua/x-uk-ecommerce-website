<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import {
  Check,
  CheckCircle2,
  Info,
  MapPin,
  Package,
  ReceiptText,
  Search,
  Truck,
  XCircle,
} from "@lucide/vue";
import { useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useTrackOrder } from "../hooks/queries";
import { useAuthStore } from "../store/auth";
import {
  ORDER_STATUS_STEPS,
  cn,
  formatDate,
  formatKES,
  orderStepIndex,
  statusColor,
} from "../lib/utils";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const queryClient = useQueryClient();

const orderRef = computed(() =>
  typeof route.params.orderRef === "string" ? route.params.orderRef : undefined
);
const search = ref("");
const receipt = ref("");

const { data: order, isLoading, isError, error } = useTrackOrder(orderRef);

const cancelOrder = useMutation({
  mutationFn: (orderId: string) => api.post(`/orders/${orderId}/cancel`),
  onSuccess: () => {
    toast.success("Order cancelled");
    queryClient.invalidateQueries({ queryKey: ["track", orderRef.value] });
  },
  onError: (err) => toast.error(errorMessage(err)),
});

const verifyReceipt = useMutation({
  mutationFn: (receiptNumber: string) =>
    api.post(`/orders/${order.value?.id}/verify-receipt`, {
      receipt_number: receiptNumber,
    }),
  onSuccess: () => {
    toast.success("Payment verified! Your order is confirmed.");
    receipt.value = "";
    queryClient.invalidateQueries({ queryKey: ["track", orderRef.value] });
  },
  onError: (err) => toast.error(errorMessage(err)),
});

function submitSearch() {
  if (search.value.trim()) router.push(`/track/${search.value.trim()}`);
}

function submitReceipt() {
  const code = receipt.value.trim();
  if (code) verifyReceipt.mutate(code);
}

const isPaidOrBeyond = computed(
  () =>
    !!order.value &&
    ["Paid", "Processing", "Shipped", "Delivered"].includes(order.value.status)
);
const isTerminal = computed(
  () =>
    !!order.value &&
    ["Cancelled", "Payment Failed"].includes(order.value.status)
);
const currentStep = computed(() => orderStepIndex(order.value?.status));
const cancellable = computed(
  () =>
    Boolean(auth.token) &&
    !!order.value &&
    ["Pending PIN", "Paid"].includes(order.value.status)
);
const needsManualVerify = computed(
  () =>
    !!order.value &&
    ["Pending PIN", "Payment Failed"].includes(order.value.status)
);
</script>

<template>
  <div v-if="!orderRef" class="mx-auto max-w-xl px-4 py-20">
    <div class="rounded-2xl border border-slate-100 bg-white p-8 text-center shadow-sm">
      <div
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-blue-700"
      >
        <Search :size="26" />
      </div>
      <h1 class="mt-4 text-xl font-bold text-slate-900">Track your order</h1>
      <p class="mt-1 text-sm text-slate-500">
        Enter the order reference you received at checkout (e.g. GWV-A1B2).
      </p>
      <form class="mt-5 flex gap-2" @submit.prevent="submitSearch">
        <input
          v-model="search"
          placeholder="GWV-XXXX"
          class="flex-1 rounded-full border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-500"
        />
        <button
          class="rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Track
        </button>
      </form>
    </div>
  </div>

  <PageLoader v-else-if="isLoading" label="Fetching order…" />

  <div v-else-if="isError || !order" class="mx-auto max-w-3xl px-4 py-16">
    <EmptyState title="Order not found" :description="errorMessage(error)">
      <template #action>
        <button
          class="mt-2 rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
          @click="router.push('/track')"
        >
          Try another reference
        </button>
      </template>
    </EmptyState>
  </div>

  <div v-else class="mx-auto max-w-4xl px-4 py-8 sm:px-6">
    <div
      v-if="isPaidOrBeyond"
      class="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-4"
    >
      <CheckCircle2 class="text-emerald-600" :size="26" />
      <div>
        <p class="font-semibold text-emerald-800">Order Placed Successfully!</p>
        <p class="text-sm text-emerald-600">
          Payment received. We're preparing your order.
        </p>
      </div>
    </div>

    <div
      v-if="!isPaidOrBeyond && !isTerminal"
      class="flex items-center gap-3 rounded-2xl border border-amber-100 bg-amber-50 px-5 py-4"
    >
      <Truck class="text-amber-600" :size="26" />
      <div>
        <p class="font-semibold text-amber-800">Waiting for payment confirmation…</p>
        <p class="text-sm text-amber-600">
          Check your phone and enter your M-Pesa PIN. This page updates
          automatically.
        </p>
      </div>
    </div>

    <div
      v-if="isTerminal"
      class="flex items-center gap-3 rounded-2xl border border-rose-100 bg-rose-50 px-5 py-4"
    >
      <XCircle class="text-rose-600" :size="26" />
      <div>
        <p class="font-semibold text-rose-800">Order {{ order.status }}</p>
        <p class="text-sm text-rose-600">This order is no longer active.</p>
      </div>
    </div>

    <div
      v-if="!isTerminal"
      class="mt-6 flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50 px-5 py-4"
    >
      <Info class="mt-0.5 shrink-0 text-blue-600" :size="22" />
      <div>
        <p class="font-semibold text-blue-800">What happens next?</p>
        <p class="text-sm text-blue-600">
          Our team will call or message you shortly to coordinate your pickup or
          delivery details.
        </p>
      </div>
    </div>

    <div
      v-if="needsManualVerify"
      class="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5"
    >
      <h2 class="flex items-center gap-2 text-sm font-bold text-amber-900">
        <ReceiptText :size="16" /> Already paid?
      </h2>
      <p class="mt-1 text-sm text-amber-700">
        Did you pay via M-Pesa? Paste your M-Pesa message code here (e.g.,
        QHS8X9...)
      </p>
      <form class="mt-3 flex flex-col gap-2 sm:flex-row" @submit.prevent="submitReceipt">
        <input
          v-model="receipt"
          placeholder="e.g. QHS8X9ABCD"
          class="flex-1 rounded-xl border border-amber-200 bg-white px-3 py-2.5 text-sm uppercase tracking-wide outline-none focus:border-amber-500"
        />
        <button
          type="submit"
          :disabled="!receipt.trim() || verifyReceipt.isPending.value"
          class="rounded-xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {{ verifyReceipt.isPending.value ? "Verifying…" : "Verify Payment" }}
        </button>
      </form>
    </div>

    <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ order.order_reference }}</h1>
        <p class="text-sm text-slate-500">Placed {{ formatDate(order.created_at) }}</p>
      </div>
      <span
        :class="
          cn('rounded-full px-3 py-1 text-xs font-semibold', statusColor(order.status))
        "
      >
        {{ order.status }}
      </span>
    </div>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_20rem]">
      <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 class="text-sm font-bold text-slate-900">Order Progress</h2>
        <ol class="mt-5 space-y-1">
          <li
            v-for="(step, index) in ORDER_STATUS_STEPS"
            :key="step.key"
            class="flex gap-3"
          >
            <div class="flex flex-col items-center">
              <span
                :class="
                  cn(
                    'flex h-8 w-8 items-center justify-center rounded-full border-2',
                    currentStep >= index && !isTerminal
                      ? 'border-blue-700 bg-blue-700 text-white'
                      : 'border-slate-200 bg-white text-slate-300'
                  )
                "
              >
                <Check v-if="currentStep >= index && !isTerminal" :size="15" />
                <span v-else class="text-xs font-semibold">{{ index + 1 }}</span>
              </span>
              <span
                v-if="index < ORDER_STATUS_STEPS.length - 1"
                :class="
                  cn(
                    'my-1 h-8 w-0.5',
                    currentStep > index && !isTerminal ? 'bg-blue-700' : 'bg-slate-200'
                  )
                "
              />
            </div>
            <div class="pb-2 pt-1">
              <p
                :class="
                  cn(
                    'text-sm',
                    currentStep === index && !isTerminal
                      ? 'font-semibold text-blue-700'
                      : currentStep >= index && !isTerminal
                        ? 'font-medium text-slate-800'
                        : 'text-slate-400'
                  )
                "
              >
                {{ step.label }}
              </p>
            </div>
          </li>
        </ol>
      </section>

      <section class="space-y-4">
        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <h2 class="flex items-center gap-2 text-sm font-bold text-slate-900">
            <Package :size="16" /> Items
          </h2>
          <div class="mt-3 space-y-3">
            <div
              v-for="item in order.items ?? []"
              :key="item.id"
              class="flex items-center gap-3"
            >
              <div
                class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg bg-slate-50"
              >
                <img
                  v-if="item.image"
                  :src="item.image"
                  :alt="item.name"
                  class="h-full w-full object-contain"
                />
                <Package v-else :size="16" class="text-slate-300" />
              </div>
              <div class="flex-1">
                <p class="line-clamp-1 text-xs font-medium text-slate-700">
                  {{ item.name }}
                </p>
                <p class="text-xs text-slate-400">Qty {{ item.qty }}</p>
              </div>
              <p class="text-xs font-semibold text-slate-800">
                {{ formatKES(item.price * item.qty) }}
              </p>
            </div>
          </div>
          <div class="mt-4 space-y-1 border-t border-slate-100 pt-3 text-sm">
            <div class="flex justify-between text-slate-600">
              <span>Delivery</span>
              <span>{{ formatKES(order.delivery_cost ?? 0) }}</span>
            </div>
            <div class="flex justify-between font-bold text-slate-900">
              <span>Total</span>
              <span>{{ formatKES(order.total_amount) }}</span>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
          <h2 class="flex items-center gap-2 text-sm font-bold text-slate-900">
            <MapPin :size="16" /> Delivery Details
          </h2>
          <dl class="mt-3 space-y-2 text-sm">
            <div class="flex justify-between">
              <dt class="text-slate-500">Fulfillment</dt>
              <dd class="font-medium text-slate-800">
                {{ order.fulfillment || "Delivery" }}
              </dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-slate-500">Location</dt>
              <dd class="font-medium text-slate-800">{{ order.location_name || "—" }}</dd>
            </div>
            <div v-if="order.delivery_address" class="flex justify-between gap-4">
              <dt class="text-slate-500">Address</dt>
              <dd class="text-right font-medium text-slate-800">
                {{ order.delivery_address }}
              </dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-slate-500">Phone</dt>
              <dd class="font-medium text-slate-800">{{ order.customer_phone || "—" }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-slate-500">Payment</dt>
              <dd class="font-medium text-slate-800">
                {{ order.payment_method || "M-Pesa" }}
              </dd>
            </div>
          </dl>

          <button
            v-if="cancellable"
            :disabled="cancelOrder.isPending.value"
            class="mt-4 w-full rounded-full border border-rose-200 px-4 py-2.5 text-sm font-medium text-rose-600 transition hover:bg-rose-50 disabled:opacity-50"
            @click="cancelOrder.mutate(order.id)"
          >
            Cancel Order
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
