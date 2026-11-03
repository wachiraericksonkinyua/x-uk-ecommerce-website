<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Package,
  ShoppingCart,
} from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import ProductCard from "../components/ProductCard.vue";
import Spinner from "../components/Spinner.vue";
import { api, errorMessage } from "../lib/api";
import { useCategories, useProducts } from "../hooks/queries";
import { useRequireAuth } from "../hooks/useRequireAuth";
import { formatKES, productImage } from "../lib/utils";

const BRANDS = [
  "Apple",
  "Samsung",
  "Google",
  "OnePlus",
  "Xiaomi",
  "realme",
  "Anker",
  "JBL",
  "Sony",
];

const STANDARD_CATEGORIES = [
  "Smartphones",
  "Headphones & Earphones",
  "Chargers & Cables",
  "Power Banks",
  "Smartwatches",
];

const CATEGORY_LABELS: Record<string, string> = {
  "Smartwatches & Wearables": "Smartwatches",
};

const TICKER = ["Same-Day Nairobi Delivery", "Tested UK Quality", "Direct Support"];

const router = useRouter();
const queryClient = useQueryClient();
const requireAuth = useRequireAuth();

const { data: products, isLoading } = useProducts({
  sort_by: "created_at",
  order: "desc",
});
const { data: categories } = useCategories();

const popular = computed(() => (products.value ?? []).slice(0, 8));
const deals = computed(() => (products.value ?? []).slice(0, 4));
const heroProducts = computed(() => (products.value ?? []).slice(0, 5));

const activeIndex = ref(0);
const activeProduct = computed(() => heroProducts.value[activeIndex.value]);

const AUTO_ADVANCE_MS = 5000;
const autoPaused = ref(false);
let autoTimer: ReturnType<typeof setInterval> | undefined;

function stopAutoAdvance() {
  if (autoTimer !== undefined) {
    clearInterval(autoTimer);
    autoTimer = undefined;
  }
}

function startAutoAdvance() {
  stopAutoAdvance();
  if (autoPaused.value || heroProducts.value.length < 2) return;

  autoTimer = setInterval(() => {
    if (!autoPaused.value && heroProducts.value.length > 1) {
      activeIndex.value = (activeIndex.value + 1) % heroProducts.value.length;
    }
  }, AUTO_ADVANCE_MS);
}

function pauseAutoAdvance() {
  autoPaused.value = true;
  stopAutoAdvance();
}

function resumeAutoAdvance() {
  autoPaused.value = false;
  startAutoAdvance();
}

watch(heroProducts, (list) => {
  if (activeIndex.value >= list.length) activeIndex.value = 0;
  startAutoAdvance();
});

onMounted(startAutoAdvance);
onBeforeUnmount(stopAutoAdvance);

const categoryPills = computed(() => {
  const live = (categories.value ?? []).map((category) => ({
    label: CATEGORY_LABELS[category.name] ?? category.name,
    name: category.name,
  }));
  const list = live.length
    ? live
    : STANDARD_CATEGORIES.map((name) => ({ label: name, name }));
  return list.slice(0, 5);
});

const railProducts = computed(() => {
  const list = heroProducts.value;
  if (list.length === 0) return [];
  const repeats = Math.max(1, Math.ceil(4 / list.length));
  return Array.from({ length: repeats }).flatMap(() => list);
});

const activeCategory = computed(
  () => activeProduct.value?.category || "Electronics"
);

const watermark = computed(() => {
  const name = activeProduct.value?.name || "X-UK";
  return name.split(" ")[0]?.replace(/[^A-Za-z0-9]/g, "").toUpperCase() || "X-UK";
});

