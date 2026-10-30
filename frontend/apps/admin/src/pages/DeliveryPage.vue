<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Pencil, Plus, Trash2, Truck } from "@lucide/vue";
import { toast } from "vue-sonner";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import LocationForm from "../components/LocationForm.vue";
import { api, errorMessage } from "../lib/api";
import { useAdminLocations } from "../hooks/queries";
import type { DeliveryLocation } from "../lib/types";
import { formatKES } from "../lib/utils";

const queryClient = useQueryClient();
const { data: locations, isLoading } = useAdminLocations();
const editing = ref<DeliveryLocation | "new" | null>(null);

const locationList = computed(() => locations.value ?? []);
const editingInitial = computed(() =>
  editing.value && editing.value !== "new" ? editing.value : undefined
);

const del = useMutation({
  mutationFn: (id: string) => api.del(`/admin/delivery-locations/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-locations"] });
    toast.success("Delivery zone deleted");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function confirmDelete(location: DeliveryLocation) {
  if (window.confirm(`Delete "${location.name}"?`)) {
    del.mutate(location.id);
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Delivery Zones</h1>
        <p class="text-sm text-slate-500">
          Set the delivery fee customers pay per location.
        </p>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        @click="editing = 'new'"
      >
        <Plus :size="16" /> New Zone
      </button>
    </div>

    <Card class="overflow-hidden">
      <PageLoader v-if="isLoading" label="Loading zones…" />
      <div v-else-if="locationList.length === 0" class="p-6">
        <EmptyState title="No delivery zones yet" />
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-slate-50">
            <tr>
              <Th>Location</Th>
              <Th>Cost</Th>
              <Th>Status</Th>
              <Th class="text-right">Actions</Th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="location in locationList"
              :key="location.id"
              class="border-t border-slate-100"
            >
              <Td>
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700"
                  >
                    <Truck :size="16" />
                  </span>
                  <span class="font-medium text-slate-800">{{ location.name }}</span>
                </div>
              </Td>
              <Td>{{ formatKES(location.cost) }}</Td>
              <Td>
                <span
                  :class="
                    location.active
                      ? 'rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700'
                      : 'rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600'
                  "
                >
                  {{ location.active ? "Active" : "Disabled" }}
                </span>
              </Td>
              <Td class="text-right">
                <div class="flex justify-end gap-1">
                  <button
                    class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-blue-700"
                    aria-label="Edit"
                    @click="editing = location"
                  >
                    <Pencil :size="16" />
                  </button>
                  <button
                    class="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                    aria-label="Delete"
                    @click="confirmDelete(location)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </Td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <LocationForm
      v-if="editing"
      :initial="editingInitial"
      @close="editing = null"
    />
  </div>
</template>
