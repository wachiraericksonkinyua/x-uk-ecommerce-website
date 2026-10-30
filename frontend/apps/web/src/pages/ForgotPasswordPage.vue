<script setup lang="ts">
import { ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { Mail } from "@lucide/vue";
import { RouterLink } from "vue-router";
import { toast } from "vue-sonner";

import AuthShell from "../components/AuthShell.vue";
import { authApi, errorMessage } from "../lib/api";

const email = ref("");

const submit = useMutation({
  mutationFn: () => authApi.post("/auth/forgot-password", { email: email.value }),
  onSuccess: () => {
    toast.success("If that email exists, a reset link has been sent.");
    email.value = "";
  },
  onError: (error) => toast.error(errorMessage(error)),
});
</script>

<template>
  <AuthShell
    title="Reset your password"
    subtitle="We'll email you a link to choose a new password."
  >
    <form class="space-y-4" @submit.prevent="submit.mutate()">
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
      <button
        type="submit"
        :disabled="submit.isPending.value"
        class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-slate-300"
      >
        <Mail :size="16" />
        {{ submit.isPending.value ? "Sending…" : "Send reset link" }}
      </button>
    </form>

    <template #footer>
      <RouterLink to="/login" class="font-semibold text-blue-700 hover:underline">
        Back to sign in
      </RouterLink>
    </template>
  </AuthShell>
</template>
