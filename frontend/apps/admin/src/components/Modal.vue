<script setup lang="ts">
import { computed } from "vue";
import { X } from "@lucide/vue";
import { cn } from "../lib/utils";

const props = withDefaults(
  defineProps<{ open: boolean; title: string; size?: "md" | "lg" | "xl" }>(),
  { size: "md" }
);
const emit = defineEmits<{ close: [] }>();

const width = computed(() =>
  props.size === "xl" ? "max-w-3xl" : props.size === "lg" ? "max-w-2xl" : "max-w-lg"
);
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/40 p-4 sm:p-8"
  >
    <div :class="cn('w-full rounded-2xl bg-white shadow-xl', width)">
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <h2 class="text-base font-bold text-slate-900">{{ title }}</h2>
        <button
          class="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-label="Close"
          @click="emit('close')"
        >
          <X :size="18" />
        </button>
      </div>
      <div class="px-6 py-5">
        <slot />
      </div>
    </div>
  </div>
</template>
