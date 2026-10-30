<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { ImagePlus, Pencil, Plus, Search, Trash2 } from "@lucide/vue";
import { toast } from "vue-sonner";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Pagination from "../components/Pagination.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import CreateProductModal from "../components/CreateProductModal.vue";
import EditProductModal from "../components/EditProductModal.vue";
import ProductImagesModal from "../components/ProductImagesModal.vue";
import { api, errorMessage } from "../lib/api";
import {
  useAdminCategories,
  useAdminProducts,
} from "../hooks/queries";
import type { Product } from "../lib/types";
import { formatKES, productImage } from "../lib/utils";

const queryClient = useQueryClient();
const page = ref(1);
const searchInput = ref("");
const search = ref("");
const lowStock = ref(false);
const createOpen = ref(false);
const editProduct = ref<Product | null>(null);
const imagesProduct = ref<Product | null>(null);

const pageSize = 20;

const { data, isLoading } = useAdminProducts(() => ({
  page: page.value,
  pageSize,
  search: search.value,
  lowStock: lowStock.value,
}));
const categories = useAdminCategories();

const products = computed(() => data.value?.data ?? []);
const categoryList = computed(() => categories.data.value ?? []);

const del = useMutation({
  mutationFn: (id: string) => api.del(`/admin/products/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    toast.success("Product deleted");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function submitSearch() {
  page.value = 1;
  search.value = searchInput.value.trim();
}

function onLowStockChange(event: Event) {
  lowStock.value = (event.target as HTMLInputElement).checked;
  page.value = 1;
}

function confirmDelete(product: Product) {
  if (window.confirm(`Delete "${product.name}"? This cannot be undone.`)) {
    del.mutate(product.id);
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Products</h1>
        <p class="text-sm text-slate-500">
          Manage your catalogue, images and stock.
        </p>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        @click="createOpen = true"
      >
        <Plus :size="16" /> Create Product
      </button>
    </div>

    <Card class="overflow-hidden">
      <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
        <form
          class="flex flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="searchInput"
            placeholder="Search products…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>
        <label class="flex items-center gap-2 text-sm text-slate-600">
          <input
            :checked="lowStock"
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
            @change="onLowStockChange"
          />
          Low stock only
        </label>
      </div>

      <PageLoader v-if="isLoading" label="Loading products…" />
      <div v-else-if="products.length === 0" class="p-6">
        <EmptyState title="No products found" />
      </div>
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50">
              <tr>
                <Th>Product</Th>
                <Th>Price</Th>
                <Th>Stock</Th>
                <Th class="text-right">Actions</Th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="product in products"
                :key="product.id"
                class="border-t border-slate-100"
              >
                <Td>
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg bg-slate-50"
                    >
                      <img
                        v-if="productImage(product)"
                        :src="productImage(product)"
                        :alt="product.name"
                        class="h-full w-full object-contain"
                      />
                    </div>
                    <div>
                      <p class="font-medium text-slate-800">{{ product.name }}</p>
                      <p class="text-xs text-slate-400">
                        {{ product.brand || "—" }} &bull; {{ product.color || "—" }}
                      </p>
                    </div>
                  </div>
                </Td>
                <Td>{{ formatKES(product.price) }}</Td>
                <Td>
                  <span
                    :class="
                      (product.stock_quantity ?? 0) <= 5
                        ? 'rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-700'
                        : 'rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700'
                    "
                  >
                    {{ product.stock_quantity ?? 0 }}
                  </span>
                </Td>
                <Td class="text-right">
                  <div class="flex justify-end gap-1">
                    <button
                      class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-700"
                      aria-label="Edit"
                      @click="editProduct = product"
                    >
                      <Pencil :size="16" />
                    </button>
                    <button
                      class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-700"
                      aria-label="Images"
                      @click="imagesProduct = product"
                    >
                      <ImagePlus :size="16" />
                    </button>
                    <button
                      class="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                      aria-label="Delete"
                      @click="confirmDelete(product)"
                    >
                      <Trash2 :size="16" />
                    </button>
                  </div>
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

    <CreateProductModal
      v-if="createOpen"
      :open="createOpen"
      :categories="categoryList"
      @close="createOpen = false"
    />
    <EditProductModal
      v-if="editProduct"
      :product="editProduct"
      :categories="categoryList"
      @close="editProduct = null"
    />
    <ProductImagesModal
      v-if="imagesProduct"
      :product="imagesProduct"
      @close="imagesProduct = null"
    />
  </div>
</template>
