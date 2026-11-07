<script setup lang="ts">
import { ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  BarChart3,
  Eye,
  EyeOff,
  LockKeyhole,
  PackageCheck,
  ShieldCheck,
} from "@lucide/vue";
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
const showPassword = ref(false);

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

const highlights = [
  { icon: BarChart3, title: "Live revenue", text: "Daily, net and refunded revenue at a glance." },
  { icon: PackageCheck, title: "Stock control", text: "Restock products before they run out." },
  { icon: ShieldCheck, title: "Role secured", text: "Every request is verified server-side." },
];
</script>

<template>
  <div class="flex min-h-screen bg-[#f5f7fa]">
    <section class="relative hidden w-[46%] flex-col justify-between overflow-hidden bg-ink-900 p-12 text-white lg:flex">
      <div class="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-orange/10 blur-3xl" />
      <div class="absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-white/[0.03] blur-2xl" />

      <div class="relative">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center overflow-hidden rounded-xl bg-white p-1.5">
            <img src="/logo-mark.png" alt="Gadgets With Vin" class="h-full w-full object-contain" />
          </div>
          <div>
            <p class="font-display text-sm font-semibold">Gadgets With Vin</p>
            <p class="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
              Admin console
            </p>
          </div>
        </div>

        <h1 class="mt-16 max-w-md font-display text-4xl font-semibold leading-tight tracking-tight">
          Run the store with clarity.
        </h1>
        <p class="mt-4 max-w-sm text-sm leading-relaxed text-slate-400">
          Orders, revenue, inventory and customer conversations — one calm,
          focused workspace for the team.
        </p>

        <ul class="mt-10 space-y-4">
          <li v-for="item in highlights" :key="item.title" class="flex items-start gap-3">
            <span class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.06] text-brand-orange">
              <component :is="item.icon" :size="17" />
            </span>
            <div>
              <p class="text-sm font-semibold text-slate-100">{{ item.title }}</p>
              <p class="text-xs text-slate-500">{{ item.text }}</p>
            </div>
          </li>
        </ul>
      </div>

      <p class="relative text-[11px] text-slate-600">
        Authorized personnel only · Access is verified on every request.
      </p>
    </section>

    <section class="flex flex-1 items-center justify-center px-4 py-12 sm:px-8">
      <div class="w-full max-w-md">
        <div class="mb-8 flex items-center gap-3 lg:hidden">
          <div class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-ink-900 p-1.5">
            <img src="/logo-mark.png" alt="Gadgets With Vin" class="h-full w-full object-contain" />
          </div>
          <div>
            <p class="font-display text-sm font-semibold text-slate-900">Gadgets With Vin</p>
            <p class="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              Admin console
            </p>
          </div>
        </div>

        <div class="panel p-7 sm:p-8">
          <span class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
            <LockKeyhole :size="12" /> Secure sign in
          </span>
          <h2 class="mt-4 font-display text-2xl font-semibold tracking-tight text-slate-900">
            Welcome back
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Sign in with your admin account to continue.
          </p>

          <form class="mt-6 space-y-4" @submit.prevent="login.mutate()">
            <div>
              <label class="label" for="admin-email">Email</label>
              <input
                id="admin-email"
                v-model="email"
                type="email"
                required
                autocomplete="username"
                placeholder="you@x-uk.com"
                class="field mt-2"
              />
            </div>
            <div>
              <div class="flex items-center justify-between">
                <label class="label" for="admin-password">Password</label>
              </div>
              <div class="relative mt-2">
                <input
                  id="admin-password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="current-password"
                  placeholder="Enter your password"
                  class="field pr-11"
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-slate-400 hover:text-slate-700"
                  :aria-label="showPassword ? 'Hide password' : 'Show password'"
                  @click="showPassword = !showPassword"
                >
                  <EyeOff v-if="showPassword" :size="17" />
                  <Eye v-else :size="17" />
                </button>
              </div>
            </div>

            <button
              type="submit"
              :disabled="login.isPending.value"
              class="btn-primary w-full"
            >
              {{ login.isPending.value ? "Signing in…" : "Sign in" }}
              <ArrowRight v-if="!login.isPending.value" :size="16" />
            </button>
          </form>

          <p class="mt-5 text-center text-xs text-slate-400">
            Locked out? Ask an owner to run
            <code class="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">
              scripts/reset_admin_password.py
            </code>
          </p>
        </div>

        <p class="mt-6 text-center text-[11px] text-slate-400">
          Protected by Supabase Auth · Session refresh handled automatically
        </p>
      </div>
    </section>
  </div>
</template>
