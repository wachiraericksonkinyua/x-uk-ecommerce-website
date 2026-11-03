<script setup lang="ts">
import { computed } from "vue";
import { Home, Search, ShoppingBag, User } from "@lucide/vue";
import { RouterLink, useRoute } from "vue-router";

import { useCart } from "../hooks/queries";
import { useAuthStore } from "../store/auth";

const route = useRoute();
const auth = useAuthStore();
const { data: cart } = useCart(() => Boolean(auth.token));

const cartCount = computed(() =>
  (cart.value ?? []).reduce((sum, item) => sum + item.quantity, 0)
);

const showDock = computed(
  () =>
    !["/login", "/signup", "/forgot-password", "/reset-password"].includes(
      route.path
    )
);

const items = computed(() => [
  { to: "/", label: "Home", icon: Home, active: route.path === "/" },
  { to: "/shop", label: "Shop", icon: Search, active: route.path.startsWith("/shop") },
  {
    to: "/cart",
    label: "Cart",
    icon: ShoppingBag,
    active: route.path === "/cart",
    badge: cartCount.value,
  },
  {
    to: auth.token ? "/profile" : "/login?next=/profile",
    label: "Profile",
    icon: User,
    active: route.path === "/profile",
  },
]);
</script>

<template>
  <nav
    v-if="showDock"
    class="fixed inset-x-6 bottom-4 z-40 mx-auto grid max-w-md grid-cols-4 gap-1 rounded-3xl border border-white/70 bg-white/90 p-1.5 shadow-[0_18px_45px_-18px_rgba(15,23,42,0.45)] backdrop-blur-xl md:hidden"
    aria-label="Mobile navigation"
  >
    <RouterLink
      v-for="item in items"
      :key="item.label"
      :to="item.to"
      :class="[
        'relative flex flex-col items-center justify-center gap-1 rounded-2xl px-2 py-2 text-[10px] font-semibold transition',
        item.active
          ? 'bg-brand-orange text-white shadow-[0_10px_20px_-12px_rgba(255,79,0,0.9)]'
          : 'text-slate-500 hover:bg-brand-blue-50 hover:text-brand-orange',
      ]"
      :aria-current="item.active ? 'page' : undefined"
    >
      <component :is="item.icon" :size="18" />
      <span>{{ item.label }}</span>
      <span
        v-if="item.badge"
        class="absolute right-2 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-blue-500 px-1 text-[9px] font-bold text-slate-900"
      >
        {{ item.badge }}
      </span>
    </RouterLink>
  </nav>
</template>
