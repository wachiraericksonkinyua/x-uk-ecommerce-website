<script setup lang="ts">
import Spinner from "./Spinner.vue";

withDefaults(defineProps<{ label?: string }>(), { label: "Loading…" });
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-24 text-slate-500">
    <Spinner class="h-8 w-8" />
    <p class="text-sm">{{ label }}</p>
  </div>
</template>
