<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import {
  CheckCircle2,
  CreditCard,
  MapPin,
  Smartphone,
  Truck,
} from "@lucide/vue";
import { useRouter } from "vue-router";
import { toast } from "vue-sonner";

import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Spinner from "../components/Spinner.vue";
import { api, errorMessage } from "../lib/api";
import { useCart, useDeliveryLocations, useMyProfile } from "../hooks/queries";
import { cn, formatKES, productImage } from "../lib/utils";

interface CheckoutResult {
  status: string;
  message: string;
  order_id: string;
  checkout_request_id?: string;
}

const STEPS = ["Delivery", "M-Pesa Payment", "Confirmation"];

function normalizePhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.startsWith("254")) return digits;
  if (digits.startsWith("0") && digits.length >= 9) return "254" + digits.slice(1);
  if (digits.length === 9) return "254" + digits;
  return digits;
}

const router = useRouter();
const queryClient = useQueryClient();
const { data: cart, isLoading } = useCart(true);
const { data: locations } = useDeliveryLocations();
const { data: profile } = useMyProfile(true);

const cartItems = computed(() => cart.value ?? []);
const locationList = computed(() => locations.value ?? []);

const fulfillment = ref<"Delivery" | "Pickup">("Delivery");
const locationId = ref("");
const address = ref("");
const email = ref("");
const phone = ref("");
const result = ref<CheckoutResult | null>(null);

watch(profile, (value) => {
  if (value?.phone_number && !phone.value) phone.value = value.phone_number;
  if (value?.address && !address.value) address.value = value.address;
});

watch(locationList, (value) => {
  if (!locationId.value && value.length > 0) locationId.value = value[0].id;
});

const itemsTotal = computed(() =>
  cartItems.value.reduce(
    (sum, item) => sum + (item.products?.price ?? 0) * item.quantity,
    0
  )
);

const isPickup = computed(() => fulfillment.value === "Pickup");
const selectedLocation = computed(() =>
  locationList.value.find((location) => location.id === locationId.value)
);
const deliveryCost = computed(() =>
  isPickup.value ? 0 : selectedLocation.value?.cost ?? 0
);
const grandTotal = computed(() => itemsTotal.value + deliveryCost.value);
const canSubmit = computed(
  () =>
    Boolean(phone.value.trim()) &&
    Boolean(email.value.trim()) &&
    (isPickup.value || Boolean(locationId.value && address.value.trim()))
);

let redirectTimer: ReturnType<typeof setTimeout> | undefined;

const checkout = useMutation({
  mutationFn: async () => {
    const items = cartItems.value.map((item) => ({
      id: item.product_id,
      name: item.products?.name ?? "Product",
      price: item.products?.price ?? 0,
      qty: item.quantity,
      image: productImage(item.products),
    }));
    return api.post<CheckoutResult>("/orders/checkout", {
      phone: normalizePhone(phone.value),
      email: email.value,
      fulfillment: fulfillment.value,
      location_id: fulfillment.value === "Delivery" ? locationId.value : null,
      delivery_address: fulfillment.value === "Delivery" ? address.value : null,
      payment_method: "M-Pesa",
      items,
      total: grandTotal.value,
    });
  },
  onSuccess: async (res) => {
    result.value = res;
    toast.success("Order placed! Check your phone for the M-Pesa prompt.");
    await api.del("/cart/").catch(() => undefined);
    queryClient.invalidateQueries({ queryKey: ["cart"] });
    redirectTimer = setTimeout(() => router.push(`/track/${res.order_id}`), 2200);
  },
  onError: (error) => toast.error(errorMessage(error)),
});

onBeforeUnmount(() => clearTimeout(redirectTimer));
</script>

