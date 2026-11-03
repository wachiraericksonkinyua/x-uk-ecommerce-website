<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { ImagePlus, Link2, Star, Trash2, Upload } from "@lucide/vue";
import { toast } from "vue-sonner";

import Modal from "./Modal.vue";
import { api, errorMessage } from "../lib/api";
import { useAdminProduct } from "../hooks/queries";
import type { Product, ProductImage } from "../lib/types";

const props = defineProps<{
  open: boolean;
  categories: { id: string; name: string }[];
  product?: Product | null;
}>();

const emit = defineEmits<{ close: []; saved: [] }>();

const queryClient = useQueryClient();
const primaryFileRef = ref<HTMLInputElement | null>(null);
const galleryFileRef = ref<HTMLInputElement | null>(null);
const galleryImages = ref<ProductImage[]>(props.product?.product_images ?? []);
const isEdit = computed(() => Boolean(props.product?.id));

const { data: fullProduct } = useAdminProduct(() => props.product?.id);

const form = reactive({
  name: props.product?.name ?? "",
  price: String(props.product?.price ?? ""),
  brand: props.product?.brand ?? "",
  description: props.product?.description ?? "",
  color: props.product?.color ?? "",
  category_id: props.product?.category_id ?? "",
  stock_quantity: String(props.product?.stock_quantity ?? 0),
  compatibility: props.product?.compatibility ?? "",
  specs: JSON.stringify(props.product?.specs ?? {}, null, 2),
  image_url: props.product?.image_url ?? "",
});

watch(fullProduct, (product) => {
  if (!product) return;
  form.name = product.name;
  form.price = String(product.price);
  form.brand = product.brand ?? "";
  form.description = product.description ?? "";
  form.color = product.color ?? "";
  form.category_id = product.category_id ?? "";
  form.stock_quantity = String(product.stock_quantity ?? 0);
  form.compatibility = product.compatibility ?? "";
  form.specs = JSON.stringify(product.specs ?? {}, null, 2);
  form.image_url = product.image_url ?? "";
  galleryImages.value = product.product_images ?? [];
});

function parseSpecs(): Record<string, unknown> {
  if (!form.specs.trim()) return {};
  let parsed: unknown;
  try {
    parsed = JSON.parse(form.specs);
  } catch {
    throw new Error("Specs must be valid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Specs must be a JSON object");
  }
  return parsed as Record<string, unknown>;
}

function selectedCategoryName() {
  return props.categories.find((category) => category.id === form.category_id)?.name;
}

function invalidate() {
  for (const queryKey of [
    ["admin-products"],
    ["admin-product"],
    ["products"],
    ["product"],
    ["admin-sales-analytics"],
    ["admin-dashboard"],
  ]) {
    queryClient.invalidateQueries({ queryKey });
  }
}

