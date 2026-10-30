<script setup lang="ts">
import { ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { useRouter } from "vue-router";
import { toast } from "vue-sonner";

import { authApi, errorMessage } from "../lib/api";
import type { AuthUser, Session } from "../lib/types";
import { useAuthStore } from "../store/auth";

interface LoginResponse {
  success: boolean;
  session: Session;
  user?: AuthUser;
}

const router = useRouter();
const auth = useAuthStore();
const email = ref("");
const password = ref("");

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
    toast.success("Signed in. Verifying admin access…");
    router.push("/");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#061A40] via-[#0B3578] to-[#1565C0] px-4"
  >
    <div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl">
      <div class="flex items-center gap-3">
        <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto" />
        <div>
          <h1 class="text-lg font-bold text-slate-900">Admin</h1>
          <p class="text-xs text-slate-500">Authorized personnel only</p>
        </div>
      </div>

      <form class="mt-6 space-y-4" @submit.prevent="login.mutate()">
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Email
          </label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="admin@x-uk.com"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Password
          </label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="••••••••"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <button
          type="submit"
          :disabled="login.isPending.value"
          class="w-full rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-slate-300"
        >
          {{ login.isPending.value ? "Signing in…" : "Sign in" }}
        </button>
      </form>

      <p class="mt-4 text-center text-xs text-slate-400">
        Access is verified against the server on every login.
      </p>
    </div>
  </div>
</template>
