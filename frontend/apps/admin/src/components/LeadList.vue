<script setup lang="ts">
import { computed, ref } from "vue";
import { Search } from "@lucide/vue";

import Badge from "./Badge.vue";
import Card from "./Card.vue";
import EmptyState from "./EmptyState.vue";
import Pagination from "./Pagination.vue";
import Spinner from "./Spinner.vue";
import { useLeads } from "../hooks/queries";
import type { Lead } from "../lib/types";
import { LEAD_STATUSES, cn, formatDate, formatKES, statusColor } from "../lib/utils";

defineProps<{ selectedId?: string }>();
const emit = defineEmits<{ select: [lead: Lead] }>();

const page = ref(1);
const status = ref("");
const searchInput = ref("");
const search = ref("");
const pageSize = 20;

const { data, isLoading } = useLeads(() => ({
  page: page.value,
  pageSize,
  status: status.value,
  search: search.value,
}));

const leads = computed(() => data.value?.data ?? []);

function submitSearch() {
  page.value = 1;
  search.value = searchInput.value.trim();
}

function selectStatus(value: string) {
  status.value = value;
  page.value = 1;
}
</script>

<template>
  <Card class="flex h-full min-h-[30rem] flex-col overflow-hidden">
    <div class="space-y-3 border-b border-slate-100 p-4">
      <form
        class="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2"
        @submit.prevent="submitSearch"
      >
        <Search :size="15" class="text-slate-400" />
        <input
          v-model="searchInput"
          placeholder="Search name or phone…"
          class="w-full bg-transparent text-sm outline-none"
        />
      </form>
      <div class="flex flex-wrap gap-1.5">
        <button
          :class="
            cn(
              'rounded-full px-3 py-1 text-xs font-medium capitalize',
              status === ''
                ? 'bg-blue-700 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            )
          "
          @click="selectStatus('')"
        >
          all
        </button>
        <button
          v-for="value in LEAD_STATUSES"
          :key="value"
          :class="
            cn(
              'rounded-full px-3 py-1 text-xs font-medium capitalize',
              status === value
                ? 'bg-blue-700 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            )
          "
          @click="selectStatus(value)"
        >
          {{ value }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-if="isLoading" class="flex justify-center py-12">
        <Spinner class="h-7 w-7" />
      </div>
      <div v-else-if="leads.length === 0" class="p-6">
        <EmptyState title="No leads found" />
      </div>
      <template v-else>
        <button
          v-for="lead in leads"
          :key="lead.id"
          :class="
            cn(
              'flex w-full items-start gap-3 border-b border-slate-50 px-4 py-3 text-left transition hover:bg-slate-50',
              selectedId === lead.id && 'bg-blue-50'
            )
          "
          @click="emit('select', lead)"
        >
          <span
            :class="
              cn(
                'mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold',
                statusColor(lead.status)
              )
            "
          >
            {{ lead.score ?? 0 }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-2">
              <p class="truncate text-sm font-semibold text-slate-800">
                {{ lead.name || lead.phone }}
              </p>
              <span class="shrink-0 text-[11px] text-slate-400">
                {{ formatDate(lead.last_message_at) }}
              </span>
            </div>
            <p class="truncate text-xs text-slate-500">
              {{ lead.interest || "No interest noted" }} &bull;
              {{ lead.location || "Unknown" }}
            </p>
            <div class="mt-1 flex items-center gap-2">
              <Badge :class="cn(statusColor(lead.status), 'capitalize')">
                {{ lead.status }}
              </Badge>
              <span v-if="lead.budget != null" class="text-[11px] text-slate-400">
                {{ formatKES(lead.budget) }}
              </span>
            </div>
          </div>
        </button>
      </template>
    </div>

    <Pagination
      v-if="data && data.total > 0"
      :page="page"
      :page-size="pageSize"
      :total="data.total"
      @page="page = $event"
    />
  </Card>
</template>
