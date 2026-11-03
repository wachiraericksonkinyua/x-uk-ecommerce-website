<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <div class="mx-auto flex max-w-lg flex-col items-center px-4 py-24 text-center">
    <p class="text-5xl font-black text-brand-orange">404</p>
    <h1 class="mt-4 text-xl font-bold text-slate-900">Page not found</h1>
    <p class="mt-2 text-sm text-slate-500">
      The page you're looking for doesn't exist or has moved.
    </p>
    <RouterLink
      to="/"
      class="mt-6 rounded-full bg-brand-orange px-6 py-2.5 text-sm font-semibold text-white hover:bg-orange-600"
    >
      Back home
    </RouterLink>
  </div>
</template>
