<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { CheckCheck, Send, UserCheck } from "@lucide/vue";
import { toast } from "vue-sonner";

import Card from "./Card.vue";
import Spinner from "./Spinner.vue";
import { api, errorMessage } from "../lib/api";
import { useLeadMessages } from "../hooks/queries";
import type { Lead } from "../lib/types";
import { LEAD_STATUSES, cn, formatDate, statusColor } from "../lib/utils";

const props = defineProps<{ lead: Lead }>();
const emit = defineEmits<{ update: [lead: Lead] }>();

const queryClient = useQueryClient();
const scrollRef = ref<HTMLDivElement | null>(null);
const { data: messages, isLoading } = useLeadMessages(() => props.lead.id);
const messageList = computed(() => messages.value ?? []);

const reply = ref("");
const status = ref(props.lead.status);
const score = ref(props.lead.score);
const assignee = ref(props.lead.assigned_to ?? "");

watch(
  () => props.lead,
  (lead) => {
    status.value = lead.status;
    score.value = lead.score;
    assignee.value = lead.assigned_to ?? "";
  },
  { immediate: true }
);

watch(
  () => messageList.value.length,
  async () => {
    await nextTick();
    scrollRef.value?.scrollTo({ top: scrollRef.value.scrollHeight });
  }
);

const saveLead = useMutation({
  mutationFn: (payload: Partial<Lead>) =>
    api.patch(`/admin/leads/${props.lead.id}`, payload),
  onSuccess: (res) => {
    queryClient.invalidateQueries({ queryKey: ["admin-leads"] });
    queryClient.invalidateQueries({ queryKey: ["admin-lead-stats"] });
    toast.success("Lead updated");
    const updated = (res as { data?: Lead }).data;
    if (updated) emit("update", updated);
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const assign = useMutation({
  mutationFn: () =>
    api.post(
      `/admin/leads/${props.lead.id}/assign?assigned_to=${encodeURIComponent(
        assignee.value.trim()
      )}`
    ),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-leads"] });
    toast.success("Assignment updated");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const sendReply = useMutation({
  mutationFn: () =>
    api.post(`/admin/leads/${props.lead.id}/reply`, {
      message: reply.value.trim(),
    }),
  onSuccess: () => {
    reply.value = "";
    queryClient.invalidateQueries({
      queryKey: ["admin-lead-messages", props.lead.id],
    });
    queryClient.invalidateQueries({ queryKey: ["admin-leads"] });
    toast.success("Reply sent");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function onStatusChange(event: Event) {
  const next = (event.target as HTMLSelectElement).value;
  status.value = next;
  saveLead.mutate({ status: next });
}

function onScoreBlur() {
  saveLead.mutate({ score: score.value });
}

function send() {
  if (reply.value.trim()) sendReply.mutate();
}
</script>

<template>
  <Card class="flex h-full min-h-[30rem] flex-col overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-4">
      <div>
        <p class="font-semibold text-slate-900">{{ lead.name || "Unknown lead" }}</p>
        <p class="text-xs text-slate-500">
          {{ lead.phone }} &bull; {{ lead.location || "Unknown location" }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <select
          :value="status"
          class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs capitalize outline-none focus:border-blue-500"
          @change="onStatusChange"
        >
          <option v-for="value in LEAD_STATUSES" :key="value" :value="value">
            {{ value }}
          </option>
        </select>
        <div class="flex items-center gap-1 rounded-full border border-slate-200 px-2 py-1">
          <span class="text-[11px] text-slate-400">Score</span>
          <input
            v-model.number="score"
            type="number"
            min="0"
            max="100"
            class="w-14 bg-transparent text-xs outline-none"
            @blur="onScoreBlur"
          />
        </div>
      </div>
    </div>

    <div ref="scrollRef" class="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
      <div v-if="isLoading" class="flex justify-center py-10">
        <Spinner class="h-7 w-7" />
      </div>
      <p
        v-else-if="messageList.length === 0"
        class="py-10 text-center text-sm text-slate-400"
      >
        No messages in this conversation yet.
      </p>
      <template v-else>
        <div
          v-for="message in messageList"
          :key="message.id"
          :class="
            cn(
              'max-w-[80%] rounded-2xl px-3 py-2 text-sm',
              message.direction === 'outbound'
                ? 'ml-auto rounded-br-sm bg-emerald-600 text-white'
                : 'mr-auto rounded-bl-sm border border-slate-100 bg-white text-slate-700'
            )
          "
        >
          <p class="whitespace-pre-wrap">{{ message.body }}</p>
          <p
            :class="
              cn(
                'mt-1 text-[10px]',
                message.direction === 'outbound'
                  ? 'text-emerald-100'
                  : 'text-slate-400'
              )
            "
          >
            {{ formatDate(message.created_at) }}
          </p>
        </div>
      </template>
    </div>

    <div class="border-t border-slate-100 p-3">
      <div class="mb-2 flex items-center gap-2">
        <div
          class="flex flex-1 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5"
        >
          <UserCheck :size="14" class="text-slate-400" />
          <input
            v-model="assignee"
            placeholder="Assign staff user id…"
            class="w-full bg-transparent text-xs outline-none"
          />
        </div>
        <button
          :disabled="assign.isPending.value"
          class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          @click="assign.mutate()"
        >
          <CheckCheck :size="14" />
        </button>
      </div>
      <div class="flex items-center gap-2">
        <input
          v-model="reply"
          placeholder="Type a WhatsApp reply…"
          class="flex-1 rounded-full border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-500"
          @keydown.enter="send"
        />
        <button
          :disabled="sendReply.isPending.value || !reply.trim()"
          class="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-white transition hover:bg-emerald-700 disabled:bg-slate-300"
          aria-label="Send reply"
          @click="send"
        >
          <Send :size="16" />
        </button>
      </div>
    </div>
  </Card>
</template>
