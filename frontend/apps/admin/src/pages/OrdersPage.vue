<script setup lang="ts">
import { computed, ref } from "vue";
import { Search } from "@lucide/vue";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import Modal from "../components/Modal.vue";
import PageLoader from "../components/PageLoader.vue";
import Pagination from "../components/Pagination.vue";
import Th from "../components/Th.vue";
import OrderDetail from "../components/OrderDetail.vue";
import OrderRow from "../components/OrderRow.vue";
import VerifyOrderModal from "../components/VerifyOrderModal.vue";
import { useAdminOrders } from "../hooks/queries";
import type { Order } from "../lib/types";
import { ORDER_STATUSES } from "../lib/utils";

const page = ref(1);
const status = ref("");
const searchInput = ref("");
const search = ref("");
const viewOrder = ref<Order | null>(null);
const verifyOrder = ref<Order | null>(null);

const pageSize = 20;

const { data, isLoading } = useAdminOrders(() => ({
  page: page.value,
  pageSize,
  status: status.value,
  search: search.value,
}));

const orders = computed(() => data.value?.data ?? []);

function submitSearch() {
  page.value = 1;
  search.value = searchInput.value.trim();
}

function onStatusFilter(event: Event) {
  status.value = (event.target as HTMLSelectElement).value;
  page.value = 1;
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Orders</h1>
      <p class="text-sm text-slate-500">
        Track, update and verify customer orders.
      </p>
    </div>

    <Card class="overflow-hidden">
      <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
        <form
          class="flex flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="searchInput"
            placeholder="Search reference, phone or email…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>
        <select
          :value="status"
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm outline-none focus:border-blue-500"
          @change="onStatusFilter"
        >
          <option value="">All statuses</option>
          <option v-for="value in ORDER_STATUSES" :key="value" :value="value">
            {{ value }}
          </option>
        </select>
      </div>

      <PageLoader v-if="isLoading" label="Loading orders…" />
      <div v-else-if="orders.length === 0" class="p-6">
        <EmptyState
          title="No orders found"
          description="Orders placed by customers will appear here."
        />
      </div>
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50">
              <tr>
                <Th>Reference</Th>
                <Th>Customer</Th>
                <Th>Total</Th>
                <Th>Status</Th>
                <Th class="text-right">Actions</Th>
              </tr>
            </thead>
            <tbody>
              <OrderRow
                v-for="order in orders"
                :key="order.id"
                :order="order"
                @view="viewOrder = $event"
                @verify="verifyOrder = $event"
              />
            </tbody>
          </table>
        </div>
        <Pagination
          :page="page"
          :page-size="pageSize"
          :total="data?.total ?? 0"
          @page="page = $event"
        />
      </template>
    </Card>

    <Modal
      v-if="viewOrder"
      :open="true"
      :title="`Order ${viewOrder.order_reference}`"
      size="lg"
      @close="viewOrder = null"
    >
      <OrderDetail :order="viewOrder" />
    </Modal>
    <VerifyOrderModal
      v-if="verifyOrder"
      :order="verifyOrder"
      @close="verifyOrder = null"
    />
  </div>
</template>