const save = useMutation({
  mutationFn: async () => {
    const specs = parseSpecs();
    const primaryFile = primaryFileRef.value?.files?.[0] ?? null;
    const galleryFiles = Array.from(galleryFileRef.value?.files ?? []);

    if (!isEdit.value) {
      if (!primaryFile && !form.image_url.trim()) {
        throw new Error("Add a primary image file or paste an image URL");
      }

      const body = new FormData();
      body.append("name", form.name);
      body.append("price", form.price);
      body.append("brand", form.brand);
      body.append("description", form.description);
      body.append("color", form.color);
      body.append("stock_quantity", form.stock_quantity || "0");
      body.append("compatibility", form.compatibility.trim());
      body.append("specs", JSON.stringify(specs));
      if (form.image_url.trim()) body.append("image_url", form.image_url.trim());
      if (form.category_id) {
        body.append("category_id", form.category_id);
        const name = selectedCategoryName();
        if (name) body.append("category", name);
      }
      if (primaryFile) body.append("primary_image", primaryFile);
      galleryFiles.forEach((file) => body.append("images", file));
      return api.post("/admin/products", body);
    }

    const productId = props.product!.id;
    let result = await api.patch(`/admin/products/${productId}`, {
      name: form.name,
      price: Number(form.price),
      brand: form.brand,
      description: form.description,
      color: form.color,
      category_id: form.category_id || null,
      category: form.category_id ? selectedCategoryName() ?? null : null,
      stock_quantity: Number(form.stock_quantity),
      compatibility: form.compatibility || null,
      specs,
      image_url: form.image_url.trim() || null,
    });

    if (primaryFile) {
      const body = new FormData();
      body.append("file", primaryFile);
      result = await api.post(`/admin/products/${productId}/primary-image`, body);
    }

    if (galleryFiles.length > 0) {
      const body = new FormData();
      galleryFiles.forEach((file) => body.append("files", file));
      await api.post(`/admin/products/${productId}/images`, body);
    }

    return result;
  },
  onSuccess: () => {
    invalidate();
    toast.success(isEdit.value ? "Product updated" : "Product created");
    emit("saved");
    emit("close");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const removeImage = useMutation({
  mutationFn: (imageId: string) =>
    api.del(`/admin/products/${props.product!.id}/images/${imageId}`),
  onSuccess: (_data, imageId) => {
    galleryImages.value = galleryImages.value.filter((image) => image.id !== imageId);
    invalidate();
    toast.success("Gallery image removed");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function removeGalleryImage(image: ProductImage) {
  if (!image.id) return;
  if (window.confirm("Remove this gallery image?")) {
    removeImage.mutate(image.id);
  }
}

function submit() {
  if (!form.name.trim() || !form.price.trim()) {
    toast.error("Name and price are required");
    return;
  }
  try {
    parseSpecs();
  } catch (error) {
    toast.error(errorMessage(error));
    return;
  }
  save.mutate();
}
</script>

<template>
  <Modal
    :open="open"
    :title="isEdit ? 'Edit Product' : 'Create Product'"
    size="lg"
    @close="emit('close')"
  >
    <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">Name</label>
        <input
          v-model="form.name"
          required
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Price (KES)
        </label>
        <input
          v-model="form.price"
          required
          type="number"
          min="0"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">
          Stock quantity
        </label>
        <input
          v-model="form.stock_quantity"
          type="number"
          min="0"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Category
        </label>
        <select
          v-model="form.category_id"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        >
          <option value="">Uncategorized</option>
          <option
            v-for="category in categories"
            :key="category.id"
            :value="category.id"
          >
            {{ category.name }}
          </option>
        </select>
        <p class="mt-1 text-xs text-slate-400">
          Selecting a category automatically stores its UUID and human-readable name.
        </p>
      </div>

      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">Brand</label>
        <input
          v-model="form.brand"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>
      <div>
        <label class="text-xs font-semibold uppercase text-slate-500">Color</label>
        <input
          v-model="form.color"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Description
        </label>
        <textarea
          v-model="form.description"
          rows="3"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Compatibility
        </label>
        <input
          v-model="form.compatibility"
          placeholder="e.g. iPhone 15 / USB-C devices"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="text-xs font-semibold uppercase text-slate-500">
          Technical specs (JSON object)
        </label>
        <textarea
          v-model="form.specs"
          rows="3"
          placeholder='{"wattage":"65W","connector":"USB-C","anc":true}'
          class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 font-mono text-xs outline-none focus:border-brand-orange"
        />
      </div>

      <div class="sm:col-span-2 rounded-2xl border border-brand-blue-200 bg-brand-blue-50/60 p-4">
        <div class="flex items-center gap-2">
          <Star :size="15" class="text-brand-orange" />
          <p class="text-xs font-semibold uppercase tracking-wide text-brand-blue-700">
            Primary image
          </p>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-4">
          <div
            class="flex h-24 w-24 items-center justify-center overflow-hidden rounded-xl border border-brand-blue-200 bg-white"
          >
            <img
              v-if="form.image_url"
              :src="form.image_url"
              alt="Primary product preview"
              class="h-full w-full object-contain"
            />
            <ImagePlus v-else :size="24" class="text-slate-300" />
          </div>
          <div class="min-w-0 flex-1 space-y-2">
            <label class="flex items-center gap-2 text-xs font-medium text-slate-500">
              <Link2 :size="14" /> Image URL
            </label>
            <input
              v-model="form.image_url"
              placeholder="https://… or leave blank and upload a file"
              class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-orange"
            />
            <input
              ref="primaryFileRef"
              type="file"
              accept="image/*"
              class="w-full text-xs"
            />
          </div>
        </div>
      </div>

      <div class="sm:col-span-2">
        <label class="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
          <ImagePlus :size="14" /> Additional gallery images
        </label>
        <input
          ref="galleryFileRef"
          type="file"
          accept="image/*"
          multiple
          class="mt-2 w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-sm"
        />

        <div v-if="galleryImages.length > 0" class="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
          <div
            v-for="image in galleryImages"
            :key="image.id ?? image.image_url"
            class="group relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
          >
            <img :src="image.image_url" alt="Gallery product" class="h-full w-full object-contain" />
            <button
              v-if="image.id"
              type="button"
              class="absolute right-1 top-1 rounded-full bg-rose-500 p-1 text-white opacity-0 transition group-hover:opacity-100"
              aria-label="Remove gallery image"
              @click="removeGalleryImage(image)"
            >
              <Trash2 :size="12" />
            </button>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 sm:col-span-2">
        <button
          type="button"
          class="rounded-full border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
          @click="emit('close')"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="save.isPending.value"
          class="inline-flex items-center gap-2 rounded-full bg-brand-orange px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:bg-slate-300"
        >
          <Upload :size="15" />
          {{ save.isPending.value ? "Saving…" : isEdit ? "Save changes" : "Create product" }}
        </button>
      </div>
    </form>
  </Modal>
</template>
