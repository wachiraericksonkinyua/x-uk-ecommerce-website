<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center"
  >
    <slot name="icon" />
    <h3 class="text-lg font-semibold text-slate-800">{{ title }}</h3>
    <p v-if="description" class="max-w-md text-sm text-slate-500">
      {{ description }}
    </p>
    <slot name="action" />
  </div>
</template>
