<script setup lang="ts">
import { reactive } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import type { Category } from "../lib/types";

const props = defineProps<{ initial?: Category }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const form = reactive({
  name: props.initial?.name ?? "",
  slug: props.initial?.slug ?? "",
  description: props.initial?.description ?? "",
  image_url: props.initial?.image_url ?? "",
  active: props.initial?.active ?? true,
});

const save = useMutation({
  mutationFn: () =>
    props.initial
      ? api.patch(`/admin/categories/${props.initial.id}`, { ...form })
      : api.post("/admin/categories", { ...form }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
    toast.success(props.initial ? "Category updated" : "Category created");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <Modal
    :open="true"
    :title="initial ? 'Edit Category' : 'Create Category'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="save.mutate()">
      <div>
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
          Slug (optional)
        </label>
        <input
          v-model="form.slug"
          placeholder="auto-generated from name"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Description
        </label>
        <textarea
          v-model="form.description"
          rows="2"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Image URL
        </label>
        <input
          v-model="form.image_url"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input
          v-model="form.active"
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300"
        />
        Active (visible on storefront)
      </label>
      <div class="flex justify-end gap-2">
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
          class="rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-slate-300"
        >
          {{ save.isPending.value ? "Saving…" : "Save" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
