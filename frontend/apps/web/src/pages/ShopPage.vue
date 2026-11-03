<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { Filter, SlidersHorizontal, X } from "@lucide/vue";
import { useRoute, useRouter } from "vue-router";

import ProductCard from "../components/ProductCard.vue";
import EmptyState from "../components/EmptyState.vue";
import PullToRefreshIndicator from "../components/PullToRefreshIndicator.vue";
import Spinner from "../components/Spinner.vue";
import { usePullToRefresh } from "../composables/usePullToRefresh";
import { useCategories, useProducts } from "../hooks/queries";
import { cn } from "../lib/utils";

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
  "Bose",
];

const COLORS = [
  "Black",
  "White",
  "Blue",
  "Green",
  "Silver",
  "Gold",
  "Purple",
  "Red",
];

const SORTS = [
  { value: "created_at:desc", label: "Newest first" },
  { value: "created_at:asc", label: "Oldest first" },
  { value: "price:asc", label: "Price: low to high" },
  { value: "price:desc", label: "Price: high to low" },
];

const route = useRoute();
const router = useRouter();
const showFilters = ref(false);

function queryValue(key: string): string {
  const value = route.query[key];
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value[0] ?? "";
  return "";
}

const filters = computed(() => ({
  search: queryValue("search"),
  category: queryValue("category"),
  brand: queryValue("brand"),
  color: queryValue("color"),
  min_price: queryValue("min_price"),
  max_price: queryValue("max_price"),
  sort_by: queryValue("sort_by") || "created_at",
  order: queryValue("order") || "desc",
}));

const searchInput = ref(filters.value.search);
const minInput = ref(filters.value.min_price);
const maxInput = ref(filters.value.max_price);

watch(
  () => filters.value.search,
  (value) => (searchInput.value = value)
);
watch(
  () => filters.value.min_price,
  (value) => (minInput.value = value)
);
watch(
  () => filters.value.max_price,
  (value) => (maxInput.value = value)
);

const { data: categories } = useCategories();
const { data: products, isLoading, isError, refetch } = useProducts(filters);
const {
  pullDistance,
  refreshing: pullRefreshing,
  ready: pullReady,
} = usePullToRefresh(() => refetch());

const productList = computed(() => products.value ?? []);
const categoryList = computed(() => categories.value ?? []);

function update(key: string, value: string) {
  const next: Record<string, string> = {};
  for (const [name, raw] of Object.entries(route.query)) {
    const text = Array.isArray(raw) ? raw[0] : raw;
    if (text) next[name] = text;
  }
  if (value) next[key] = value;
  else delete next[key];
  router.replace({ query: next });
}

let minTimer: ReturnType<typeof setTimeout> | undefined;
let maxTimer: ReturnType<typeof setTimeout> | undefined;

watch(minInput, (value) => {
  clearTimeout(minTimer);
  minTimer = setTimeout(() => {
    if (value !== filters.value.min_price) update("min_price", value);
  }, 400);
});

watch(maxInput, (value) => {
  clearTimeout(maxTimer);
  maxTimer = setTimeout(() => {
    if (value !== filters.value.max_price) update("max_price", value);
  }, 400);
});

onBeforeUnmount(() => {
  clearTimeout(minTimer);
  clearTimeout(maxTimer);
});

function setSort(value: string) {
  const [sortBy, order] = value.split(":");
  const next: Record<string, string> = {};
  for (const [name, raw] of Object.entries(route.query)) {
    const text = Array.isArray(raw) ? raw[0] : raw;
    if (text) next[name] = text;
  }
  next.sort_by = sortBy;
  next.order = order;
  router.replace({ query: next });
}

function clearAll() {
  searchInput.value = "";
  minInput.value = "";
  maxInput.value = "";
  router.replace({ query: {} });
}

const activeCount = computed(
  () =>
    ["category", "brand", "color", "min_price", "max_price", "search"].filter(
      (key) => typeof route.query[key] === "string" && route.query[key]
    ).length
);

function submitSearch() {
  update("search", searchInput.value.trim());
}

function onCategoryChange(event: Event) {
  update("category", (event.target as HTMLSelectElement).value);
}

function onSortChange(event: Event) {
  setSort((event.target as HTMLSelectElement).value);
}
</script>

