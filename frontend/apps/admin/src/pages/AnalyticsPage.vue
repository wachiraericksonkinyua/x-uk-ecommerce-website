<script setup lang="ts">
import { computed } from "vue";
import {
  AlertTriangle,
  BarChart3,
  Boxes,
  CheckCircle2,
  Package,
  RotateCcw,
  TrendingUp,
} from "@lucide/vue";

import Badge from "../components/Badge.vue";
import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import { useSalesAnalytics } from "../hooks/queries";
import { formatDate, formatKES } from "../lib/utils";

const { data, isLoading } = useSalesAnalytics(14, 5);

const analytics = computed(() => data.value);
const maxRevenue = computed(() =>
  Math.max(1, ...(analytics.value?.daily_series ?? []).map((day) => day.revenue))
);

const stats = computed(() => {
  const current = analytics.value;
  if (!current) return [];
  return [
    {
      label: "Net Revenue",
      value: formatKES(current.revenue.net),
      hint: `${formatKES(current.revenue.refunded)} refunded`,
      icon: TrendingUp,
      tone: "bg-emerald-50 text-emerald-600",
    },
    {
      label: "Units Sold",
      value: String(current.units_sold),
      hint: `${current.orders.paid} paid orders`,
      icon: Package,
      tone: "bg-brand-orange-soft text-brand-orange-dark",
    },
    {
      label: "Low Stock",
      value: String(current.stock_alerts.length),
      hint: `At or below ${current.low_stock_threshold} units`,
      icon: AlertTriangle,
      tone: "bg-rose-50 text-rose-600",
    },
    {
      label: "Needs Verification",
      value: String(current.orders.unverified_paid),
      hint: `${current.orders.verified} already verified`,
      icon: CheckCircle2,
      tone: "bg-amber-50 text-amber-700",
    },
  ];
});

function barHeight(revenue: number) {
  return `${Math.max(4, Math.round((revenue / maxRevenue.value) * 100))}%`;
}

function reasonLabel(reason: string) {
  return reason.split("_").join(" ");
}
</script>

