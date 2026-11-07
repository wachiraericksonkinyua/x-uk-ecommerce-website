<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Check } from "@lucide/vue";
import { toast } from "vue-sonner";

import { api, errorMessage } from "../lib/api";

const props = defineProps<{ id: string; name: string; stock: number }>();

const queryClient = useQueryClient();
const value = ref(String(props.stock));

const update = useMutation({
  mutationFn: () =>
    api.patch(`/admin/inventory/${props.id}`, {
      stock_quantity: Math.max(0, Number(value.value) || 0),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    queryClient.invalidateQueries({ queryKey: ["admin-low-stock"] });
    queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["admin-sales-analytics"] });
    toast.success(`Stock updated for ${props.name}`);
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <div class="flex items-center gap-2">
    <input
      v-model="value"
      type="number"
      min="0"
      class="w-20 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm outline-none focus:border-brand-orange"
    />
    <button
      :disabled="update.isPending.value"
      class="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-ink-700 disabled:opacity-40"
      @click="update.mutate()"
    >
      <Check :size="13" /> Save
    </button>
  </div>
</template>
