<script setup lang="ts">
import { computed } from "vue";
import { RefreshCw } from "@lucide/vue";

const props = defineProps<{
  distance: number;
  refreshing: boolean;
  ready: boolean;
}>();

const offset = computed(() => Math.min(80, props.distance));
const label = computed(() => {
  if (props.refreshing) return "Refreshing";
  if (props.ready) return "Release to refresh";
  return "Pull to refresh";
});
</script>

<template>
  <div
    v-if="distance > 0 || refreshing"
    class="pointer-events-none fixed left-1/2 top-20 z-50 flex items-center gap-2 rounded-full border border-brand-blue-200 bg-white/95 px-4 py-2 text-xs font-semibold text-slate-700 shadow-lg backdrop-blur"
    :style="{ transform: `translate(-50%, ${offset}px)` }"
  >
    <RefreshCw
      :size="15"
      :class="refreshing ? 'animate-spin text-brand-orange' : 'text-brand-blue-700'"
      :style="{ transform: ready && !refreshing ? 'rotate(180deg)' : undefined }"
    />
    {{ label }}
  </div>
</template>
