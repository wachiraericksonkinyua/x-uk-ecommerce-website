<script setup lang="ts">
import { ref, watch } from "vue";
import { ShieldAlert } from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";

import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import PageLoader from "./PageLoader.vue";
import AdminLayout from "./AdminLayout.vue";

type Status = "checking" | "ok" | "forbidden";

const router = useRouter();
const auth = useAuthStore();
const status = ref<Status>("checking");

watch(
  () => auth.token,
  async (token) => {
    if (!token) {
      await router.replace("/login");
      return;
    }
    status.value = "checking";
    try {
      await api.get("/admin/dashboard/summary");
      auth.setAdmin(true);
      status.value = "ok";
    } catch {
      auth.setAdmin(false);
      status.value = "forbidden";
    }
  },
  { immediate: true }
);

function signOut() {
  auth.logout();
  router.push("/login");
}
</script>

<template>
  <div v-if="!auth.token"></div>
  <PageLoader v-else-if="status === 'checking'" label="Verifying admin access…" />
  <div
    v-else-if="status === 'forbidden'"
    class="flex min-h-screen items-center justify-center bg-slate-50 px-4"
  >
    <div
      class="max-w-md rounded-2xl border border-rose-100 bg-white p-8 text-center shadow-sm"
    >
      <div
        class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-600"
      >
        <ShieldAlert :size="28" />
      </div>
      <h1 class="mt-4 text-xl font-bold text-slate-900">Access denied</h1>
      <p class="mt-2 text-sm text-slate-500">
        This account does not have admin privileges. If you believe this is a
        mistake, ask an owner to add your email to <code>ADMIN_EMAILS</code> or
        set <code>profiles.role = 'admin'</code>.
      </p>
      <div class="mt-6 flex justify-center gap-3">
        <button
          class="rounded-full bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
          @click="signOut"
        >
          Sign out
        </button>
        <RouterLink
          to="/login"
          class="rounded-full border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
        >
          Switch account
        </RouterLink>
      </div>
    </div>
  </div>
  <AdminLayout v-else />
</template>
