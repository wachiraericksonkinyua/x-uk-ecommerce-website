<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Check } from "@lucide/vue";
import { toast } from "vue-sonner";

import Td from "./Td.vue";
import { api, errorMessage } from "../lib/api";

const props = defineProps<{
  id: string;
  name: string;
  brand?: string | null;
  stock: number;
}>();

const queryClient = useQueryClient();
const value = ref(String(props.stock));

const update = useMutation({
  mutationFn: () =>
    api.patch(`/admin/inventory/${props.id}`, {
      stock_quantity: Number(value.value),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-low-stock"] });
    queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    toast.success(`Updated stock for ${props.name}`);
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <tr class="border-t border-slate-100">
    <Td>
      <p class="font-medium text-slate-800">{{ name }}</p>
      <p class="text-xs text-slate-400">{{ brand || "—" }}</p>
    </Td>
    <Td>
      <span
        class="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-700"
      >
        {{ stock }} left
      </span>
    </Td>
    <Td>
      <div class="flex items-center gap-2">
        <input
          v-model="value"
          type="number"
          min="0"
          class="w-24 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500"
        />
        <button
          :disabled="update.isPending.value"
          class="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-800 disabled:bg-slate-300"
          @click="update.mutate()"
        >
          <Check :size="13" /> Save
        </button>
      </div>
    </Td>
  </tr>
</template>
