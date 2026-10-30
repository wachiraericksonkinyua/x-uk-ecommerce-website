<script setup lang="ts">
import { ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { ImagePlus, Trash2, Upload } from "@lucide/vue";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import Spinner from "./Spinner.vue";
import { api, errorMessage } from "../lib/api";
import { useAdminProduct } from "../hooks/queries";
import type { Product } from "../lib/types";

const props = defineProps<{ product: Product }>();
const emit = defineEmits<{ close: [] }>();

const queryClient = useQueryClient();
const fileRef = ref<HTMLInputElement | null>(null);
const { data, isLoading, refetch } = useAdminProduct(() => props.product.id);

const upload = useMutation({
  mutationFn: () => {
    const body = new FormData();
    const files = fileRef.value?.files;
    if (files) {
      Array.from(files).forEach((file) => body.append("files", file));
    }
    return api.post(`/admin/products/${props.product.id}/images`, body);
  },
  onSuccess: () => {
    if (fileRef.value) fileRef.value.value = "";
    refetch();
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    toast.success("Images uploaded");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const remove = useMutation({
  mutationFn: (imageId: string) =>
    api.del(`/admin/products/${props.product.id}/images/${imageId}`),
  onSuccess: () => {
    refetch();
    toast.success("Image removed");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function submitUpload() {
  if (!fileRef.value?.files?.length) {
    toast.error("Select at least one image");
    return;
  }
  upload.mutate();
}
</script>

<template>
  <Modal
    :open="true"
    :title="`Manage Images — ${product.name}`"
    size="lg"
    @close="emit('close')"
  >
    <div v-if="isLoading" class="flex justify-center py-10">
      <Spinner class="h-8 w-8" />
    </div>
    <div v-else class="space-y-5">
      <div class="grid grid-cols-3 gap-3 sm:grid-cols-4">
        <div
          v-for="image in data?.product_images ?? []"
          :key="image.id"
          class="group relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
        >
          <img
            :src="image.image_url"
            alt="product"
            class="h-full w-full object-contain"
          />
          <button
            class="absolute right-1 top-1 rounded-full bg-rose-500 p-1 text-white opacity-0 transition group-hover:opacity-100"
            aria-label="Delete image"
            @click="image.id && remove.mutate(image.id)"
          >
            <Trash2 :size="13" />
          </button>
        </div>
        <p
          v-if="(data?.product_images ?? []).length === 0"
          class="col-span-full text-sm text-slate-500"
        >
          No images yet.
        </p>
      </div>

      <div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4">
        <label
          class="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500"
        >
          <ImagePlus :size="14" /> Add images
        </label>
        <input
          ref="fileRef"
          type="file"
          accept="image/*"
          multiple
          class="mt-2 w-full text-sm"
        />
        <button
          :disabled="upload.isPending.value"
          class="mt-3 inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-slate-300"
          @click="submitUpload"
        >
          <Upload :size="15" />
          {{ upload.isPending.value ? "Uploading…" : "Upload" }}
        </button>
      </div>
    </div>
  </Modal>
</template>