<template>
  <PageLoader v-if="isLoading || !analytics" label="Loading sales analytics…" />

  <div v-else>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Sales &amp; Analytics</h1>
        <p class="text-sm text-slate-500">
          Revenue, unit movement and stock health for the last
          {{ analytics.window_days }} days.
        </p>
      </div>
      <div class="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-500">
        <BarChart3 :size="15" class="text-brand-orange" />
        Live from paid and fulfilled orders
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card v-for="stat in stats" :key="stat.label" class="p-5">
        <span
          :class="`flex h-10 w-10 items-center justify-center rounded-xl ${stat.tone}`"
        >
          <component :is="stat.icon" :size="20" />
        </span>
        <p class="mt-4 text-2xl font-bold text-slate-900">{{ stat.value }}</p>
        <p class="mt-1 text-sm font-medium text-slate-700">{{ stat.label }}</p>
        <p class="mt-0.5 text-xs text-slate-400">{{ stat.hint }}</p>
      </Card>
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">
      <Card class="p-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Revenue Trend</h2>
            <p class="text-xs text-slate-400">Daily paid revenue</p>
          </div>
          <span class="rounded-full bg-brand-blue-50 px-3 py-1 text-xs font-semibold text-brand-blue-700">
            {{ formatKES(analytics.revenue.gross) }} gross
          </span>
        </div>

        <div class="mt-6 flex h-48 items-end gap-1.5">
          <div
            v-for="day in analytics.daily_series"
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
        <div class="mt-3 flex justify-between text-[10px] text-slate-400">
          <span>{{ analytics.daily_series[0]?.date?.slice(5) }}</span>
          <span>{{ analytics.daily_series[analytics.daily_series.length - 1]?.date?.slice(5) }}</span>
        </div>
      </Card>

      <Card class="p-5">
        <h2 class="text-sm font-bold text-slate-900">Revenue Breakdown</h2>
        <div class="mt-4 space-y-3 text-sm">
          <div class="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5">
            <span class="text-slate-500">Gross revenue</span>
            <span class="font-semibold text-slate-900">{{ formatKES(analytics.revenue.gross) }}</span>
          </div>
          <div class="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5">
            <span class="text-slate-500">Refunded</span>
            <span class="font-semibold text-rose-600">-{{ formatKES(analytics.revenue.refunded) }}</span>
          </div>
          <div class="flex items-center justify-between rounded-xl bg-brand-orange-soft px-3 py-2.5">
            <span class="font-medium text-brand-orange-dark">Net revenue</span>
            <span class="font-bold text-brand-orange-dark">{{ formatKES(analytics.revenue.net) }}</span>
          </div>
          <div class="flex items-center justify-between rounded-xl bg-brand-blue-50 px-3 py-2.5">
            <span class="text-brand-blue-700">Today</span>
            <span class="font-semibold text-brand-blue-700">{{ formatKES(analytics.revenue.today) }}</span>
          </div>
        </div>

        <h3 class="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Order pipeline
        </h3>
        <div class="mt-2 flex flex-wrap gap-2">
          <Badge
            v-for="(count, status) in analytics.status_breakdown"
            :key="status"
            class="bg-slate-100 text-slate-600"
          >
            {{ status }}: {{ count }}
          </Badge>
        </div>
      </Card>
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-2">
      <Card class="overflow-hidden">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Stock Alerts</h2>
            <p class="text-xs text-slate-400">Products at or below the warning threshold.</p>
          </div>
          <Boxes :size="20" class="text-slate-300" />
        </div>
        <p v-if="analytics.stock_alerts.length === 0" class="px-5 py-10 text-center text-sm text-slate-500">
          Every product is above the low-stock threshold.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50">
              <tr>
                <Th>Product</Th>
                <Th>Stock</Th>
                <Th>Units sold</Th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="product in analytics.stock_alerts"
                :key="product.id"
                class="border-t border-slate-100"
              >
                <Td>
                  <p class="font-medium text-slate-800">{{ product.name }}</p>
                  <p class="text-xs text-slate-400">{{ product.brand || "General" }}</p>
                </Td>
                <Td>
                  <span class="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-700">
                    {{ product.stock_quantity }}
                  </span>
                </Td>
                <Td class="text-slate-600">{{ product.units_sold }}</Td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <Card class="overflow-hidden">
        <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Top Products</h2>
            <p class="text-xs text-slate-400">Ranked by units sold in paid orders.</p>
          </div>
          <TrendingUp :size="20" class="text-slate-300" />
        </div>
        <p v-if="analytics.top_products.length === 0" class="px-5 py-10 text-center text-sm text-slate-500">
          No paid product movement yet.
        </p>
        <div v-else class="divide-y divide-slate-100">
          <div
            v-for="(product, index) in analytics.top_products"
            :key="product.product_id"
            class="flex items-center gap-3 px-5 py-3"
          >
            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue-50 text-xs font-bold text-brand-blue-700">
              {{ index + 1 }}
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-800">{{ product.name }}</p>
              <p class="text-xs text-slate-400">{{ product.units }} units moved</p>
            </div>
            <p class="text-sm font-semibold text-slate-900">{{ formatKES(product.revenue) }}</p>
          </div>
        </div>
      </Card>
    </div>

    <Card class="mt-6 overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 class="text-sm font-bold text-slate-900">Unit Movement History</h2>
          <p class="text-xs text-slate-400">Sales, refunds, cancellations and manual adjustments.</p>
        </div>
        <RotateCcw :size="20" class="text-slate-300" />
      </div>
      <div v-if="analytics.movements.length === 0" class="p-6">
        <EmptyState
          title="No movement recorded yet"
          description="Inventory changes will appear here after the next sale or stock adjustment."
        />
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-slate-50">
            <tr>
              <Th>When</Th>
              <Th>Product</Th>
              <Th>Change</Th>
              <Th>Before</Th>
              <Th>After</Th>
              <Th>Reason</Th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="movement in analytics.movements"
              :key="movement.id"
              class="border-t border-slate-100"
            >
              <Td class="whitespace-nowrap text-slate-500">{{ formatDate(movement.created_at) }}</Td>
              <Td>
                <p class="text-sm text-slate-700">{{ movement.product_name || "Unknown product" }}</p>
                <p class="font-mono text-[10px] text-slate-400">{{ movement.product_id?.slice(0, 8) || "—" }}</p>
              </Td>
              <Td>
                <span
                  :class="
                    movement.change_qty >= 0
                      ? 'font-semibold text-brand-orange'
                      : 'font-semibold text-rose-600'
                  "
                >
                  {{ movement.change_qty > 0 ? "+" : "" }}{{ movement.change_qty }}
                </span>
              </Td>
              <Td class="text-slate-600">{{ movement.quantity_before ?? "—" }}</Td>
              <Td class="text-slate-600">{{ movement.quantity_after ?? "—" }}</Td>
              <Td>
                <Badge class="bg-slate-100 capitalize text-slate-600">
                  {{ reasonLabel(movement.reason) }}
                </Badge>
              </Td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>