<template>
  <PageLoader v-if="isLoading" label="Preparing checkout…" />

  <div v-else-if="result" class="mx-auto max-w-xl px-4 py-20 text-center">
    <div
      class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-700"
    >
      <Smartphone :size="30" />
    </div>
    <h1 class="mt-5 text-2xl font-bold text-slate-900">Waiting for M-Pesa…</h1>
    <p class="mt-2 text-sm text-slate-500">
      Check your phone and enter your M-Pesa PIN to complete payment for order
      <span class="font-semibold">{{ result.order_id }}</span>.
    </p>
    <div class="mt-6 flex justify-center">
      <Spinner class="h-6 w-6" />
    </div>
    <button
      class="mt-6 rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
      @click="router.push(`/track/${result.order_id}`)"
    >
      View order status
    </button>
  </div>

  <div
    v-else-if="cartItems.length === 0"
    class="mx-auto max-w-3xl px-4 py-16"
  >
    <EmptyState title="Nothing to checkout" description="Your cart is empty.">
      <template #action>
        <button
          class="mt-2 rounded-full bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
          @click="router.push('/shop')"
        >
          Browse products
        </button>
      </template>
    </EmptyState>
  </div>

  <div v-else class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-slate-900">Checkout</h1>

    <div class="mt-6 flex items-center gap-2 text-sm">
      <div v-for="(step, index) in STEPS" :key="step" class="flex items-center gap-2">
        <span
          :class="
            cn(
              'flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold',
              index === 0 ? 'bg-blue-700 text-white' : 'bg-slate-200 text-slate-500'
            )
          "
        >
          {{ index + 1 }}
        </span>
        <span :class="index === 0 ? 'font-semibold text-slate-800' : 'text-slate-500'">
          {{ step }}
        </span>
        <span v-if="index < STEPS.length - 1" class="mx-2 h-px w-8 bg-slate-300" />
      </div>
    </div>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_22rem]">
      <div class="space-y-6">
        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 class="flex items-center gap-2 text-sm font-bold text-slate-900">
            <Truck :size="16" /> Fulfillment
          </h2>
          <div class="mt-4 grid grid-cols-2 gap-3">
            <button
              v-for="option in (['Delivery', 'Pickup'] as const)"
              :key="option"
              :class="
                cn(
                  'rounded-xl border px-4 py-3 text-sm font-medium transition',
                  fulfillment === option
                    ? 'border-blue-600 bg-blue-50 text-blue-700'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                )
              "
              @click="fulfillment = option"
            >
              {{ option }}
            </button>
          </div>

          <div
            v-if="isPickup"
            class="mt-5 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-4"
          >
            <MapPin :size="18" class="mt-0.5 shrink-0 text-emerald-600" />
            <div>
              <p class="text-sm font-semibold text-emerald-800">
                Store Pickup — Free
              </p>
              <p class="mt-0.5 text-xs text-emerald-700">
                Collect from our shop. No delivery fee.
              </p>
            </div>
          </div>

          <template v-else>
            <div class="mt-5">
              <label
                class="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500"
              >
                <MapPin :size="14" /> Delivery Location
              </label>
              <select
                v-model="locationId"
                class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              >
                <option value="">Select a location</option>
                <option
                  v-for="location in locationList"
                  :key="location.id"
                  :value="location.id"
                >
                  {{ location.name }} — {{ formatKES(location.cost) }}
                </option>
              </select>
            </div>

            <div class="mt-4">
              <label class="text-xs font-semibold uppercase text-slate-500">
                Delivery Address
              </label>
              <input
                v-model="address"
                placeholder="e.g. Kilimani, Wood Avenue, Apt 4B"
                class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              />
            </div>
          </template>
        </section>

        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 class="flex items-center gap-2 text-sm font-bold text-slate-900">
            <CreditCard :size="16" /> M-Pesa Payment
          </h2>
          <div class="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase text-slate-500">
                Email
              </label>
              <input
                v-model="email"
                type="email"
                placeholder="you@example.com"
                class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase text-slate-500">
                M-Pesa Phone Number
              </label>
              <input
                v-model="phone"
                placeholder="2547XXXXXXXX"
                class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <p class="mt-3 rounded-xl bg-blue-50 px-3 py-2 text-xs text-blue-700">
            You'll receive an STK Push prompt on your phone. Enter your M-Pesa
            PIN to complete payment.
          </p>
        </section>
      </div>

      <div class="lg:sticky lg:top-20 lg:h-fit">
        <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 class="text-sm font-bold text-slate-900">Your Order</h2>
          <div class="mt-4 max-h-64 space-y-3 overflow-y-auto">
            <div v-for="item in cartItems" :key="item.id" class="flex items-center gap-3">
              <div
                class="flex h-12 w-12 items-center justify-center overflow-hidden rounded-lg bg-slate-50"
              >
                <img
                  v-if="productImage(item.products)"
                  :src="productImage(item.products)"
                  :alt="item.products?.name ?? ''"
                  class="h-full w-full object-contain"
                />
                <Smartphone v-else :size="18" class="text-slate-300" />
              </div>
              <div class="flex-1">
                <p class="line-clamp-1 text-xs font-medium text-slate-700">
                  {{ item.products?.name }}
                </p>
                <p class="text-xs text-slate-400">Qty {{ item.quantity }}</p>
              </div>
              <p class="text-xs font-semibold text-slate-800">
                {{ formatKES((item.products?.price ?? 0) * item.quantity) }}
              </p>
            </div>
          </div>

          <div class="mt-4 space-y-2 border-t border-slate-100 pt-4 text-sm">
            <div class="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span class="font-medium text-slate-900">{{ formatKES(itemsTotal) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>{{ isPickup ? "Pickup" : "Delivery" }}</span>
              <span class="font-medium text-slate-900">
                {{ isPickup ? "Free" : formatKES(deliveryCost) }}
              </span>
            </div>
            <div
              class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold text-slate-900"
            >
              <span>Total</span>
              <span>{{ formatKES(grandTotal) }}</span>
            </div>
          </div>

          <button
            :disabled="!canSubmit || checkout.isPending.value"
            class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            @click="checkout.mutate()"
          >
            <CheckCircle2 :size="18" />
            {{ checkout.isPending.value ? "Placing order…" : "Pay with M-Pesa" }}
          </button>
          <p class="mt-3 text-center text-[11px] text-slate-400">
            Totals are verified by our servers before payment.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
