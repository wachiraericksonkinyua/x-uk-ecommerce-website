<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { BadgeCheck, Ban, Eye } from "@lucide/vue";
import { toast } from "vue-sonner";

import Badge from "./Badge.vue";
import Td from "./Td.vue";
import { api, errorMessage } from "../lib/api";
import type { Order } from "../lib/types";
import {
  ORDER_STATUSES,
  cn,
  formatDate,
  formatKES,
  statusColor,
} from "../lib/utils";

const props = defineProps<{ order: Order }>();
const emit = defineEmits<{
  view: [order: Order];
  verify: [order: Order];
}>();

const queryClient = useQueryClient();
const status = ref(props.order.status);

const updateStatus = useMutation({
  mutationFn: (next: string) =>
    api.patch(`/admin/orders/${props.order.id}/status`, { status: next }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    toast.success("Status updated");
  },
  onError: (error) => {
    status.value = props.order.status;
    toast.error(errorMessage(error));
  },
});

const cancel = useMutation({
  mutationFn: () => api.post(`/admin/orders/${props.order.id}/cancel`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    toast.success("Order cancelled & stock restored");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function onStatusChange(event: Event) {
  const next = (event.target as HTMLSelectElement).value;
  status.value = next;
  updateStatus.mutate(next);
}

function confirmCancel() {
  if (window.confirm(`Cancel order ${props.order.order_reference}?`)) {
    cancel.mutate();
  }
}
</script>

<template>
  <tr class="border-t border-slate-100">
    <Td>
      <p class="font-medium text-slate-800">{{ order.order_reference }}</p>
      <p class="text-xs text-slate-400">{{ formatDate(order.created_at) }}</p>
    </Td>
    <Td>
      <p class="text-slate-700">{{ order.customer_email || "—" }}</p>
      <p class="text-xs text-slate-400">{{ order.customer_phone || "—" }}</p>
    </Td>
    <Td>{{ formatKES(order.total_amount) }}</Td>
    <Td>
      <select
        :value="status"
        class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-blue-500"
        @change="onStatusChange"
      >
        <option v-for="value in ORDER_STATUSES" :key="value" :value="value">
          {{ value }}
        </option>
      </select>
      <div class="mt-1">
        <Badge :class="cn(statusColor(order.status))">{{ order.status }}</Badge>
      </div>
    </Td>
    <Td class="text-right">
      <div class="flex justify-end gap-1">
        <button
          class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-700"
          aria-label="View"
          @click="emit('view', order)"
        >
          <Eye :size="16" />
        </button>
        <button
          class="rounded-lg p-2 text-slate-500 hover:bg-emerald-50 hover:text-emerald-600"
          aria-label="Verify payment"
          @click="emit('verify', order)"
        >
          <BadgeCheck :size="16" />
        </button>
        <button
          class="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
          aria-label="Cancel"
          @click="confirmCancel"
        >
          <Ban :size="16" />
        </button>
      </div>
    </Td>
  </tr>
</template>
