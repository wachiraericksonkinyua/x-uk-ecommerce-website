<script setup lang="ts">
import { cn } from "../lib/utils";

defineProps<{ class?: string }>();
</script>

<template>
  <div :class="cn('rounded-2xl border border-slate-200/80 bg-white shadow-panel', $props.class)">
    <slot />
  </div>
</template>
