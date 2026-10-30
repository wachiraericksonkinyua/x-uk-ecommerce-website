<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { Bot, Send, Sparkles, X } from "@lucide/vue";
import { RouterLink, useRoute } from "vue-router";

import { api, errorMessage } from "../lib/api";
import { useAuthStore } from "../store/auth";
import Spinner from "./Spinner.vue";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  choices: { message: { content: string } }[];
}

const auth = useAuthStore();
const route = useRoute();
const open = ref(false);
const input = ref("");
const messages = ref<ChatMessage[]>([
  {
    role: "assistant",
    content:
      "Hi! I'm your GWV-xuk shopping assistant. Tell me your budget and what you need, and I'll recommend a phone.",
  },
]);

const user = computed(() => auth.user);

const send = useMutation({
  mutationFn: async (history: ChatMessage[]) => {
    const res = await api.post<ChatResponse>("/ai/chat", { messages: history });
    return res.choices?.[0]?.message?.content ?? "Sorry, I couldn't respond.";
  },
  onSuccess: (reply) => {
    messages.value = [...messages.value, { role: "assistant", content: reply }];
  },
  onError: (error) => {
    messages.value = [
      ...messages.value,
      { role: "assistant", content: errorMessage(error) },
    ];
  },
});

function handleSend() {
  const text = input.value.trim();
  if (!text || send.isPending.value) return;
  const next: ChatMessage[] = [
    ...messages.value,
    { role: "user", content: text },
  ];
  messages.value = next;
  input.value = "";
  send.mutate(next);
}
</script>

<template>
  <div v-if="!auth.token" class="fixed bottom-5 right-5 z-40">
    <RouterLink
      :to="{ path: '/login', query: { next: route.path } }"
      class="inline-flex items-center gap-2 rounded-full bg-blue-700 px-5 py-3 text-sm font-medium text-white shadow-lg transition hover:bg-blue-800"
    >
      <Sparkles :size="18" />
      Ask our AI
    </RouterLink>
  </div>

  <template v-else>
    <div
      v-if="open"
      class="fixed bottom-24 right-5 z-40 flex h-[28rem] w-[22rem] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
    >
      <div
        class="flex items-center justify-between bg-gradient-to-r from-[#061A40] via-[#0B3578] to-[#1565C0] px-4 py-3 text-white"
      >
        <div class="flex items-center gap-2">
          <Bot :size="18" />
          <div>
            <p class="text-sm font-semibold">AI Shopping Assistant</p>
            <p class="text-[11px] text-blue-100">
              {{ user?.email ?? "Here to help" }}
            </p>
          </div>
        </div>
        <button aria-label="Close chat" @click="open = false">
          <X :size="18" />
        </button>
      </div>

      <div class="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="
            message.role === 'user'
              ? 'ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-blue-700 px-3 py-2 text-sm text-white'
              : 'mr-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-sm border border-slate-100 bg-white px-3 py-2 text-sm text-slate-700'
          "
        >
          {{ message.content }}
        </div>
        <div
          v-if="send.isPending.value"
          class="mr-auto flex items-center gap-2 rounded-2xl bg-white px-3 py-2 text-sm text-slate-500"
        >
          <Spinner class="h-4 w-4" /> Thinking…
        </div>
      </div>

      <div class="flex items-center gap-2 border-t border-slate-100 p-3">
        <input
          v-model="input"
          placeholder="Ask about a phone…"
          class="flex-1 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm outline-none focus:border-blue-500"
          @keydown.enter="handleSend"
        />
        <button
          :disabled="send.isPending.value"
          aria-label="Send message"
          class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-700 text-white transition hover:bg-blue-800 disabled:bg-slate-300"
          @click="handleSend"
        >
          <Send :size="16" />
        </button>
      </div>
    </div>

    <button
      class="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-blue-700 text-white shadow-lg transition hover:bg-blue-800"
      aria-label="Toggle AI assistant"
      @click="open = !open"
    >
      <X v-if="open" :size="22" />
      <Sparkles v-else :size="22" />
    </button>
  </template>
</template>
