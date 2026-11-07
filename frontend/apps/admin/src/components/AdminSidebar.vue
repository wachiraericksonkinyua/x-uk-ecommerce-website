<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import {
  BarChart3,
  Boxes,
  KeyRound,
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
import { toast } from "vue-sonner";

import { useAuthStore } from "../store/auth";
import { api, errorMessage } from "../lib/api";
import { cn } from "../lib/utils";
import Modal from "./Modal.vue";

const emit = defineEmits<{ close: [] }>();

const NAV_GROUPS = [
  {
    label: "Overview",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
      { to: "/analytics", label: "Revenue & Analytics", icon: BarChart3, end: false },
    ],
  },
  {
    label: "Commerce",
    items: [
      { to: "/orders", label: "Orders", icon: ShoppingCart, end: false },
      { to: "/products", label: "Products", icon: Package, end: false },
      { to: "/categories", label: "Categories", icon: Tags, end: false },
      { to: "/inventory", label: "Inventory", icon: Boxes, end: false },
    ],
  },
  {
    label: "Operations",
    items: [
      { to: "/delivery", label: "Delivery Zones", icon: Truck, end: false },
      { to: "/customers", label: "Customers", icon: Users, end: false },
      { to: "/reviews", label: "Reviews", icon: Star, end: false },
      { to: "/leads", label: "WhatsApp Leads", icon: MessageCircle, end: false },
    ],
  },
];

const router = useRouter();
const route = useRoute();
const queryClient = useQueryClient();
const auth = useAuthStore();

const showPassword = ref(false);
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

function isActive(to: string, end: boolean) {
  return end ? route.path === to : route.path.startsWith(to);
}

function handleLogout() {
  auth.logout();
  queryClient.clear();
  router.push("/login");
}

const changePassword = useMutation({
  mutationFn: () =>
    api.post("/auth/change-password", {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    }),
  onSuccess: () => {
    toast.success("Password updated");
    showPassword.value = false;
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function submitPassword() {
  if (newPassword.value.length < 8) {
    toast.error("Use at least 8 characters.");
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    toast.error("The new passwords do not match.");
    return;
  }
  changePassword.mutate();
}
</script>

<template>
  <div class="flex h-full flex-col bg-ink-900 text-slate-300">
    <div class="flex items-center gap-3 px-5 pb-5 pt-6">
      <div class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-white/95 p-1.5">
        <img src="/logo-mark.png" alt="Gadgets With Vin" class="h-full w-full object-contain" />
      </div>
      <div class="min-w-0">
        <p class="truncate font-display text-sm font-semibold text-white">Gadgets With Vin</p>
        <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Admin Console
        </p>
      </div>
    </div>

    <nav class="flex-1 space-y-6 overflow-y-auto px-3 pb-4 no-scrollbar">
      <div v-for="group in NAV_GROUPS" :key="group.label">
        <p class="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {{ group.label }}
        </p>
        <div class="space-y-0.5">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            :class="
              cn(
                'group flex items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-sm font-medium transition',
                isActive(item.to, item.end)
                  ? 'border-brand-orange bg-white/[0.07] text-white'
                  : 'border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-100'
              )
            "
            @click="emit('close')"
          >
            <component
              :is="item.icon"
              :size="17"
              :class="isActive(item.to, item.end) ? 'text-brand-orange' : 'text-slate-500 group-hover:text-slate-300'"
            />
            {{ item.label }}
          </RouterLink>
        </div>
      </div>
    </nav>

    <div class="border-t border-white/[0.07] p-3">
      <div class="flex items-center gap-2.5 rounded-xl bg-white/[0.04] px-3 py-2.5">
        <span
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-orange/15 text-xs font-bold text-brand-orange"
        >
          {{ (auth.user?.email ?? "A")[0]?.toUpperCase() }}
        </span>
        <span class="min-w-0 flex-1 truncate text-xs text-slate-300">
          {{ auth.user?.email ?? "admin" }}
        </span>
        <button
          class="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/10 hover:text-white"
          aria-label="Change password"
          title="Change password"
          @click="showPassword = true"
        >
          <KeyRound :size="15" />
        </button>
        <button
          class="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/10 hover:text-white"
          aria-label="Sign out"
          title="Sign out"
          @click="handleLogout"
        >
          <LogOut :size="15" />
        </button>
      </div>
    </div>

    <Modal :open="showPassword" title="Change admin password" @close="showPassword = false">
      <form class="space-y-4" @submit.prevent="submitPassword">
        <div>
          <label class="label">Current password</label>
          <input v-model="currentPassword" type="password" required class="field mt-2" autocomplete="current-password" />
        </div>
        <div>
          <label class="label">New password</label>
          <input v-model="newPassword" type="password" required minlength="8" class="field mt-2" autocomplete="new-password" />
          <p class="mt-1 text-xs text-slate-400">At least 8 characters.</p>
        </div>
        <div>
          <label class="label">Confirm new password</label>
          <input v-model="confirmPassword" type="password" required minlength="8" class="field mt-2" autocomplete="new-password" />
        </div>
        <div class="flex justify-end gap-2 pt-1">
          <button type="button" class="btn-secondary" @click="showPassword = false">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="changePassword.isPending.value">
            {{ changePassword.isPending.value ? "Updating…" : "Update password" }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
