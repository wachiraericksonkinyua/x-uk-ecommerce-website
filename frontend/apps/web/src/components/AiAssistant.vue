<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useMutation } from "@tanstack/vue-query";
import { Bot, GripVertical, Send, Sparkles, X } from "@lucide/vue";
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
      "Hi! I'm your GWV-xuk shopping assistant. Tell me your budget and what you need, and I'll recommend the right product.",
  },
]);

const user = computed(() => auth.user);

const panel = ref<HTMLElement | null>(null);
const position = reactive({ x: 0, y: 0 });
const hasPosition = ref(false);
let dragging = false;
let dragStartX = 0;
let dragStartY = 0;
let dragOriginX = 0;
let dragOriginY = 0;

function clampPosition(x: number, y: number) {
  const width = panel.value?.offsetWidth ?? 352;
  const height = panel.value?.offsetHeight ?? 448;
  return {
    x: Math.max(8, Math.min(window.innerWidth - width - 8, x)),
    y: Math.max(8, Math.min(window.innerHeight - height - 8, y)),
  };
}

function placeDefault() {
  const width = panel.value?.offsetWidth ?? 352;
  const height = panel.value?.offsetHeight ?? 448;
  const bottomOffset = window.innerWidth < 768 ? 132 : 92;
  const next = clampPosition(
    window.innerWidth - width - 20,
    window.innerHeight - height - bottomOffset
  );
  position.x = next.x;
  position.y = next.y;
  hasPosition.value = true;
}

async function toggleOpen() {
  open.value = !open.value;
  if (open.value) {
    await nextTick();
    if (!hasPosition.value) placeDefault();
    else onResize();
  }
}

function startDrag(event: PointerEvent) {
  if (event.button !== 0) return;
  dragging = true;
  dragStartX = event.clientX;
  dragStartY = event.clientY;
  dragOriginX = position.x;
  dragOriginY = position.y;
  window.addEventListener("pointermove", onDrag);
  window.addEventListener("pointerup", stopDrag, { once: true });
  window.addEventListener("pointercancel", stopDrag, { once: true });
  event.preventDefault();
}

function onDrag(event: PointerEvent) {
  if (!dragging) return;
  const next = clampPosition(
    dragOriginX + event.clientX - dragStartX,
    dragOriginY + event.clientY - dragStartY
  );
  position.x = next.x;
  position.y = next.y;
}

function stopDrag() {
  dragging = false;
  window.removeEventListener("pointermove", onDrag);
  window.removeEventListener("pointerup", stopDrag);
  window.removeEventListener("pointercancel", stopDrag);
}

function onResize() {
  if (!open.value || !hasPosition.value) return;
  const next = clampPosition(position.x, position.y);
  position.x = next.x;
  position.y = next.y;
}

onMounted(() => window.addEventListener("resize", onResize));
onBeforeUnmount(() => {
  stopDrag();
  window.removeEventListener("resize", onResize);
});

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
  <div v-if="!auth.token" class="fixed bottom-24 right-5 z-40 md:bottom-5">
    <RouterLink
      :to="{ path: '/login', query: { next: route.path } }"
      class="inline-flex items-center gap-2 rounded-full bg-brand-orange px-5 py-3 text-sm font-medium text-white shadow-lg transition hover:bg-orange-600"
    >
      <Sparkles :size="18" />
      Ask our AI
    </RouterLink>
  </div>

  <template v-else>
    <div
      v-if="open"
      ref="panel"
      class="fixed z-40 flex h-[28rem] w-[22rem] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_30px_70px_-30px_rgba(15,23,42,0.55)]"
      :style="{ left: `${position.x}px`, top: `${position.y}px` }"
    >
      <div
        class="flex cursor-move touch-none select-none items-center justify-between bg-gradient-to-r from-brand-orange-dark via-brand-orange to-[#FF8A5B] px-4 py-3 text-white"
        title="Drag to move"
        @pointerdown="startDrag"
      >
        <div class="flex items-center gap-2">
          <GripVertical :size="16" class="text-white/60" />
          <Bot :size="18" />
          <div>
            <p class="text-sm font-semibold">AI Shopping Assistant</p>
            <p class="text-[11px] text-white/75">
              {{ user?.email ?? "Here to help" }}
            </p>
          </div>
        </div>
        <button
          aria-label="Close chat"
          class="rounded-full p-1 transition hover:bg-white/15"
          @pointerdown.stop
          @click="open = false"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="
            message.role === 'user'
              ? 'ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-brand-orange px-3 py-2 text-sm text-white'
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
          placeholder="Ask about a product…"
          class="flex-1 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm outline-none focus:border-brand-orange"
          @keydown.enter="handleSend"
        />
        <button
          :disabled="send.isPending.value"
          aria-label="Send message"
          class="flex h-9 w-9 items-center justify-center rounded-full bg-brand-orange text-white transition hover:bg-orange-600 disabled:bg-slate-300"
          @click="handleSend"
        >
          <Send :size="16" />
        </button>
      </div>
    </div>

    <button
      class="fixed bottom-24 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-brand-orange text-white shadow-lg transition hover:bg-orange-600 md:bottom-5"
      aria-label="Toggle AI assistant"
      @click="toggleOpen"
    >
      <X v-if="open" :size="22" />
      <Sparkles v-else :size="22" />
    </button>
  </template>
</template>
