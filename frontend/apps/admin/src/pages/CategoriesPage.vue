<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Pencil, Plus, Tags, Trash2 } from "@lucide/vue";
import { toast } from "vue-sonner";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import CategoryForm from "../components/CategoryForm.vue";
import { api, errorMessage } from "../lib/api";
import { useAdminCategories } from "../hooks/queries";
import type { Category } from "../lib/types";

const queryClient = useQueryClient();
const { data: categories, isLoading } = useAdminCategories();
const editing = ref<Category | "new" | null>(null);

const categoryList = computed(() => categories.value ?? []);
const editingInitial = computed(() =>
  editing.value && editing.value !== "new" ? editing.value : undefined
);

const del = useMutation({
  mutationFn: (id: string) => api.del(`/admin/categories/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
    toast.success("Category deleted");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function confirmDelete(category: Category) {
  if (window.confirm(`Delete "${category.name}"?`)) {
    del.mutate(category.id);
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Categories</h1>
        <p class="text-sm text-slate-500">
          Organise products into browsable categories.
        </p>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        @click="editing = 'new'"
      >
        <Plus :size="16" /> New Category
      </button>
    </div>

    <Card class="overflow-hidden">
      <PageLoader v-if="isLoading" label="Loading categories…" />
      <div v-else-if="categoryList.length === 0" class="p-6">
        <EmptyState title="No categories yet" />
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-slate-50">
            <tr>
              <Th>Name</Th>
              <Th>Slug</Th>
              <Th>Status</Th>
              <Th class="text-right">Actions</Th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="category in categoryList"
              :key="category.id"
              class="border-t border-slate-100"
            >
              <Td>
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700"
                  >
                    <Tags :size="16" />
                  </span>
                  <div>
                    <p class="font-medium text-slate-800">{{ category.name }}</p>
                    <p v-if="category.description" class="text-xs text-slate-400">
                      {{ category.description }}
                    </p>
                  </div>
                </div>
              </Td>
              <Td class="text-slate-500">{{ category.slug }}</Td>
              <Td>
                <span
                  :class="
                    category.active
                      ? 'rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700'
                      : 'rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600'
                  "
                >
                  {{ category.active ? "Active" : "Hidden" }}
                </span>
              </Td>
              <Td class="text-right">
                <div class="flex justify-end gap-1">
                  <button
                    class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-700"
                    aria-label="Edit"
                    @click="editing = category"
                  >
                    <Pencil :size="16" />
                  </button>
                  <button
                    class="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                    aria-label="Delete"
                    @click="confirmDelete(category)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </Td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <CategoryForm
      v-if="editing"
      :initial="editingInitial"
      @close="editing = null"
    />
  </div>
</template>