const specPills = computed(() => {
  const product = activeProduct.value;
  if (!product) return [];
  const pills: string[] = [];
  if (product.compatibility) {
    pills.push(
      ...product.compatibility
        .split(/[/,|]/)
        .map((value) => value.trim())
        .filter(Boolean)
    );
  }
  const specs = product.specs;
  if (specs && typeof specs === "object") {
    for (const [key, value] of Object.entries(specs)) {
      if (value === null || value === undefined || value === "") continue;
      if (typeof value === "object") continue;
      pills.push(`${key}: ${String(value)}`);
      if (pills.length >= 4) break;
    }
  }
  if (pills.length === 0) {
    if (product.brand) pills.push(product.brand);
    if (product.color) pills.push(product.color);
  }
  return pills.slice(0, 4);
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

function addActiveToCart() {
  if (!activeProduct.value) return;
  if (requireAuth()) addToCart.mutate(activeProduct.value.id);
}

function previousSlide() {
  const total = heroProducts.value.length;
  if (total === 0) return;
  activeIndex.value = (activeIndex.value - 1 + total) % total;
  startAutoAdvance();
}

function nextSlide() {
  const total = heroProducts.value.length;
  if (total === 0) return;
  activeIndex.value = (activeIndex.value + 1) % total;
  startAutoAdvance();
}

function selectSlide(index: number) {
  activeIndex.value = index;
  startAutoAdvance();
}

function shopCategory(name: string) {
  router.push(`/shop?category=${encodeURIComponent(name)}`);
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
    <!-- Desktop editorial split-stage hero -->
    <section
      class="hidden lg:grid min-h-[80vh] grid-cols-12 items-center gap-6"
      @mouseenter="pauseAutoAdvance"
      @mouseleave="resumeAutoAdvance"
    >
      <aside class="col-span-2 h-[560px] overflow-hidden">
        <div class="grid h-full grid-cols-2 gap-3">
          <div class="relative h-full overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_8%,black_92%,transparent)]">
            <div class="animate-marquee-up flex flex-col hover:[animation-play-state:paused]">
              <div v-for="group in 2" :key="`cat-group-${group}`" class="flex shrink-0 flex-col gap-3 pb-3">
                <button
                  v-for="pill in categoryPills"
                  :key="`${group}-${pill.name}`"
                  class="rounded-2xl border border-slate-100 bg-white px-3 py-3 text-left text-[11px] font-semibold leading-snug text-slate-600 shadow-sm transition hover:border-brand-orange hover:text-brand-orange"
                  @click="shopCategory(pill.name)"
                >
                  {{ pill.label }}
                </button>
              </div>
            </div>
          </div>

          <div class="relative h-full overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_8%,black_92%,transparent)]">
            <div class="animate-marquee-down flex flex-col hover:[animation-play-state:paused]">
              <div v-for="group in 2" :key="`thumb-group-${group}`" class="flex shrink-0 flex-col gap-3 pb-3">
                <button
                  v-for="(product, index) in railProducts"
                  :key="`${group}-${product.id}-${index}`"
                  class="group rounded-2xl border border-slate-100 bg-slate-50 p-2 text-left transition hover:border-brand-blue-300 hover:bg-white"
                  @click="selectSlide(index % Math.max(1, heroProducts.length))"
                >
                  <div class="flex aspect-square items-center justify-center overflow-hidden rounded-xl bg-white">
                    <img
                      v-if="productImage(product)"
                      :src="productImage(product)"
                      :alt="product.name"
                      class="h-full w-full object-contain p-1 transition-transform duration-300 group-hover:scale-105"
                    />
                    <Package v-else :size="22" class="text-slate-300" />
                  </div>
                  <p class="mt-2 line-clamp-1 text-[10px] font-semibold text-slate-600">
                    {{ product.name }}
                  </p>
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <div class="relative col-span-6 flex min-h-[560px] items-center justify-center">
        <span
          class="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 select-none text-center text-[8rem] font-black uppercase leading-none tracking-tighter text-slate-900/5"
          aria-hidden="true"
        >
          {{ watermark }}
        </span>

        <button
          class="absolute left-0 top-1/2 z-20 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-600 shadow-sm backdrop-blur transition hover:border-brand-orange hover:text-brand-orange"
          aria-label="Previous slide"
          @click="previousSlide"
        >
          <ChevronLeft :size="20" />
        </button>

        <Transition name="hero-slide" mode="out-in">
          <RouterLink
            v-if="activeProduct"
            :key="activeProduct.id"
            :to="`/products/${activeProduct.id}`"
            class="relative z-10 flex max-h-[460px] w-full items-center justify-center px-12"
          >
            <img
              v-if="productImage(activeProduct)"
              :src="productImage(activeProduct)"
              :alt="activeProduct.name"
              class="max-h-[420px] w-auto max-w-full object-contain drop-shadow-2xl"
            />
            <div v-else class="flex h-[320px] w-full items-center justify-center text-slate-300">
              <Package :size="88" />
            </div>
          </RouterLink>
        </Transition>

        <button
          class="absolute right-0 top-1/2 z-20 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-600 shadow-sm backdrop-blur transition hover:border-brand-orange hover:text-brand-orange"
          aria-label="Next slide"
          @click="nextSlide"
        >
          <ChevronRight :size="20" />
        </button>

        <div class="absolute bottom-2 left-1/2 z-20 flex -translate-x-1/2 items-center gap-2">
          <button
            v-for="(product, index) in heroProducts"
            :key="`dot-${product.id}`"
            :class="[
              'h-2 rounded-full transition-all duration-300',
              index === activeIndex
                ? 'w-8 bg-brand-orange'
                : 'w-2 bg-slate-300 hover:bg-brand-blue-500',
            ]"
            :aria-label="`Go to ${product.name}`"
            @click="selectSlide(index)"
          />
        </div>
      </div>

      <aside class="col-span-4">
        <div class="rounded-3xl border border-slate-100 bg-white p-6 shadow-xl">
          <span
            class="inline-flex rounded-full bg-brand-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-brand-blue-700"
          >
            {{ activeCategory }}
          </span>
          <h1
            class="mt-4 text-3xl font-black leading-[1.05] tracking-tight text-slate-900 xl:text-4xl"
          >
            {{ activeProduct?.name || "New collection arriving soon" }}
          </h1>
          <p class="mt-3 line-clamp-3 text-sm leading-relaxed text-slate-500">
            {{
              activeProduct?.description ||
              "Curated electronics and accessories, tested and ready for delivery."
            }}
          </p>

          <div v-if="specPills.length" class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="pill in specPills"
              :key="pill"
              class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600"
            >
              {{ pill }}
            </span>
          </div>

          <div class="mt-6 flex items-end justify-between gap-4">
            <div>
              <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
                Price
              </p>
              <p class="mt-1 text-2xl font-black text-slate-900">
                {{ formatKES(activeProduct?.price ?? 0) }}
              </p>
            </div>
            <span class="text-right text-[11px] text-slate-400">
              {{ activeProduct?.stock_quantity ?? 0 }} in stock
            </span>
          </div>

          <div class="mt-5 grid gap-2">
            <button
              v-magnetic
              type="button"
              :disabled="!activeProduct || addToCart.isPending.value"
              class="inline-flex items-center justify-center gap-2 rounded-full bg-[#FF4F00] px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 hover:shadow-[0_16px_32px_-14px_rgba(255,79,0,0.7)] disabled:cursor-not-allowed disabled:bg-slate-300"
              @click="addActiveToCart"
            >
              <ShoppingCart :size="17" /> Add to Cart
            </button>
            <RouterLink
              v-if="activeProduct"
              :to="`/products/${activeProduct.id}`"
              class="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-brand-orange hover:text-brand-orange"
            >
              View Details <ArrowRight :size="16" />
            </RouterLink>
          </div>
        </div>
      </aside>
    </section>

    <!-- Mobile hero -->
    <section
      class="min-w-0 lg:hidden"
      @touchstart.passive="pauseAutoAdvance"
      @touchend="resumeAutoAdvance"
      @touchcancel="resumeAutoAdvance"
      @mouseenter="pauseAutoAdvance"
      @mouseleave="resumeAutoAdvance"
    >
      <div class="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
        <button
          v-for="pill in categoryPills"
          :key="pill.name"
          class="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-600 transition hover:border-brand-orange hover:text-brand-orange"
          @click="shopCategory(pill.name)"
        >
          {{ pill.label }}
        </button>
      </div>

      <div class="mt-4 overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-lg">
        <div class="relative overflow-hidden bg-slate-50 p-4">
          <span
            class="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 select-none text-center text-[4.5rem] font-black uppercase leading-none tracking-tighter text-slate-900/5"
            aria-hidden="true"
          >
            {{ watermark }}
          </span>
          <Transition name="hero-slide" mode="out-in">
            <RouterLink
              v-if="activeProduct"
              :key="activeProduct.id"
              :to="`/products/${activeProduct.id}`"
              class="relative z-10 flex max-w-full justify-center"
            >
              <img
                v-if="productImage(activeProduct)"
                :src="productImage(activeProduct)"
                :alt="activeProduct.name"
                class="max-h-[240px] w-auto max-w-full object-contain drop-shadow-xl"
              />
              <Package v-else :size="72" class="text-slate-300" />
            </RouterLink>
          </Transition>

          <button
            class="absolute left-2 top-1/2 z-20 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-600 shadow-sm"
            aria-label="Previous slide"
            @click="previousSlide"
          >
            <ChevronLeft :size="18" />
          </button>
          <button
            class="absolute right-2 top-1/2 z-20 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-600 shadow-sm"
            aria-label="Next slide"
            @click="nextSlide"
          >
            <ChevronRight :size="18" />
          </button>

          <div class="relative z-20 mt-2 flex justify-center gap-1.5">
            <button
              v-for="(product, index) in heroProducts"
              :key="`mobile-dot-${product.id}`"
              :class="[
                'h-1.5 rounded-full transition-all',
                index === activeIndex ? 'w-6 bg-brand-orange' : 'w-1.5 bg-slate-300',
              ]"
              :aria-label="`Go to ${product.name}`"
              @click="selectSlide(index)"
            />
          </div>
        </div>

        <div class="min-w-0 p-5">
          <span
            class="inline-flex rounded-full bg-brand-blue-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-brand-blue-700"
          >
            {{ activeCategory }}
          </span>
          <h1
            class="mt-3 break-words font-black leading-[1.04] tracking-tight text-slate-900"
            :style="{ fontSize: 'clamp(1.6rem, 5vw, 3rem)' }"
          >
            {{ activeProduct?.name || "New collection arriving soon" }}
          </h1>
          <p class="mt-2 line-clamp-2 break-words text-sm text-slate-500">
            {{
              activeProduct?.description ||
              "Curated electronics and accessories, tested and ready for delivery."
            }}
          </p>
          <div v-if="specPills.length" class="mt-3 flex flex-wrap gap-1.5">
            <span
              v-for="pill in specPills"
              :key="`mobile-${pill}`"
              class="max-w-full truncate rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] text-slate-600"
            >
              {{ pill }}
            </span>
          </div>
          <div class="mt-4 flex items-center justify-between gap-3">
            <p class="shrink-0 text-xl font-black text-slate-900">
              {{ formatKES(activeProduct?.price ?? 0) }}
            </p>
            <RouterLink
              v-if="activeProduct"
              :to="`/products/${activeProduct.id}`"
              class="truncate text-right text-xs font-semibold text-brand-orange"
            >
              View details
            </RouterLink>
          </div>
          <button
            type="button"
            :disabled="!activeProduct || addToCart.isPending.value"
            class="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#FF4F00] px-4 py-3 text-sm font-semibold text-white disabled:bg-slate-300"
            @click="addActiveToCart"
          >
            <ShoppingCart :size="16" /> Add to Cart
          </button>
        </div>
      </div>
    </section>

    <!-- Slim trust ticker -->
    <div class="mt-4 flex justify-center overflow-x-auto py-2 text-xs text-slate-500 no-scrollbar">
      <div class="flex items-center gap-5 whitespace-nowrap">
        <template v-for="(item, index) in TICKER" :key="item">
          <span>{{ item }}</span>
          <span v-if="index < TICKER.length - 1" class="h-1 w-1 rounded-full bg-brand-orange" />
        </template>
      </div>
    </div>

    <section class="mt-6 md:mt-10">
      <div class="flex items-end justify-between">
        <h2 class="text-xl font-bold text-slate-900">Popular Electronics</h2>
        <RouterLink
          to="/shop"
          class="text-sm font-medium text-brand-orange hover:underline"
        >
          View all
        </RouterLink>
      </div>
      <div v-if="isLoading" class="flex justify-center py-16">
        <Spinner class="h-8 w-8" />
      </div>
      <div v-else class="mt-5 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
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
          class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-brand-blue-300 hover:text-brand-orange"
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
          class="text-sm font-medium text-brand-orange hover:underline"
        >
          View all
        </RouterLink>
      </div>
      <div class="mt-5 grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
        <ProductCard v-for="product in deals" :key="product.id" :product="product" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-slide-enter-active,
.hero-slide-leave-active {
  transition:
    opacity 320ms ease,
    transform 420ms cubic-bezier(0.22, 1, 0.36, 1);
}

.hero-slide-enter-from {
  opacity: 0;
  transform: translateX(28px) scale(0.94);
}

.hero-slide-leave-to {
  opacity: 0;
  transform: translateX(-28px) scale(1.02);
}
</style>
