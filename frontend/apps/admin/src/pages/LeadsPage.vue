<script setup lang="ts">
import { ref } from "vue";
import { MessageCircle } from "@lucide/vue";

import Card from "../components/Card.vue";
import FunnelBar from "../components/FunnelBar.vue";
import LeadConversation from "../components/LeadConversation.vue";
import LeadList from "../components/LeadList.vue";
import type { Lead } from "../lib/types";

const selected = ref<Lead | null>(null);
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">WhatsApp AI Triage CRM</h1>
      <p class="text-sm text-slate-500">
        Review AI-scored leads, read transcripts and take over conversations.
      </p>
    </div>

    <FunnelBar />

    <div class="mt-6 grid gap-4 lg:grid-cols-[22rem_1fr]">
      <LeadList :selected-id="selected?.id" @select="selected = $event" />
      <LeadConversation
        v-if="selected"
        :lead="selected"
        @update="selected = $event"
      />
      <Card v-else class="flex min-h-[30rem] items-center justify-center">
        <div class="text-center">
          <MessageCircle class="mx-auto text-slate-300" :size="40" />
          <p class="mt-3 text-sm font-medium text-slate-600">
            Select a lead to view the conversation
          </p>
          <p class="text-xs text-slate-400">
            AI scores, budget and interest are shown in the list.
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>
