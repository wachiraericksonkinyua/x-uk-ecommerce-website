<script setup lang="ts">
import { computed } from "vue";
import {
  ArrowRight,
  BadgeCheck,
  Headphones,
  ShieldCheck,
  Smartphone,
  Truck,
} from "@lucide/vue";
import { RouterLink } from "vue-router";

import ProductCard from "../components/ProductCard.vue";
import Spinner from "../components/Spinner.vue";
import { useProducts } from "../hooks/queries";
import { formatKES, productImage } from "../lib/utils";

const BRANDS = ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "realme"];

const TRUST = [
  {
    icon: Truck,
    title: "Fast Countrywide Delivery",
    text: "Nairobi same-day, countrywide in 1–3 days.",
  },
  {
    icon: ShieldCheck,
    title: "100% M-Pesa Verified",
    text: "Secure STK Push checkout, instantly verified.",
  },
  {
    icon: Headphones,
    title: "24/7 Support",
    text: "Chat with our AI assistant or WhatsApp us.",
  },
  {
    icon: BadgeCheck,
    title: "Verified UK Quality",
    text: "Every device tested and graded before sale.",
  },
];

const { data: products, isLoading } = useProducts({
  sort_by: "created_at",
  order: "desc",
});

const popular = computed(() => (products.value ?? []).slice(0, 8));
const deals = computed(() => (products.value ?? []).slice(0, 4));
const featured = computed(() => (products.value ?? []).slice(0, 5));

const marqueeTiles = computed(() => {
  const list = featured.value;
  if (list.length === 0) return [];
  const repeats = Math.max(1, Math.ceil(6 / list.length));
  const half = Array.from({ length: repeats }).flatMap(() => list);
  return [...half, ...half];
});
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
    <section
      class="overflow-hidden rounded-3xl bg-gradient-to-r from-[#061A40] via-[#0B3578] to-[#1565C0] text-white"
    >
      <div
        class="grid items-center gap-8 px-6 py-12 sm:px-10 md:grid-cols-2 md:py-16"
      >
        <div>
          <span
            class="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium"
          >
            <BadgeCheck :size="14" /> Trusted UK-used smartphones
          </span>
          <h1 class="mt-4 text-3xl font-bold leading-tight sm:text-4xl md:text-5xl">
            Premium UK-Used Smartphones. Unbeatable Value.
          </h1>
          <p class="mt-4 max-w-lg text-blue-100">
            Genuine, tested devices at prices that make sense. Pay securely with
            M-Pesa and get fast countrywide delivery.
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <RouterLink
              to="/shop"
              class="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-blue-800 transition hover:bg-blue-50"
            >
              Shop Now <ArrowRight :size="16" />
            </RouterLink>
            <RouterLink
              to="/track"
              class="inline-flex items-center gap-2 rounded-full border border-white/40 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Track your order
            </RouterLink>
          </div>
        </div>

        <div class="-mx-6 sm:-mx-10 md:mx-0">
          <div
            class="relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]"
          >
            <div v-if="featured.length === 0" class="flex w-max gap-4">
              <div
                v-for="n in 5"
                :key="n"
                class="flex h-40 w-28 shrink-0 animate-pulse flex-col items-center justify-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 sm:h-52 sm:w-40"
              >
                <div class="h-16 w-16 rounded-xl bg-white/10 sm:h-24 sm:w-24" />
                <div class="h-3 w-20 rounded-full bg-white/10" />
              </div>
            </div>

            <div
              v-else
              class="relative overflow-hidden py-2 [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]"
            >
              <div
                class="flex w-max animate-marquee gap-4 hover:[animation-play-state:paused]"
              >
                <RouterLink
                  v-for="(product, index) in marqueeTiles"
                  :key="`${product.id}-${index}`"
                  :to="`/products/${product.id}`"
                  class="group relative flex h-40 w-28 shrink-0 flex-col items-center justify-center gap-2 rounded-2xl border border-white/15 bg-white/10 p-3 backdrop-blur transition hover:border-white/30 hover:bg-white/20 sm:h-52 sm:w-40 sm:gap-3"
                >
                  <div class="flex h-20 w-full items-center justify-center sm:h-32">
                    <img
                      v-if="productImage(product)"
                      :src="productImage(product)"
                      :alt="product.name"
                      loading="lazy"
                      class="max-h-full max-w-full object-contain drop-shadow-xl transition-transform duration-300 group-hover:scale-105"
                    />
                    <Smartphone v-else class="text-white/60" :size="38" />
                  </div>
                  <div class="w-full text-center">
                    <p class="line-clamp-1 text-xs font-semibold text-white">
                      {{ product.name }}
                    </p>
                    <p class="text-[11px] text-blue-100">
                      {{ formatKES(product.price) }}
                    </p>
                  </div>
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="item in TRUST"
        :key="item.title"
        class="flex items-start gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
      >
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700"
        >
          <component :is="item.icon" :size="20" />
        </span>
        <div>
          <p class="text-sm font-semibold text-slate-800">{{ item.title }}</p>
          <p class="mt-0.5 text-xs text-slate-500">{{ item.text }}</p>
        </div>
      </div>
    </section>

    <section class="mt-12">
      <div class="flex items-end justify-between">
        <h2 class="text-xl font-bold text-slate-900">Popular Smartphones</h2>
        <RouterLink
          to="/shop"
          class="text-sm font-medium text-blue-700 hover:underline"
        >
          View all
        </RouterLink>
      </div>
      <div v-if="isLoading" class="flex justify-center py-16">
        <Spinner class="h-8 w-8" />
      </div>
      <div v-else class="mt-5 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <ProductCard
          v-for="product in popular"
          :key="product.id"
          :product="product"
        />
      </div>
    </section>

    <section class="mt-12">
      <h2 class="text-xl font-bold text-slate-900">Shop by Brand</h2>
      <div class="mt-4 flex flex-wrap gap-3">
        <RouterLink
          v-for="brand in BRANDS"
          :key="brand"
          :to="`/shop?brand=${encodeURIComponent(brand)}`"
          class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-700"
        >
          {{ brand }}
        </RouterLink>
      </div>
    </section>

    <section v-if="deals.length > 0" class="mt-12">
      <div class="flex items-end justify-between">
        <h2 class="text-xl font-bold text-slate-900">Best Deals</h2>
        <RouterLink
          to="/shop"
          class="text-sm font-medium text-blue-700 hover:underline"
        >
          View all
        </RouterLink>
      </div>
      <div class="mt-5 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="product in deals" :key="product.id" :product="product" />
      </div>
    </section>

    <section
      class="mt-12 grid gap-6 rounded-3xl border border-slate-100 bg-white p-8 shadow-sm md:grid-cols-2 md:items-center"
    >
      <div>
        <h2 class="text-xl font-bold text-slate-900">
          Can't find what you need?
        </h2>
        <p class="mt-2 text-sm text-slate-500">
          Message us on WhatsApp and our team will source the exact device you
          want. Get notified about new arrivals and exclusive offers.
        </p>
      </div>
      <div class="flex justify-start md:justify-end">
        <a
          href="https://wa.me/254112323814"
          target="_blank"
          rel="noreferrer"
          class="inline-flex items-center gap-2 rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
        >
          Chat on WhatsApp
        </a>
      </div>
    </section>
  </div>
</template>