<template>
  <PullToRefreshIndicator
    :distance="pullDistance"
    :refreshing="pullRefreshing"
    :ready="pullReady"
  />
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
    <section class="relative overflow-hidden rounded-[2rem] bg-slate-950 px-6 py-12 text-white sm:px-10 sm:py-16">
      <div class="pointer-events-none absolute -right-16 -top-24 h-72 w-72 rounded-full bg-brand-orange/30 blur-3xl" />
      <div class="pointer-events-none absolute -bottom-28 left-1/3 h-56 w-56 rounded-full bg-brand-blue/20 blur-3xl" />
      <div class="relative">
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-brand-blue-300">
          The editorial collection
        </p>
        <h1 class="mt-1 text-[clamp(3.5rem,14vw,9rem)] font-black leading-[0.82] tracking-tighter">
          Shop
        </h1>
        <div class="mt-4 flex flex-wrap items-end justify-between gap-3">
          <p class="max-w-lg text-sm text-slate-400">
            Smartphones, audio, power and wearables — curated for how you
            actually live.
          </p>
          <p class="text-xs font-medium text-slate-500">
            {{ isLoading ? "Loading collection…" : `${productList.length} pieces available` }}
          </p>
        </div>
      </div>
    </section>

    <div class="relative z-10 -mt-6 rounded-2xl border border-slate-100 bg-white p-3 shadow-lg sm:p-4">
      <div class="flex flex-col gap-2 lg:flex-row lg:items-center">
        <form
          class="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5"
          @submit.prevent="submitSearch"
        >
          <Filter :size="16" class="shrink-0 text-slate-400" />
          <input
            v-model="searchInput"
            placeholder="Search the collection"
            class="min-w-0 flex-1 bg-transparent text-sm outline-none"
          />
          <button
            type="submit"
            class="rounded-lg bg-brand-orange px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-orange-600"
          >
            Search
          </button>
        </form>

        <select
          :value="filters.category"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-orange lg:w-52"
          @change="onCategoryChange"
        >
          <option value="">All categories</option>
          <option
            v-for="category in categoryList"
            :key="category.id"
            :value="category.name"
          >
            {{ category.name }}
          </option>
        </select>

        <select
          :value="`${filters.sort_by}:${filters.order}`"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-orange lg:w-48"
          @change="onSortChange"
        >
          <option v-for="sort in SORTS" :key="sort.value" :value="sort.value">
            {{ sort.label }}
          </option>
        </select>

        <button
          class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-600 transition hover:border-brand-orange hover:text-brand-orange lg:hidden"
          @click="showFilters = !showFilters"
        >
          <X v-if="showFilters" :size="16" />
          <SlidersHorizontal v-else :size="16" /> Filters
        </button>
      </div>
      <div v-if="activeCount > 0" class="mt-2 flex items-center justify-between px-1 text-xs">
        <span class="text-slate-500">{{ activeCount }} active filter{{ activeCount === 1 ? "" : "s" }}</span>
        <button class="font-semibold text-brand-orange hover:underline" @click="clearAll">
          Clear all
        </button>
      </div>
    </div>

    <div class="mt-6 grid gap-6 lg:grid-cols-[16rem_1fr]">
      <aside
        :class="
          showFilters
            ? 'rounded-2xl border border-slate-100 bg-white p-5 shadow-sm lg:sticky lg:top-20 lg:block lg:h-fit'
            : 'hidden rounded-2xl border border-slate-100 bg-white p-5 shadow-sm lg:sticky lg:top-20 lg:block lg:h-fit'
        "
      >
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <h3 class="flex items-center gap-2 text-sm font-bold text-slate-900">
              <SlidersHorizontal :size="16" /> Filters
            </h3>
            <button
              v-if="activeCount > 0"
              class="text-xs font-medium text-brand-orange hover:underline"
              @click="clearAll"
            >
              Clear all
            </button>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase text-slate-500">
              Brand
            </label>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="brand in BRANDS"
                :key="brand"
                :class="
                  filters.brand === brand
                    ? 'rounded-full bg-brand-orange px-3 py-1.5 text-xs font-medium text-white'
                    : 'rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition hover:border-brand-blue-300 hover:text-brand-orange'
                "
                @click="update('brand', filters.brand === brand ? '' : brand)"
              >
                {{ brand }}
              </button>
            </div>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase text-slate-500">
              Color
            </label>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="color in COLORS"
                :key="color"
                :class="
                  filters.color === color
                    ? 'rounded-full bg-brand-orange px-3 py-1.5 text-xs font-medium text-white'
                    : 'rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition hover:border-brand-blue-300 hover:text-brand-orange'
                "
                @click="update('color', filters.color === color ? '' : color)"
              >
                {{ color }}
              </button>
            </div>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase text-slate-500">
              Price range (KES)
            </label>
            <div class="mt-2 grid grid-cols-2 gap-2">
              <input
                v-model="minInput"
                type="number"
                min="0"
                placeholder="Min"
                :class="
                  filters.min_price
                    ? 'rounded-xl border border-brand-orange bg-brand-blue-50 px-3 py-2 text-sm text-brand-orange-dark outline-none focus:border-brand-orange'
                    : 'rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-brand-orange'
                "
              />
              <input
                v-model="maxInput"
                type="number"
                min="0"
                placeholder="Max"
                :class="
                  filters.max_price
                    ? 'rounded-xl border border-brand-orange bg-brand-blue-50 px-3 py-2 text-sm text-brand-orange-dark outline-none focus:border-brand-orange'
                    : 'rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-brand-orange'
                "
              />
            </div>
            <p
              v-if="filters.min_price || filters.max_price"
              class="mt-2 text-xs text-brand-orange"
            >
              Active: {{ filters.min_price ? `from KES ${filters.min_price}` : "any min" }}
              {{ filters.max_price ? ` to KES ${filters.max_price}` : " with no max" }}
            </p>
          </div>
        </div>
      </aside>

      <div>
        <div v-if="isLoading" class="flex justify-center py-24">
          <Spinner class="h-8 w-8" />
        </div>

        <EmptyState
          v-else-if="isError"
          title="Could not load products"
          description="Make sure the backend is running and CORS_ORIGINS includes this origin."
        />

        <EmptyState
          v-else-if="productList.length === 0"
          title="No products match your filters"
          description="Try adjusting or clearing your filters."
        />

        <div v-else class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          <ProductCard
            v-for="product in productList"
            :key="product.id"
            :product="product"
          />
        </div>
      </div>
    </div>
  </div>
</template>
