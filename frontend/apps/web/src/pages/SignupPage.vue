<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { UserPlus } from "@lucide/vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import AuthShell from "../components/AuthShell.vue";
import { authApi, errorMessage } from "../lib/api";
import type { AuthUser, Session } from "../lib/types";
import { useAuthStore } from "../store/auth";

interface SignupResponse {
  success: boolean;
  data?: { session?: Session | null; user?: AuthUser };
  session?: Session | null;
  user?: AuthUser;
}

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const email = ref("");
const password = ref("");
const confirm = ref("");

const next = computed(() =>
  typeof route.query.next === "string" ? route.query.next : "/"
);

const signup = useMutation({
  mutationFn: () =>
    authApi.post<SignupResponse>("/auth/signup", {
      email: email.value,
      password: password.value,
    }),
  onSuccess: (res) => {
    // With email confirmation disabled Supabase returns a session right away.
    const session = res?.data?.session ?? res?.session ?? null;
    const user = res?.data?.user ?? res?.user ?? null;
    if (session?.access_token) {
      auth.setSession(session, user);
      toast.success("Welcome to GWV-xuk!");
      router.push(next.value);
      return;
    }
    toast.success(
      "Account created! Check your email to confirm it, then sign in."
    );
    router.push("/login");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function submit() {
  if (password.value.length < 6) {
    toast.error("Password must be at least 6 characters");
    return;
  }
  if (password.value !== confirm.value) {
    toast.error("Passwords do not match");
    return;
  }
  signup.mutate();
}
</script>

<template>
  <AuthShell
    title="Create your account"
    subtitle="Join GWV-xuk to shop, track and save favourites."
  >
    <form class="space-y-4" @submit.prevent="submit">
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Email
        </label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="you@example.com"
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
          placeholder="At least 6 characters"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Confirm password
        </label>
        <input
          v-model="confirm"
          type="password"
          required
          placeholder="Re-enter password"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <button
        type="submit"
        :disabled="signup.isPending.value"
        class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-slate-300"
      >
        <UserPlus :size="16" />
        {{ signup.isPending.value ? "Creating account…" : "Create account" }}
      </button>
    </form>

    <template #footer>
      Already have an account?
      <RouterLink to="/login" class="font-semibold text-blue-700 hover:underline">
        Sign in
      </RouterLink>
    </template>
  </AuthShell>
</template>
