<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { LockKeyhole } from "@lucide/vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    length?: number;
    alphanumeric?: boolean;
    label?: string;
    disabled?: boolean;
  }>(),
  {
    length: 6,
    alphanumeric: false,
    label: "Secure code",
    disabled: false,
  }
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  complete: [value: string];
}>();

const inputs = ref<HTMLInputElement[]>([]);
const chars = ref<string[]>(Array.from({ length: props.length }, () => ""));
const activeIndex = ref(0);

const allowedPattern = computed(() =>
  props.alphanumeric ? /[^A-Za-z0-9]/g : /[^0-9]/g
);

const value = computed(() => chars.value.join(""));

function emitValue() {
  const next = value.value;
  emit("update:modelValue", next);
  if (next.length === props.length && !next.includes("")) {
    emit("complete", next);
  }
}

function syncFromModel(raw: string) {
  const cleaned = (raw || "")
    .replace(allowedPattern.value, "")
    .slice(0, props.length)
    .toUpperCase()
    .split("");
  chars.value = Array.from(
    { length: props.length },
    (_, index) => cleaned[index] ?? ""
  );
}

watch(
  () => props.modelValue,
  (next) => {
    if (next !== value.value) syncFromModel(next);
  },
  { immediate: true }
);

watch(
  () => props.length,
  () => syncFromModel(props.modelValue)
);

function setInputRef(element: unknown, index: number) {
  if (element instanceof HTMLInputElement) {
    inputs.value[index] = element;
  }
}

function focusCell(index: number) {
  const target = Math.max(0, Math.min(props.length - 1, index));
  activeIndex.value = target;
  nextTick(() => inputs.value[target]?.focus());
}

function writeChars(startIndex: number, raw: string) {
  const cleaned = raw.replace(allowedPattern.value, "").toUpperCase();
  if (!cleaned) return;

  const next = [...chars.value];
  let cursor = startIndex;
  for (const char of cleaned) {
    if (cursor >= props.length) break;
    next[cursor] = char;
    cursor += 1;
  }
  chars.value = next;
  emitValue();
  focusCell(cursor >= props.length ? props.length - 1 : cursor);
}

function onInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement;
  writeChars(index, input.value);
  input.value = chars.value[index] ?? "";
}

function onPaste(index: number, event: ClipboardEvent) {
  event.preventDefault();
  const text = event.clipboardData?.getData("text") ?? "";
  writeChars(index, text);
}

function onKeydown(index: number, event: KeyboardEvent) {
  if (event.key === "Backspace") {
    event.preventDefault();
    const next = [...chars.value];
    if (next[index]) {
      next[index] = "";
      chars.value = next;
      emitValue();
      focusCell(index);
    } else {
      focusCell(index - 1);
      if (index > 0) {
        next[index - 1] = "";
        chars.value = next;
        emitValue();
      }
    }
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    focusCell(index - 1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    focusCell(index + 1);
  } else if (event.key === "Home") {
    event.preventDefault();
    focusCell(0);
  } else if (event.key === "End") {
    event.preventDefault();
    focusCell(props.length - 1);
  }
}

function onFocus(index: number) {
  activeIndex.value = index;
  const input = inputs.value[index];
  if (input) input.select();
}

onMounted(() => {
  if (props.modelValue) syncFromModel(props.modelValue);
});
</script>

<template>
  <div class="flex w-full flex-col items-center">
    <div class="relative mb-3 flex h-12 w-12 items-center justify-center">
      <span
        class="absolute inset-0 animate-ping rounded-2xl bg-brand-blue-200/60"
      />
      <span
        class="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-brand-blue-200 bg-white text-brand-orange shadow-[0_12px_24px_-14px_rgba(255,79,0,0.55)]"
      >
        <LockKeyhole :size="21" />
      </span>
    </div>

    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
      {{ label }}
    </p>

    <div
      class="mt-3 grid w-full max-w-md gap-1.5 sm:gap-2"
      :style="{ gridTemplateColumns: `repeat(${length}, minmax(0, 1fr))` }"
    >
      <label
        v-for="(char, index) in chars"
        :key="index"
        :class="[
          'liquid-cell relative flex aspect-square min-w-0 items-center justify-center overflow-hidden rounded-xl border bg-white transition-all duration-300 sm:rounded-2xl',
          char
            ? 'liquid-cell--filled border-brand-blue-300'
            : 'border-slate-200',
          activeIndex === index
            ? 'scale-[1.03] border-brand-orange shadow-[0_0_0_3px_rgba(255,79,0,0.12)]'
            : '',
        ]"
      >
        <span class="liquid-fill" aria-hidden="true" />
        <input
          :ref="(element) => setInputRef(element, index)"
          :value="char"
          :disabled="disabled"
          :inputmode="alphanumeric ? 'text' : 'numeric'"
          :autocomplete="index === 0 ? 'one-time-code' : 'off'"
          :aria-label="`${label} character ${index + 1}`"
          maxlength="1"
          class="relative z-10 h-full w-full min-w-0 bg-transparent text-center text-base font-bold uppercase text-slate-900 outline-none sm:text-xl"
          @input="onInput(index, $event)"
          @keydown="onKeydown(index, $event)"
          @paste="onPaste(index, $event)"
          @focus="onFocus(index)"
        />
      </label>
    </div>

    <p class="mt-3 text-center text-[11px] text-slate-400">
      Paste the full code or type it character by character.
    </p>
  </div>
</template>

<style scoped>
.liquid-fill {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 0%;
  background: linear-gradient(
    180deg,
    rgba(150, 197, 247, 0.5),
    rgba(255, 79, 0, 0.5)
  );
  transition: height 480ms cubic-bezier(0.22, 1, 0.36, 1);
}

.liquid-fill::after {
  content: "";
  position: absolute;
  left: -60%;
  right: -60%;
  top: -7px;
  height: 14px;
  border-radius: 50%;
  background: rgba(150, 197, 247, 0.55);
  animation: liquid-wave 2.4s linear infinite;
}

.liquid-cell--filled .liquid-fill {
  height: 100%;
}

@keyframes liquid-wave {
  0% {
    transform: translateX(-8%) rotate(0deg);
  }
  50% {
    transform: translateX(8%) rotate(2deg);
  }
  100% {
    transform: translateX(-8%) rotate(0deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .liquid-fill,
  .liquid-fill::after {
    transition: none;
    animation: none;
  }
}
</style>
