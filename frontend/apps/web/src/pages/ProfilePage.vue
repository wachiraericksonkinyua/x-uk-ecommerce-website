<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Camera, Save, User } from "@lucide/vue";
import { toast } from "vue-sonner";

import PageLoader from "../components/PageLoader.vue";
import { api, errorMessage } from "../lib/api";
import { useMyProfile } from "../hooks/queries";
import type { Profile } from "../lib/types";

const queryClient = useQueryClient();
const fileRef = ref<HTMLInputElement | null>(null);
const { data: profile, isLoading } = useMyProfile(true);

const form = reactive({
  full_name: "",
  phone_number: "",
  address: "",
  date_of_birth: "",
  avatar_url: "",
});

watch(profile, (value) => {
  if (!value) return;
  form.full_name = value.full_name ?? "";
  form.phone_number = value.phone_number ?? "";
  form.address = value.address ?? "";
  form.date_of_birth = value.date_of_birth ?? "";
  form.avatar_url = value.avatar_url ?? "";
});

const save = useMutation({
  mutationFn: (payload: Partial<Profile>) =>
    api.patch("/profiles/me", {
      ...payload,
      date_of_birth: payload.date_of_birth || null,
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["profile"] });
    toast.success("Profile updated");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const uploadAvatar = useMutation({
  mutationFn: async (file: File) => {
    const body = new FormData();
    body.append("file", file);
    const res = await api.post<{ success: boolean; url: string }>(
      "/upload/profile-picture",
      body
    );
    return res.url;
  },
  onSuccess: (url) => {
    form.avatar_url = url;
    save.mutate({ avatar_url: url });
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function handleFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) uploadAvatar.mutate(file);
}

function submit() {
  save.mutate({ ...form });
}

function onDateInput(event: Event) {
  form.date_of_birth = (event.target as HTMLInputElement).value;
}
</script>

<template>
  <PageLoader v-if="isLoading" label="Loading profile…" />

  <div v-else class="mx-auto max-w-3xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-slate-900">My Profile</h1>

    <div class="mt-6 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div class="flex items-center gap-5">
        <div class="relative">
          <div
            class="flex h-20 w-20 items-center justify-center overflow-hidden rounded-full bg-slate-100"
          >
            <img
              v-if="form.avatar_url"
              :src="form.avatar_url"
              alt="Avatar"
              class="h-full w-full object-cover"
            />
            <User v-else class="text-slate-400" :size="30" />
          </div>
          <button
            class="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full bg-blue-700 text-white shadow"
            aria-label="Upload avatar"
            @click="fileRef?.click()"
          >
            <Camera :size="15" />
          </button>
          <input
            ref="fileRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFile"
          />
        </div>
        <div>
          <p class="font-semibold text-slate-800">
            {{ form.full_name || "Your name" }}
          </p>
          <p class="text-sm text-slate-500">
            {{
              uploadAvatar.isPending.value
                ? "Uploading…"
                : "Update your photo and details"
            }}
          </p>
        </div>
      </div>

      <form class="mt-6 grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Full name
          </label>
          <input
            v-model="form.full_name"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Phone number
          </label>
          <input
            v-model="form.phone_number"
            placeholder="2547XXXXXXXX"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <div class="sm:col-span-2">
          <label class="text-xs font-semibold uppercase text-slate-500">
            Address
          </label>
          <input
            v-model="form.address"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label class="text-xs font-semibold uppercase text-slate-500">
            Date of birth
          </label>
          <input
            type="date"
            :value="form.date_of_birth?.slice(0, 10) ?? ''"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
            @input="onDateInput"
          />
        </div>
        <div class="flex items-end">
          <button
            type="submit"
            :disabled="save.isPending.value"
            class="inline-flex w-full items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:bg-slate-300"
          >
            <Save :size="16" />
            {{ save.isPending.value ? "Saving…" : "Save changes" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
