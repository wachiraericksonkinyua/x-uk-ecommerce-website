<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { KeyRound } from "@lucide/vue";
import { RouterLink, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import AuthShell from "../components/AuthShell.vue";
import SegmentedCodeInput from "../components/SegmentedCodeInput.vue";
import { authApi, errorMessage } from "../lib/api";

/**
 * Supabase puts the recovery tokens in the URL fragment
 * (`#access_token=...&refresh_token=...&type=recovery`) for implicit-flow
 * links, or in the query string (`?token_hash=...&type=recovery`) for newer
 * OTP-style templates.
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

const email = ref(params.get("email") ?? "");
const otpCode = ref("");
const password = ref("");
const confirmPassword = ref("");

const isCodeFlow = computed(() => !hasRecoveryToken);
const passwordsMatch = computed(
  () => password.value.length > 0 && password.value === confirmPassword.value
);
const codeReady = computed(() => otpCode.value.length === 6);
const canSubmit = computed(
  () =>
    passwordsMatch.value &&
    (hasRecoveryToken || (Boolean(email.value.trim()) && codeReady.value))
);

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
      email: isCodeFlow.value ? email.value.trim() : undefined,
      otp_code: isCodeFlow.value ? otpCode.value : undefined,
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
  if (isCodeFlow.value && !codeReady.value) {
    toast.error("Enter the 6-digit recovery code.");
    return;
  }
  submit.mutate();
}
</script>

<template>
  <AuthShell
    title="Choose a new password"
    subtitle="Your reset session is valid for a short time."
  >
    <div v-if="linkError" class="mb-4 rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700">
      {{ linkError }}
    </div>

    <form class="space-y-4" @submit.prevent="onSubmit">
      <template v-if="isCodeFlow">
        <div class="rounded-2xl border border-brand-blue-200 bg-brand-blue-50/70 p-4">
          <p class="text-sm font-semibold text-slate-800">
            Enter the code from your reset email
          </p>
          <p class="mt-1 text-xs text-slate-500">
            Use the one-time recovery code, then choose a new password.
          </p>
        </div>

        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Account email
          </label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            placeholder="you@example.com"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
          />
        </div>

        <SegmentedCodeInput
          v-model="otpCode"
          :length="6"
          label="Recovery code"
        />
      </template>

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
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
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
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
        <p v-if="confirmPassword && !passwordsMatch" class="mt-1.5 text-xs text-rose-600">
          Passwords do not match.
        </p>
      </div>

      <button
        type="submit"
        :disabled="submit.isPending.value || !canSubmit"
        class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand-orange px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:bg-slate-300"
      >
        <KeyRound :size="16" />
        {{ submit.isPending.value ? "Updating…" : "Update password" }}
      </button>
    </form>

    <template #footer>
      <div class="flex flex-col items-center gap-2">
        <RouterLink to="/forgot-password" class="font-semibold text-brand-orange hover:underline">
          Request a new reset link
        </RouterLink>
        <RouterLink to="/login" class="text-slate-500 hover:text-brand-orange">
          Back to sign in
        </RouterLink>
      </div>
    </template>
  </AuthShell>
</template>
