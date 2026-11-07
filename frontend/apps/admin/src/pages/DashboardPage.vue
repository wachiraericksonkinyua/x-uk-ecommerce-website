<script setup lang="ts">
import { computed } from "vue";
import {
  AlertTriangle,
  ArrowUpRight,
  BadgeCheck,
  Banknote,
  ExternalLink,
  PackageCheck,
  PackagePlus,
  Plus,
  ShoppingCart,
  TrendingUp,
  Users,
} from "@lucide/vue";
import { RouterLink } from "vue-router";

import Card from "../components/Card.vue";
import PageLoader from "../components/PageLoader.vue";
import RestockRow from "../components/RestockRow.vue";
import Th from "../components/Th.vue";
import { useDashboardSummary, useLowStock } from "../hooks/queries";
import { formatDate, formatKES, statusColor } from "../lib/utils";

const { data: summary, isLoading } = useDashboardSummary();
const { data: lowStock } = useLowStock();

const products = computed(
  () => lowStock.value?.data ?? summary.value?.low_stock_products ?? []
);

const series = computed(() => summary.value?.revenue_series ?? []);
const recentOrders = computed(() => summary.value?.recent_orders ?? []);
const topProducts = computed(() => summary.value?.top_products ?? []);
const maxRevenue = computed(() =>
  Math.max(1, ...series.value.map((day) => day.revenue))
);

const stats = computed(() => {
  const current = summary.value;
  if (!current) return [];
  const avg = current.paid_orders
    ? current.total_revenue / current.paid_orders
    : 0;
  return [
    {
      icon: Banknote,
      label: "Paid revenue",
      value: formatKES(current.total_revenue),
      hint: `${current.paid_orders} paid orders`,
      tone: "bg-emerald-50 text-emerald-600",
    },
    {
      icon: TrendingUp,
      label: "Revenue today",
      value: formatKES(current.daily_revenue),
      hint: `${formatKES(avg)} avg. order`,
      tone: "bg-brand-orange-soft text-brand-orange-dark",
    },
    {
      icon: ShoppingCart,
      label: "Awaiting payment",
      value: String(current.pending_orders),
      hint: `${current.total_orders} orders total`,
      tone: "bg-amber-50 text-amber-600",
    },
    {
      icon: Users,
      label: "Customers",
      value: String(current.total_customers),
      hint: `${formatKES(current.refunded_revenue)} refunded`,
      tone: "bg-sky-50 text-sky-600",
    },
  ];
});

const pipeline = computed(() => {
  const breakdown = summary.value?.status_breakdown ?? {};
  const total = Math.max(1, summary.value?.total_orders ?? 1);
  const order = [
    "paid",
    "processing",
    "shipped",
    "delivered",
    "pending pin",
    "payment failed",
    "cancelled",
    "refunded",
  ];
  return order
    .filter((key) => (breakdown[key] ?? 0) > 0)
    .map((key) => ({
      label: key.replace(/\b\w/g, (char) => char.toUpperCase()),
      count: breakdown[key],
      share: Math.round(((breakdown[key] ?? 0) / total) * 100),
    }));
});

const storefrontUrl = import.meta.env.VITE_STOREFRONT_URL || "http://localhost:5173";

const quickActions = [
  { to: "/products?create=1", label: "Add product", text: "Create a listing", icon: PackagePlus },
  { to: "/orders", label: "Review orders", text: "Update fulfilment", icon: ShoppingCart },
  { to: "/inventory", label: "Restock", text: "Fix low stock", icon: PackageCheck },
  { to: "/analytics", label: "Analytics", text: "Read the numbers", icon: BadgeCheck },
];

function barHeight(revenue: number) {
  return `${Math.max(4, Math.round((revenue / maxRevenue.value) * 100))}%`;
}
</script>

