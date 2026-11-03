<script setup lang="ts">
import { reactive } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import type { Product } from "../lib/types";

const props = defineProps<{
  product: Product;
  categories: { id: string; name: string }[];
}>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const form = reactive({
  name: props.product.name,
  price: String(props.product.price),
  brand: props.product.brand ?? "",
  description: props.product.description ?? "",
  color: props.product.color ?? "",
  category_id: props.product.category_id ?? "",
  stock_quantity: String(props.product.stock_quantity ?? 0),
  compatibility: props.product.compatibility ?? "",
  specs: JSON.stringify(props.product.specs ?? {}, null, 2),
});

const save = useMutation({
  mutationFn: () => {
    let specs: Record<string, unknown> = {};
    if (form.specs.trim()) {
      try {
        const parsed = JSON.parse(form.specs);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("Specs must be a JSON object");
        }
        specs = parsed as Record<string, unknown>;
      } catch (error) {
        throw new Error(
          error instanceof SyntaxError
            ? "Specs must be valid JSON"
            : error instanceof Error
              ? error.message
              : "Specs must be a JSON object"
        );
      }
    }

    return api.patch(`/admin/products/${props.product.id}`, {
      name: form.name,
      price: Number(form.price),
      brand: form.brand,
      description: form.description,
      color: form.color,
      category_id: form.category_id || null,
      stock_quantity: Number(form.stock_quantity),
      compatibility: form.compatibility || null,
      specs,
    });
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    queryClient.invalidateQueries({ queryKey: ["admin-sales-analytics"] });
    toast.success("Product updated");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <Modal :open="true" title="Edit Product" size="lg" @close="emit('close')">
    <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="save.mutate()">
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">Name</label>
        <input
          v-model="form.name"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Price (KES)
        </label>
        <input
          v-model="form.price"
          type="number"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">Stock</label>
        <input
          v-model="form.stock_quantity"
          type="number"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">Brand</label>
        <input
          v-model="form.brand"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">Color</label>
        <input
          v-model="form.color"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Category
        </label>
        <select
          v-model="form.category_id"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        >
          <option value="">Uncategorized</option>
          <option
            v-for="category in categories"
            :key="category.id"
            :value="category.id"
          >
            {{ category.name }}
          </option>
        </select>
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Compatibility
        </label>
        <input
          v-model="form.compatibility"
          placeholder="e.g. iPhone 15 / USB-C devices"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Technical specs (JSON object)
        </label>
        <textarea
          v-model="form.specs"
          rows="4"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-xs outline-none focus:border-brand-orange"
        />
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Description
        </label>
        <textarea
          v-model="form.description"
          rows="3"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div class="flex justify-end gap-2 sm:col-span-2">
        <button
          type="button"
          class="rounded-full border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
          @click="emit('close')"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="save.isPending.value"
          class="rounded-full bg-brand-orange px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:bg-slate-300"
        >
          {{ save.isPending.value ? "Saving…" : "Save changes" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
