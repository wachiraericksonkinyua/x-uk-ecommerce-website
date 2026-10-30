<script setup lang="ts">
import { cn } from "../lib/utils";

defineProps<{ class?: string }>();
</script>

<template>
  <td :class="cn('px-4 py-3 text-sm text-slate-700', $props.class)">
    <slot />
  </td>
</template>
