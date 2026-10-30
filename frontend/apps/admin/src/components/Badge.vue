<script setup lang="ts">
import { cn } from "../lib/utils";

defineProps<{ class?: string }>();
</script>

<template>
  <span
    :class="
      cn(
        'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold',
        $props.class
      )
    "
  >
    <slot />
  </span>
</template>
