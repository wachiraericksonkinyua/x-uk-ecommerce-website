<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { LogIn } from "@lucide/vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import AuthShell from "../components/AuthShell.vue";
import { authApi, errorMessage } from "../lib/api";
import type { AuthUser, Session } from "../lib/types";
import { useAuthStore } from "../store/auth";

interface LoginResponse {
  success: boolean;
  session: Session;
  user?: AuthUser;
}

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const email = ref("");
const password = ref("");

const next = computed(() =>
  typeof route.query.next === "string" ? route.query.next : "/"
);

const login = useMutation({
  mutationFn: () =>
    authApi.post<LoginResponse>("/auth/login", {
      email: email.value,
      password: password.value,
    }),
  onSuccess: (res) => {
    if (!res?.session?.access_token) {
      toast.error("Login failed: no session returned");
      return;
    }
    auth.setSession(res.session, res.user ?? null);
    toast.success("Welcome back!");
    router.push(next.value);
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <AuthShell title="Sign in" subtitle="Access your cart, orders and wishlist.">
    <form class="space-y-4" @submit.prevent="login.mutate()">
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Email
        </label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="you@example.com"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <div class="flex items-center justify-between">
          <label class="text-xs font-semibold uppercase text-slate-500">
            Password
          </label>
          <RouterLink
            to="/forgot-password"
            class="text-xs font-medium text-brand-orange hover:underline"
          >
            Forgot?
          </RouterLink>
        </div>
        <input
          v-model="password"
          type="password"
          required
          placeholder="••••••••"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <button
        type="submit"
        :disabled="login.isPending.value"
        class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand-orange px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:bg-slate-300"
      >
        <LogIn :size="16" />
        {{ login.isPending.value ? "Signing in…" : "Sign in" }}
      </button>
    </form>

    <template #footer>
      New here?
      <RouterLink to="/signup" class="font-semibold text-brand-orange hover:underline">
        Create an account
      </RouterLink>
    </template>
  </AuthShell>
</template>
