<script setup lang="ts">
import { Toaster } from "vue-sonner";

import MobileDock from "./components/MobileDock.vue";
</script>

<template>
  <RouterView />
  <MobileDock />
  <Toaster rich-colors position="top-right" />
</template>
