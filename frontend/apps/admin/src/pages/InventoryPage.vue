<script setup lang="ts">
import { computed, ref } from "vue";
import { Boxes, PackageX, Plus, Search } from "@lucide/vue";
import { RouterLink } from "vue-router";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Pagination from "../components/Pagination.vue";
import StockEditor from "../components/StockEditor.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import { useAdminProducts } from "../hooks/queries";
import { formatKES, productImage } from "../lib/utils";

const page = ref(1);
const searchInput = ref("");
const search = ref("");
const pageSize = 20;

const { data, isLoading } = useAdminProducts(() => ({
  page: page.value,
  pageSize,
  search: search.value,
}));

const products = computed(() => data.value?.data ?? []);
const lowCount = computed(
  () => products.value.filter((product) => (product.stock_quantity ?? 0) <= 5).length
);
const outCount = computed(
  () => products.value.filter((product) => (product.stock_quantity ?? 0) === 0).length
);

function submitSearch() {
  page.value = 1;
  search.value = searchInput.value.trim();
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-orange">
          Commerce
        </p>
        <h1 class="mt-1 font-display text-2xl font-semibold tracking-tight text-slate-900">
          Inventory
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          Track stock levels and restock products without leaving the dashboard.
        </p>
      </div>
      <RouterLink to="/products" class="btn-primary">
        <Plus :size="16" /> Add product
      </RouterLink>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      <Card class="p-5">
        <div class="flex items-center justify-between">
          <p class="kpi-label">Products</p>
          <Boxes :size="18" class="text-slate-400" />
        </div>
        <p class="kpi-value">{{ data?.total ?? 0 }}</p>
      </Card>
      <Card class="p-5">
        <div class="flex items-center justify-between">
          <p class="kpi-label">Low stock (≤ 5)</p>
          <PackageX :size="18" class="text-amber-500" />
        </div>
        <p class="kpi-value">{{ lowCount }}</p>
      </Card>
      <Card class="p-5">
        <div class="flex items-center justify-between">
          <p class="kpi-label">Out of stock</p>
          <PackageX :size="18" class="text-rose-500" />
        </div>
        <p class="kpi-value">{{ outCount }}</p>
      </Card>
    </div>

    <Card class="mt-6 overflow-hidden">
      <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
        <form
          class="flex flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="searchInput"
            placeholder="Search the catalogue…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>
      </div>

      <PageLoader v-if="isLoading" label="Loading inventory…" />
      <div v-else-if="products.length === 0" class="p-6">
        <EmptyState title="No products found" />
      </div>
      <template v-else>
        <div class="table-shell">
          <table class="w-full">
            <thead class="bg-slate-50/80">
              <tr>
                <Th>Product</Th>
                <Th>Price</Th>
                <Th>Status</Th>
                <Th>Stock</Th>
                <Th>Update</Th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="product in products" :key="product.id" class="border-t border-slate-100">
                <Td>
                  <div class="flex items-center gap-3">
                    <div class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg bg-slate-50">
                      <img
                        v-if="productImage(product)"
                        :src="productImage(product)"
                        :alt="product.name"
                        class="h-full w-full object-contain"
                      />
                    </div>
                    <div>
                      <p class="font-medium text-slate-800">{{ product.name }}</p>
                      <p class="text-xs text-slate-400">{{ product.brand || "—" }}</p>
                    </div>
                  </div>
                </Td>
                <Td>{{ formatKES(product.price) }}</Td>
                <Td>
                  <span
                    :class="
                      (product.stock_quantity ?? 0) === 0
                        ? 'rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700'
                        : (product.stock_quantity ?? 0) <= 5
                          ? 'rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700'
                          : 'rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700'
                    "
                  >
                    {{
                      (product.stock_quantity ?? 0) === 0
                        ? "Out of stock"
                        : (product.stock_quantity ?? 0) <= 5
                          ? "Low stock"
                          : "In stock"
                    }}
                  </span>
                </Td>
                <Td class="font-semibold text-slate-900">{{ product.stock_quantity ?? 0 }}</Td>
                <Td>
                  <StockEditor
                    :id="product.id"
                    :name="product.name"
                    :stock="product.stock_quantity ?? 0"
                  />
                </Td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :page="page"
          :page-size="pageSize"
          :total="data?.total ?? 0"
          @page="page = $event"
        />
      </template>
    </Card>
  </div>
</template>
