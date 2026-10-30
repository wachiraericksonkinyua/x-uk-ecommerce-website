<script setup lang="ts">
import { useQueryClient } from "@tanstack/vue-query";
import {
  LayoutDashboard,
  LogOut,
  MessageCircle,
  Package,
  ShoppingCart,
  Star,
  Tags,
  Truck,
  Users,
} from "@lucide/vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../store/auth";
import { cn } from "../lib/utils";

const emit = defineEmits<{ close: [] }>();

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/orders", label: "Orders", icon: ShoppingCart, end: false },
  { to: "/products", label: "Products", icon: Package, end: false },
  { to: "/categories", label: "Categories", icon: Tags, end: false },
  { to: "/delivery", label: "Delivery Zones", icon: Truck, end: false },
  { to: "/customers", label: "Customers", icon: Users, end: false },
  { to: "/reviews", label: "Reviews", icon: Star, end: false },
  { to: "/leads", label: "WhatsApp Leads", icon: MessageCircle, end: false },
];

const router = useRouter();
const route = useRoute();
const queryClient = useQueryClient();
const auth = useAuthStore();

function isActive(to: string, end: boolean) {
  return end ? route.path === to : route.path.startsWith(to);
}

function handleLogout() {
  auth.logout();
  queryClient.clear();
  router.push("/login");
}
</script>

<template>
  <div class="flex h-full flex-col bg-[#061A40] text-slate-300">
    <div class="flex items-center gap-2 px-5 py-5">
      <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto" />
      <span class="text-[11px] font-medium uppercase tracking-wide text-slate-400">
        Admin
      </span>
    </div>

    <nav class="flex-1 space-y-1 px-3 py-2">
      <RouterLink
        v-for="item in NAV"
        :key="item.to"
        :to="item.to"
        :class="
          cn(
            'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition',
            isActive(item.to, item.end)
              ? 'bg-blue-700 text-white'
              : 'text-slate-300 hover:bg-white/5 hover:text-white'
          )
        "
        @click="emit('close')"
      >
        <component :is="item.icon" :size="18" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="border-t border-white/10 p-3">
      <div class="flex items-center gap-2 rounded-xl px-2 py-2">
        <span
          class="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-xs font-bold text-white"
        >
          {{ (auth.user?.email ?? "A")[0]?.toUpperCase() }}
        </span>
        <span class="flex-1 truncate text-xs text-slate-300">
          {{ auth.user?.email ?? "admin" }}
        </span>
        <button
          class="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white"
          aria-label="Sign out"
          @click="handleLogout"
        >
          <LogOut :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>
