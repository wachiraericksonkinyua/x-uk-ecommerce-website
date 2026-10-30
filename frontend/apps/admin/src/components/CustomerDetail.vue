<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Mail, MapPin, Phone, ShieldCheck, User } from "@lucide/vue";
import { toast } from "vue-sonner";

import Badge from "./Badge.vue";
import PageLoader from "./PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useCustomerDetail } from "../hooks/queries";
import { cn, formatDate, formatKES, statusColor } from "../lib/utils";

const props = defineProps<{ userId: string }>();

const queryClient = useQueryClient();
const { data, isLoading } = useCustomerDetail(() => props.userId);

const profile = computed(() => data.value?.profile);
const orders = computed(() => data.value?.orders ?? []);
const currentRole = computed(() => profile.value?.role || "customer");

const updateRole = useMutation({
  mutationFn: (role: string) =>
    api.patch(`/admin/customers/${props.userId}/role`, { role }),
  onSuccess: () => {
    toast.success("Role updated");
    queryClient.invalidateQueries({ queryKey: ["admin-customer", props.userId] });
    queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function onRoleChange(event: Event) {
  updateRole.mutate((event.target as HTMLSelectElement).value);
}
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading customer…" />

  <div v-else class="space-y-5">
    <div class="rounded-xl bg-slate-50 p-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-700"
        >
          <User :size="22" />
        </span>
        <div>
          <p class="font-semibold text-slate-900">
            {{ profile?.full_name || "Unnamed customer" }}
          </p>
          <p class="text-xs text-slate-500">
            Joined {{ formatDate(profile?.created_at) }}
          </p>
        </div>
      </div>
      <div class="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
        <span class="flex items-center gap-2">
          <Phone :size="14" /> {{ profile?.phone_number || "—" }}
        </span>
        <span class="flex items-center gap-2">
          <MapPin :size="14" /> {{ profile?.address || "—" }}
        </span>
        <span class="flex items-center gap-2 sm:col-span-2">
          <Mail :size="14" />
          <span class="capitalize">{{ currentRole }}</span>
        </span>
      </div>
    </div>

    <div class="flex items-center justify-between rounded-xl border border-slate-100 p-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-700"
        >
          <ShieldCheck :size="18" />
        </span>
        <div>
          <p class="text-sm font-semibold text-slate-800">Account Role</p>
          <p class="text-xs text-slate-500">
            Promote to admin or revoke admin access.
          </p>
        </div>
      </div>
      <select
        :value="currentRole"
        :disabled="updateRole.isPending.value"
        class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm capitalize outline-none focus:border-blue-500 disabled:opacity-50"
        @change="onRoleChange"
      >
        <option value="customer">Customer</option>
        <option value="staff">Staff</option>
        <option value="admin">Admin</option>
      </select>
    </div>

    <div>
      <p class="mb-2 text-xs font-semibold uppercase text-slate-500">
        Order History ({{ orders.length }})
      </p>
      <p v-if="orders.length === 0" class="text-sm text-slate-500">No orders yet.</p>
      <div v-else class="space-y-2">
        <div
          v-for="order in orders"
          :key="order.id"
          class="flex items-center justify-between rounded-xl border border-slate-100 p-3"
        >
          <div>
            <p class="text-sm font-medium text-slate-800">
              {{ order.order_reference }}
            </p>
            <p class="text-xs text-slate-400">{{ formatDate(order.created_at) }}</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-semibold text-slate-900">
              {{ formatKES(order.total_amount) }}
            </p>
            <Badge :class="cn(statusColor(order.status))">{{ order.status }}</Badge>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
