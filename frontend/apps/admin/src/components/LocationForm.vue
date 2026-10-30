<script setup lang="ts">
import { reactive } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import type { DeliveryLocation } from "../lib/types";

const props = defineProps<{ initial?: DeliveryLocation }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const form = reactive({
  name: props.initial?.name ?? "",
  cost: String(props.initial?.cost ?? 0),
  active: props.initial?.active ?? true,
});

const save = useMutation({
  mutationFn: () => {
    const payload = {
      name: form.name,
      cost: Number(form.cost),
      active: form.active,
    };
    return props.initial
      ? api.patch(`/admin/delivery-locations/${props.initial.id}`, payload)
      : api.post("/admin/delivery-locations", payload);
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-locations"] });
    queryClient.invalidateQueries({ queryKey: ["delivery-locations"] });
    toast.success(props.initial ? "Zone updated" : "Zone created");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <Modal
    :open="true"
    :title="initial ? 'Edit Delivery Zone' : 'New Delivery Zone'"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="save.mutate()">
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Location name *
        </label>
        <input
          v-model="form.name"
          required
          placeholder="e.g. Nairobi CBD"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Delivery cost (KES) *
        </label>
        <input
          v-model="form.cost"
          required
          type="number"
          min="0"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <label class="flex items-center gap-2 text-sm text-slate-600">
        <input
          v-model="form.active"
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300"
        />
        Active (available at checkout)
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
