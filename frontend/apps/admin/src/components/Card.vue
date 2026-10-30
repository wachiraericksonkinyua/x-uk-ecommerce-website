<script setup lang="ts">
import { cn } from "../lib/utils";

defineProps<{ class?: string }>();
</script>

<template>
  <div :class="cn('rounded-2xl border border-slate-100 bg-white shadow-sm', $props.class)">
    <slot />
  </div>
</template>
