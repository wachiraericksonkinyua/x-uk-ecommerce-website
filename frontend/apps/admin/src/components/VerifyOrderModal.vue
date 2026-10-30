<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { BadgeCheck } from "@lucide/vue";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import type { Order } from "../lib/types";

const props = defineProps<{ order: Order }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const receipt = ref("");

const verify = useMutation({
  mutationFn: () =>
    api.patch(`/orders/verify-payment/${props.order.id}`, {
      receipt_number: receipt.value.trim(),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    toast.success("Payment verified, order marked Paid");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <Modal
    :open="true"
    :title="`Verify M-Pesa Payment — ${order.order_reference}`"
    @close="emit('close')"
  >
    <form
      class="space-y-4"
      @submit.prevent="verify.mutate()"
    >
      <p class="text-sm text-slate-500">
        Enter the M-Pesa receipt number to confirm this payment. The order will
        be marked <span class="font-semibold">Paid</span> and a receipt emailed
        to {{ order.customer_email || "the customer" }}.
      </p>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Receipt number
        </label>
        <input
          v-model="receipt"
          required
          placeholder="e.g. QK12ABC34D"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-sm outline-none focus:border-blue-500"
        />
      </div>
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
          :disabled="verify.isPending.value"
          class="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
        >
          <BadgeCheck :size="16" />
          {{ verify.isPending.value ? "Verifying…" : "Verify payment" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
