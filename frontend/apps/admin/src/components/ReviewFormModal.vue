<script setup lang="ts">
import { reactive } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import type { Review } from "../lib/types";

const props = defineProps<{ initial?: Review }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const form = reactive({
  product_id: props.initial?.product_id ?? "",
  user_id: props.initial?.user_id ?? "",
  rating: String(props.initial?.rating ?? 5),
  comment: props.initial?.comment ?? "",
  is_approved: props.initial?.is_approved ?? true,
});

const save = useMutation({
  mutationFn: () => {
    const payload = {
      rating: Number(form.rating),
      comment: form.comment,
      is_approved: form.is_approved,
    };
    return props.initial
      ? api.patch(`/admin/reviews/${props.initial.id}`, payload)
      : api.post("/admin/reviews", {
          ...payload,
          product_id: form.product_id,
          user_id: form.user_id,
        });
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
    toast.success(props.initial ? "Review updated" : "Review created");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <Modal
    :open="true"
    :title="initial ? 'Edit Review' : 'Create Review'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="save.mutate()">
      <div v-if="!initial" class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Product ID *
          </label>
          <input
            v-model="form.product_id"
            required
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-xs outline-none focus:border-brand-orange"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            User ID *
          </label>
          <input
            v-model="form.user_id"
            required
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-xs outline-none focus:border-brand-orange"
          />
        </div>
      </div>

      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Rating *
        </label>
        <select
          v-model="form.rating"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        >
          <option v-for="value in [5, 4, 3, 2, 1]" :key="value" :value="String(value)">
            {{ value }} star{{ value === 1 ? "" : "s" }}
          </option>
        </select>
      </div>

      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Comment *
        </label>
        <textarea
          v-model="form.comment"
          required
          rows="4"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input
          v-model="form.is_approved"
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300"
        />
        Approved (visible on the storefront)
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
          class="btn-primary"
        >
          {{ save.isPending.value ? "Saving…" : "Save review" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
