<script setup lang="ts">
import { RouterLink } from "vue-router";

withDefaults(
  defineProps<{
    title: string;
    subtitle?: string;
  }>(),
  { subtitle: undefined }
);
</script>

<template>
  <div class="flex min-h-screen flex-col bg-slate-50">
    <header class="border-b border-slate-100 bg-white">
      <div class="mx-auto flex max-w-7xl items-center px-4 py-3 sm:px-6">
        <RouterLink
          to="/"
          class="flex items-center gap-2"
          aria-label="Gadgets With Vin"
        >
          <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto" />
        </RouterLink>
      </div>
    </header>

    <main class="flex flex-1 items-center justify-center px-4 py-10">
      <div class="w-full max-w-md rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
        <h1 class="text-xl font-bold text-slate-900">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1 text-sm text-slate-500">{{ subtitle }}</p>
        <div class="mt-6">
          <slot />
        </div>
        <div v-if="$slots.footer" class="mt-6 text-center text-sm">
          <slot name="footer" />
        </div>
      </div>
    </main>
  </div>
</template>
