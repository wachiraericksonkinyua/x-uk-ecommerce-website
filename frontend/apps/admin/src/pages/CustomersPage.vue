<script setup lang="ts">
import { computed, ref } from "vue";
import { Search, User } from "@lucide/vue";

import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import Modal from "../components/Modal.vue";
import PageLoader from "../components/PageLoader.vue";
import Pagination from "../components/Pagination.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import CustomerDetail from "../components/CustomerDetail.vue";
import { useAdminCustomers } from "../hooks/queries";
import type { Customer } from "../lib/types";
import { formatDate } from "../lib/utils";

const page = ref(1);
const searchInput = ref("");
const search = ref("");
const selected = ref<Customer | null>(null);

const pageSize = 20;

const { data, isLoading } = useAdminCustomers(() => ({
  page: page.value,
  pageSize,
  search: search.value,
}));

const customers = computed(() => data.value?.data ?? []);

function submitSearch() {
  page.value = 1;
  search.value = searchInput.value.trim();
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Customers</h1>
      <p class="text-sm text-slate-500">
        Browse registered customers and their order history.
      </p>
    </div>

    <Card class="overflow-hidden">
      <div class="border-b border-slate-100 p-4">
        <form
          class="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="searchInput"
            placeholder="Search by name or phone…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>
      </div>

      <PageLoader v-if="isLoading" label="Loading customers…" />
      <div v-else-if="customers.length === 0" class="p-6">
        <EmptyState title="No customers found" />
      </div>
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50">
              <tr>
                <Th>Customer</Th>
                <Th>Phone</Th>
                <Th>Role</Th>
                <Th>Joined</Th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="customer in customers"
                :key="customer.user_id"
                class="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50"
                @click="selected = customer"
              >
                <Td>
                  <div class="flex items-center gap-3">
                    <span
                      class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-700"
                    >
                      <User :size="16" />
                    </span>
                    <div>
                      <p class="font-medium text-slate-800">
                        {{ customer.full_name || "Unnamed" }}
                      </p>
                      <p class="text-xs text-slate-400">
                        {{ customer.user_id.slice(0, 8) }}…
                      </p>
                    </div>
                  </div>
                </Td>
                <Td>{{ customer.phone_number || "—" }}</Td>
                <Td class="capitalize">{{ customer.role || "customer" }}</Td>
                <Td>{{ formatDate(customer.created_at) }}</Td>
              </tr>
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
      v-if="selected"
      :open="true"
      :title="selected.full_name || 'Customer'"
      size="lg"
      @close="selected = null"
    >
      <CustomerDetail :user-id="selected.user_id" />
    </Modal>
  </div>
</template>
