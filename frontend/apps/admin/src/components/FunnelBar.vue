<script setup lang="ts">
import Card from "./Card.vue";
import { useLeadStats } from "../hooks/queries";
import { LEAD_STATUSES } from "../lib/utils";

const { data: stats } = useLeadStats();
</script>

<template>
  <div v-if="stats" class="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
    <Card v-for="status in LEAD_STATUSES" :key="status" class="p-4">
      <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {{ status }}
      </p>
      <p class="mt-1 text-2xl font-bold text-slate-900">
        {{ stats.by_status?.[status] ?? 0 }}
      </p>
    </Card>
  </div>
</template>
