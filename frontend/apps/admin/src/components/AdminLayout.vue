<script setup lang="ts">
import { ref } from "vue";
import { Menu, X } from "@lucide/vue";
import { RouterLink, RouterView } from "vue-router";

import AdminSidebar from "./AdminSidebar.vue";

const open = ref(false);
</script>

<template>
  <div class="flex min-h-screen bg-[#F4F7FB]">
    <aside class="hidden w-64 shrink-0 lg:block">
      <AdminSidebar @close="open = false" />
    </aside>

    <div v-if="open" class="fixed inset-0 z-40 lg:hidden">
      <div class="absolute inset-0 bg-slate-900/50" @click="open = false" />
      <div class="absolute left-0 top-0 h-full w-64">
        <AdminSidebar @close="open = false" />
      </div>
    </div>

    <div class="flex min-w-0 flex-1 flex-col">
      <header
        class="flex items-center gap-3 border-b border-slate-100 bg-white px-4 py-3 lg:hidden"
      >
        <button
          class="rounded-lg p-2 text-slate-600"
          aria-label="Menu"
          @click="open = !open"
        >
          <X v-if="open" :size="20" />
          <Menu v-else :size="20" />
        </button>
        <RouterLink to="/" class="flex items-center gap-2 font-bold text-slate-900">
          <img src="/logo.png" alt="Gadgets With Vin" class="h-8 w-auto" />
          Admin
        </RouterLink>
      </header>

      <main class="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>
