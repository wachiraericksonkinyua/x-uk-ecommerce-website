<script setup lang="ts">
import { computed, ref } from "vue";
import { useQueryClient } from "@tanstack/vue-query";
import { ExternalLink, Menu, RefreshCw, X } from "@lucide/vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import AdminSidebar from "./AdminSidebar.vue";

const open = ref(false);
const route = useRoute();
const queryClient = useQueryClient();

const TITLES: Record<string, { title: string; crumb: string }> = {
  "/": { title: "Dashboard", crumb: "Overview" },
  "/analytics": { title: "Revenue & Analytics", crumb: "Overview" },
  "/orders": { title: "Orders", crumb: "Commerce" },
  "/products": { title: "Products", crumb: "Commerce" },
  "/categories": { title: "Categories", crumb: "Commerce" },
  "/inventory": { title: "Inventory", crumb: "Commerce" },
  "/delivery": { title: "Delivery Zones", crumb: "Operations" },
  "/customers": { title: "Customers", crumb: "Operations" },
  "/reviews": { title: "Reviews", crumb: "Operations" },
  "/leads": { title: "WhatsApp Leads", crumb: "Operations" },
};

const page = computed(() => {
  const match = Object.entries(TITLES)
    .filter(([path]) => (path === "/" ? route.path === "/" : route.path.startsWith(path)))
    .sort((a, b) => b[0].length - a[0].length)[0];
  return match?.[1] ?? { title: "Admin", crumb: "Console" };
});

const storefrontUrl = import.meta.env.VITE_STOREFRONT_URL || "http://localhost:5173";

const today = new Intl.DateTimeFormat("en-KE", {
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric",
}).format(new Date());

const refreshing = ref(false);
async function refreshAll() {
  refreshing.value = true;
  try {
    await queryClient.invalidateQueries();
  } finally {
    window.setTimeout(() => (refreshing.value = false), 500);
  }
}
</script>

<template>
  <div class="flex min-h-screen bg-[#f5f7fa]">
    <aside class="hidden w-[268px] shrink-0 lg:block">
      <div class="fixed inset-y-0 left-0 w-[268px]">
        <AdminSidebar @close="open = false" />
      </div>
    </aside>

    <div v-if="open" class="fixed inset-0 z-40 lg:hidden">
      <div class="absolute inset-0 bg-ink-950/60 backdrop-blur-sm" @click="open = false" />
      <div class="absolute left-0 top-0 h-full w-[268px]">
        <AdminSidebar @close="open = false" />
      </div>
    </div>

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div class="flex items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <button
            class="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Menu"
            @click="open = !open"
          >
            <X v-if="open" :size="20" />
            <Menu v-else :size="20" />
          </button>

          <div class="min-w-0 flex-1">
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              {{ page.crumb }} <span class="mx-1 text-slate-300">/</span> {{ page.title }}
            </p>
            <h2 class="truncate font-display text-sm font-semibold text-slate-900">
              Admin console
            </h2>
          </div>

          <span class="hidden text-xs text-slate-400 md:block">{{ today }}</span>

          <button
            class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            :disabled="refreshing"
            @click="refreshAll"
          >
            <RefreshCw :size="14" :class="refreshing ? 'animate-spin' : ''" />
            <span class="hidden sm:inline">Refresh</span>
          </button>

          <a
            :href="storefrontUrl"
            target="_blank"
            rel="noreferrer"
            class="inline-flex items-center gap-2 rounded-xl bg-ink-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-ink-700"
          >
            <ExternalLink :size="14" />
            <span class="hidden sm:inline">Storefront</span>
          </a>
        </div>
      </header>

      <main class="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <RouterView />
      </main>

      <footer class="border-t border-slate-200/70 px-4 py-4 text-center text-[11px] text-slate-400 sm:px-6 lg:px-8">
        <RouterLink to="/" class="hover:text-slate-600">Gadgets With Vin</RouterLink>
        <span class="mx-1.5">·</span>
        Admin console
        <span class="mx-1.5">·</span>
        Secured with role-based access
      </footer>
    </div>
  </div>
</template>
