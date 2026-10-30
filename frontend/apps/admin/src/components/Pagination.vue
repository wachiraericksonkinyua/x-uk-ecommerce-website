<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  page: number;
  pageSize: number;
  total: number;
}>();

const emit = defineEmits<{ page: [page: number] }>();

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
</script>

<template>
  <div
    class="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500"
  >
    <span> Page {{ page }} of {{ pages }} &bull; {{ total }} records </span>
    <div class="flex gap-2">
      <button
        :disabled="page <= 1"
        class="rounded-lg border border-slate-200 px-3 py-1.5 font-medium transition hover:bg-slate-50 disabled:opacity-40"
        @click="emit('page', page - 1)"
      >
        Prev
      </button>
      <button
        :disabled="page >= pages"
        class="rounded-lg border border-slate-200 px-3 py-1.5 font-medium transition hover:bg-slate-50 disabled:opacity-40"
        @click="emit('page', page + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>
