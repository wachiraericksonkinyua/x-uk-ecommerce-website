<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { KeyRound } from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import AuthShell from "../components/AuthShell.vue";
import { authApi, errorMessage } from "../lib/api";

/**
 * Supabase puts the recovery tokens in the URL fragment
 * (`#access_token=...&refresh_token=...&type=recovery`) for implicit-flow
 * links, or in the query string (`?token_hash=...&type=recovery`) for newer
 * OTP-style templates. Read both so either email template works.
 */
function readParams(): URLSearchParams {
  const params = new URLSearchParams(window.location.search);
  const hash = window.location.hash.replace(/^#/, "");
  if (hash) {
    for (const [key, value] of new URLSearchParams(hash)) {
      if (!params.has(key)) params.set(key, value);
    }
  }
  return params;
}

const router = useRouter();
const params = readParams();

const accessToken = params.get("access_token") ?? "";
const refreshToken = params.get("refresh_token") ?? "";
const tokenHash = params.get("token_hash") ?? "";
const linkError = params.get("error_description") ?? "";
const hasRecoveryToken = Boolean(accessToken || tokenHash);

const password = ref("");
const confirmPassword = ref("");

const passwordsMatch = computed(
  () => password.value.length > 0 && password.value === confirmPassword.value
);

// Strip the tokens from the address bar so they are not left in history or
// accidentally shared/copied after the reset.
if (window.location.hash || params.has("token_hash")) {
  window.history.replaceState({}, "", window.location.pathname);
}

const submit = useMutation({
  mutationFn: () =>
    authApi.post("/auth/reset-password", {
      new_password: password.value,
      access_token: accessToken || undefined,
      refresh_token: refreshToken || undefined,
      token_hash: tokenHash || undefined,
    }),
  onSuccess: () => {
    toast.success("Password updated. Please sign in.");
    router.push("/login");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function onSubmit() {
  if (!passwordsMatch.value) {
    toast.error("Passwords do not match.");
    return;
  }
  submit.mutate();
}
</script>

<template>
  <AuthShell
    title="Choose a new password"
    subtitle="Your reset link is valid for a short time."
  >
    <div
      v-if="linkError || !hasRecoveryToken"
      class="space-y-4"
    >
      <p class="rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700">
        {{ linkError || "This reset link is invalid or has expired." }}
      </p>
      <RouterLink
        to="/forgot-password"
        class="inline-flex w-full items-center justify-center rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
      >
        Request a new link
      </RouterLink>
    </div>

    <form v-else class="space-y-4" @submit.prevent="onSubmit">
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          New password
        </label>
        <input
          v-model="password"
          type="password"
          required
          minlength="8"
          maxlength="72"
          autocomplete="new-password"
          placeholder="At least 8 characters"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Confirm password
        </label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          minlength="8"
          maxlength="72"
          autocomplete="new-password"
          placeholder="Repeat your new password"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
        />
        <p
          v-if="confirmPassword && !passwordsMatch"
          class="mt-1.5 text-xs text-rose-600"
        >
          Passwords do not match.
        </p>
      </div>
      <button
        type="submit"
        :disabled="submit.isPending.value || !passwordsMatch"
        class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-slate-300"
      >
        <KeyRound :size="16" />
        {{ submit.isPending.value ? "Updating…" : "Update password" }}
      </button>
    </form>

    <template #footer>
      <RouterLink to="/login" class="font-semibold text-blue-700 hover:underline">
        Back to sign in
      </RouterLink>
    </template>
  </AuthShell>
</template>
