<script setup lang="ts">
import { reactive, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";

defineProps<{ open: boolean; categories: { id: string; name: string }[] }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const fileRef = ref<HTMLInputElement | null>(null);
const form = reactive({
  name: "",
  price: "",
  brand: "",
  description: "",
  color: "",
  category_id: "",
  stock_quantity: "",
});

const create = useMutation({
  mutationFn: () => {
    const body = new FormData();
    body.append("name", form.name);
    body.append("price", form.price);
    body.append("brand", form.brand);
    body.append("description", form.description);
    body.append("color", form.color);
    const files = fileRef.value?.files;
    if (files) {
      Array.from(files).forEach((file) => body.append("images", file));
    }
    return api.post("/products/", body);
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    toast.success("Product created");
    form.name = "";
    form.price = "";
    form.brand = "";
    form.description = "";
    form.color = "";
    form.category_id = "";
    form.stock_quantity = "";
    if (fileRef.value) fileRef.value.value = "";
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function submit() {
  if (!fileRef.value?.files?.length) {
    toast.error("At least one product image is required");
    return;
  }
  create.mutate();
}
</script>

<template>
  <Modal :open="open" title="Create Product" size="lg" @close="emit('close')">
    <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Name *
        </label>
        <input
          v-model="form.name"
          required
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Price (KES) *
        </label>
        <input
          v-model="form.price"
          required
          type="number"
          min="0"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Brand *
        </label>
        <input
          v-model="form.brand"
          required
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Color *
        </label>
        <input
          v-model="form.color"
          required
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Description *
        </label>
        <textarea
          v-model="form.description"
          required
          rows="3"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Images * (select multiple)
        </label>
        <input
          ref="fileRef"
          type="file"
          accept="image/*"
          multiple
          class="mt-2 w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm"
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
          :disabled="create.isPending.value"
          class="rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-slate-300"
        >
          {{ create.isPending.value ? "Creating…" : "Create product" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
