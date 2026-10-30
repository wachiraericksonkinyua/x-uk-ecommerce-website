<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { Filter, SlidersHorizontal, X } from "@lucide/vue";
import { useRoute, useRouter } from "vue-router";

import ProductCard from "../components/ProductCard.vue";
import EmptyState from "../components/EmptyState.vue";
import Spinner from "../components/Spinner.vue";
import { useCategories, useProducts } from "../hooks/queries";
import { cn } from "../lib/utils";

const BRANDS = [
  "Apple",
  "Samsung",
  "Google",
  "OnePlus",
  "Xiaomi",
  "realme",
  "Huawei",
  "Oppo",
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
const { data: products, isLoading, isError } = useProducts(filters);

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
  <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Shop</h1>
        <p class="text-sm text-slate-500">
          {{ isLoading ? "Loading…" : `${productList.length} products found` }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <select
          :value="`${filters.sort_by}:${filters.order}`"
          class="hidden rounded-full border border-slate-200 bg-white px-4 py-2 text-sm outline-none focus:border-blue-500 sm:block"
          @change="onSortChange"
        >
          <option v-for="sort in SORTS" :key="sort.value" :value="sort.value">
            {{ sort.label }}
          </option>
        </select>
        <button
          class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 lg:hidden"
          @click="showFilters = !showFilters"
        >
          <X v-if="showFilters" :size="16" />
          <Filter v-else :size="16" /> Filters
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
              class="text-xs font-medium text-blue-700 hover:underline"
              @click="clearAll"
            >
              Clear all
            </button>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase text-slate-500">
              Search
            </label>
            <form class="mt-2" @submit.prevent="submitSearch">
              <input
                v-model="searchInput"
                placeholder="Search products"
                :class="
                  filters.search
                    ? 'w-full rounded-xl border border-blue-400 bg-blue-50 px-3 py-2 text-sm text-blue-900 outline-none focus:border-blue-500'
                    : 'w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-blue-500'
                "
              />
              <p v-if="filters.search" class="mt-2 text-xs text-blue-700">
                Searching for “{{ filters.search }}”
              </p>
            </form>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase text-slate-500">
              Category
            </label>
            <select
              :value="filters.category"
              class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-blue-500"
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
                    ? 'rounded-full bg-blue-700 px-3 py-1.5 text-xs font-medium text-white'
                    : 'rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition hover:border-blue-300 hover:text-blue-700'
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
                    ? 'rounded-full bg-blue-700 px-3 py-1.5 text-xs font-medium text-white'
                    : 'rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition hover:border-blue-300 hover:text-blue-700'
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
                    ? 'rounded-xl border border-blue-400 bg-blue-50 px-3 py-2 text-sm text-blue-900 outline-none focus:border-blue-500'
                    : 'rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-blue-500'
                "
              />
              <input
                v-model="maxInput"
                type="number"
                min="0"
                placeholder="Max"
                :class="
                  filters.max_price
                    ? 'rounded-xl border border-blue-400 bg-blue-50 px-3 py-2 text-sm text-blue-900 outline-none focus:border-blue-500'
                    : 'rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-blue-500'
                "
              />
            </div>
            <p
              v-if="filters.min_price || filters.max_price"
              class="mt-2 text-xs text-blue-700"
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
