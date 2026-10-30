<script setup lang="ts">
import { computed } from "vue";
import { Star } from "@lucide/vue";

const props = withDefaults(
  defineProps<{ value?: number; size?: number }>(),
  { value: 5, size: 14 }
);

const rounded = computed(() => Math.round(props.value));
</script>

<template>
  <span class="inline-flex items-center gap-0.5">
    <Star
      v-for="i in 5"
      :key="i"
      :size="size"
      :class="
        i <= rounded
          ? 'fill-amber-400 text-amber-400'
          : 'fill-slate-200 text-slate-200'
      "
    />
  </span>
</template>
