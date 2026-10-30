<script setup lang="ts">
import { computed } from "vue";
import {
  AlertTriangle,
  DollarSign,
  PackageCheck,
  ShoppingCart,
  Users,
} from "@lucide/vue";

import Card from "../components/Card.vue";
import PageLoader from "../components/PageLoader.vue";
import RestockRow from "../components/RestockRow.vue";
import Th from "../components/Th.vue";
import { useDashboardSummary, useLowStock } from "../hooks/queries";
import { formatKES } from "../lib/utils";

const { data: summary, isLoading } = useDashboardSummary();
const { data: lowStock } = useLowStock();

const products = computed(
  () => lowStock.value?.data ?? summary.value?.low_stock_products ?? []
);

const tones: Record<string, string> = {
  blue: "bg-blue-50 text-blue-700",
  amber: "bg-amber-50 text-amber-700",
  rose: "bg-rose-50 text-rose-700",
  emerald: "bg-emerald-50 text-emerald-700",
};

const stats = computed(() => {
  const current = summary.value;
  if (!current) return [];
  return [
    {
      icon: DollarSign,
      label: "Daily Revenue",
      value: formatKES(current.daily_revenue),
      tone: "emerald",
    },
    {
      icon: ShoppingCart,
      label: "Pending Orders",
      value: String(current.pending_orders),
      tone: "amber",
    },
    {
      icon: AlertTriangle,
      label: "Low Stock Count",
      value: String(products.value.length),
      tone: "rose",
    },
    {
      icon: Users,
      label: "Total Customers",
      value: String(current.total_customers),
      tone: "blue",
    },
  ];
});
</script>

<template>
  <PageLoader v-if="isLoading || !summary" label="Loading dashboard…" />

  <div v-else>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Dashboard Overview</h1>
      <p class="text-sm text-slate-500">
        A snapshot of your store's performance today.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card v-for="stat in stats" :key="stat.label" class="p-5">
        <div class="flex items-center justify-between">
          <span
            :class="`flex h-10 w-10 items-center justify-center rounded-xl ${tones[stat.tone]}`"
          >
            <component :is="stat.icon" :size="20" />
          </span>
        </div>
        <p class="mt-4 text-2xl font-bold text-slate-900">{{ stat.value }}</p>
        <p class="mt-1 text-sm text-slate-500">{{ stat.label }}</p>
      </Card>
    </div>

    <Card class="mt-8 overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 class="text-sm font-bold text-slate-900">Low Stock Alert</h2>
          <p class="text-xs text-slate-500">
            Quick-restock products running low (below
            {{ summary.low_stock_threshold }}).
          </p>
        </div>
        <PackageCheck class="text-slate-300" :size="22" />
      </div>

      <p v-if="products.length === 0" class="px-5 py-10 text-center text-sm text-slate-500">
        All products are well stocked.
      </p>
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-slate-50">
            <tr>
              <Th>Product</Th>
              <Th>Current Stock</Th>
              <Th>Set New Stock</Th>
            </tr>
          </thead>
          <tbody>
            <RestockRow
              v-for="product in products"
              :key="product.id"
              :id="product.id"
              :name="product.name"
              :brand="product.brand"
              :stock="product.stock_quantity"
            />
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