<template>
  <PageLoader v-if="isLoading || !summary" label="Loading dashboard…" />

  <div v-else class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-orange">
          Overview
        </p>
        <h1 class="mt-1 font-display text-2xl font-semibold tracking-tight text-slate-900">
          Store performance
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          Revenue, orders and inventory health — updated live.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span class="chip">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Live
        </span>
        <RouterLink :to="{ path: '/products', query: { create: '1' } }" class="btn-primary">
          <Plus :size="16" /> Add product
        </RouterLink>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="stat in stats" :key="stat.label" class="kpi-card">
        <div class="flex items-start justify-between">
          <p class="kpi-label">{{ stat.label }}</p>
          <span :class="`flex h-9 w-9 items-center justify-center rounded-lg ${stat.tone}`">
            <component :is="stat.icon" :size="18" />
          </span>
        </div>
        <p class="kpi-value">{{ stat.value }}</p>
        <p class="mt-1 text-xs text-slate-400">{{ stat.hint }}</p>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
      <Card class="p-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="section-title">Revenue trend</h2>
            <p class="section-subtitle">Paid revenue over the last {{ series.length }} days</p>
          </div>
          <span class="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
            {{ formatKES(series.reduce((sum, day) => sum + day.revenue, 0)) }}
          </span>
        </div>

        <div class="mt-6 flex h-52 items-end gap-1.5">
          <div
            v-for="day in series"
            :key="day.date"
            class="group relative flex h-full flex-1 items-end"
            :title="`${day.date}: ${formatKES(day.revenue)} · ${day.orders} orders`"
          >
            <div
              class="w-full rounded-t-md bg-brand-orange/85 transition-all duration-300 group-hover:bg-brand-orange"
              :style="{ height: barHeight(day.revenue) }"
            />
          </div>
        </div>
        <div class="mt-3 flex justify-between text-[10px] font-medium text-slate-400">
          <span>{{ series[0]?.date?.slice(5) }}</span>
          <span>{{ series[series.length - 1]?.date?.slice(5) }}</span>
        </div>

        <div class="mt-5 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3">
          <div>
            <p class="kpi-label">Gross</p>
            <p class="mt-1 text-sm font-semibold text-slate-900">
              {{ formatKES(summary.total_revenue) }}
            </p>
          </div>
          <div>
            <p class="kpi-label">Refunded</p>
            <p class="mt-1 text-sm font-semibold text-rose-600">
              -{{ formatKES(summary.refunded_revenue) }}
            </p>
          </div>
          <div>
            <p class="kpi-label">Net</p>
            <p class="mt-1 text-sm font-semibold text-emerald-600">
              {{ formatKES(summary.net_revenue) }}
            </p>
          </div>
        </div>
      </Card>

      <Card class="p-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="section-title">Order pipeline</h2>
            <p class="section-subtitle">Where every order sits right now</p>
          </div>
          <RouterLink to="/orders" class="text-xs font-semibold text-brand-orange hover:text-brand-orange-dark">
            View all
          </RouterLink>
        </div>

        <div v-if="pipeline.length === 0" class="py-10 text-center text-sm text-slate-400">
          No orders yet.
        </div>
        <div v-else class="mt-5 space-y-4">
          <div v-for="row in pipeline" :key="row.label">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-slate-600">{{ row.label }}</span>
              <span class="font-semibold text-slate-900">{{ row.count }}</span>
            </div>
            <div class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                class="h-full rounded-full bg-ink-800"
                :style="{ width: `${Math.max(3, row.share)}%` }"
              />
            </div>
          </div>
        </div>
      </Card>
    </div>

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <RouterLink
        v-for="action in quickActions"
        :key="action.to"
        :to="action.to"
        class="panel group flex items-center gap-3 p-4 transition hover:border-slate-300 hover:shadow-lift"
      >
        <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-600 transition group-hover:bg-ink-900 group-hover:text-white">
          <component :is="action.icon" :size="18" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block text-sm font-semibold text-slate-900">{{ action.label }}</span>
          <span class="block text-xs text-slate-400">{{ action.text }}</span>
        </span>
        <ArrowUpRight :size="16" class="text-slate-300 transition group-hover:text-brand-orange" />
      </RouterLink>
    </div>

    <div class="grid gap-6 xl:grid-cols-[1.55fr_1fr]">
      <Card class="overflow-hidden">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="section-title">Recent orders</h2>
            <p class="section-subtitle">The latest activity across the store</p>
          </div>
          <RouterLink to="/orders" class="text-xs font-semibold text-brand-orange hover:text-brand-orange-dark">
            Manage
          </RouterLink>
        </div>

        <p v-if="recentOrders.length === 0" class="px-5 py-12 text-center text-sm text-slate-400">
          No orders yet.
        </p>
        <div v-else class="table-shell">
          <table class="w-full">
            <thead class="bg-slate-50/80">
              <tr>
                <Th>Reference</Th>
                <Th>Customer</Th>
                <Th>Status</Th>
                <Th class="text-right">Total</Th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="order in recentOrders"
                :key="order.id"
                class="border-t border-slate-100"
              >
                <td class="px-4 py-3">
                  <p class="font-mono text-xs font-semibold text-slate-900">
                    {{ order.order_reference || "—" }}
                  </p>
                  <p class="text-[11px] text-slate-400">{{ formatDate(order.created_at) }}</p>
                </td>
                <td class="px-4 py-3">
                  <p class="max-w-[190px] truncate text-sm text-slate-700">
                    {{ order.customer_email || order.customer_phone || "Guest" }}
                  </p>
                  <p class="text-[11px] text-slate-400">{{ order.fulfillment || "—" }}</p>
                </td>
                <td class="px-4 py-3">
                  <span
                    :class="`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusColor(order.status)}`"
                  >
                    {{ order.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right text-sm font-semibold text-slate-900">
                  {{ formatKES(order.total_amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <Card class="overflow-hidden">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="section-title">Low stock</h2>
            <p class="section-subtitle">Below {{ summary.low_stock_threshold }} units</p>
          </div>
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <AlertTriangle :size="16" />
          </span>
        </div>

        <p v-if="products.length === 0" class="px-5 py-12 text-center text-sm text-slate-400">
          Every product is well stocked.
        </p>
        <div v-else class="table-shell">
          <table class="w-full">
            <thead class="bg-slate-50/80">
              <tr>
                <Th>Product</Th>
                <Th>Stock</Th>
                <Th>Restock</Th>
              </tr>
            </thead>
            <tbody>
              <RestockRow
                v-for="product in products.slice(0, 6)"
                :key="product.id"
                :id="product.id"
                :name="product.name"
                :brand="product.brand"
                :stock="product.stock_quantity"
              />
            </tbody>
          </table>
        </div>
        <div class="border-t border-slate-100 px-5 py-3">
          <RouterLink to="/inventory" class="text-xs font-semibold text-brand-orange hover:text-brand-orange-dark">
            Open inventory →
          </RouterLink>
        </div>
      </Card>
    </div>

    <Card class="p-5">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="section-title">Top products</h2>
          <p class="section-subtitle">Ranked by units sold in paid orders</p>
        </div>
        <a
          :href="storefrontUrl"
          target="_blank"
          rel="noreferrer"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900"
        >
          View storefront <ExternalLink :size="13" />
        </a>
      </div>

      <p v-if="topProducts.length === 0" class="py-8 text-center text-sm text-slate-400">
        No paid product movement yet.
      </p>
      <div v-else class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <div
          v-for="(product, index) in topProducts"
          :key="product.product_id"
          class="rounded-xl border border-slate-100 bg-slate-50/60 p-3"
        >
          <div class="flex items-center justify-between">
            <span class="flex h-6 w-6 items-center justify-center rounded-md bg-white text-[11px] font-bold text-slate-500 shadow-sm">
              {{ index + 1 }}
            </span>
            <span class="text-[11px] font-semibold text-emerald-600">
              {{ product.units }} sold
            </span>
          </div>
          <p class="mt-2 truncate text-sm font-medium text-slate-800" :title="product.name">
            {{ product.name }}
          </p>
          <p class="text-xs text-slate-400">{{ formatKES(product.revenue) }}</p>
        </div>
      </div>
    </Card>
  </div>
</template>
