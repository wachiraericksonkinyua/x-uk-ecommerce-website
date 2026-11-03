<script setup lang="ts">
import { computed, ref } from "vue";
import { useMutation, useQueryClient } from "@tanstack/vue-query";
import { Check, EyeOff, Pencil, Plus, Star, Trash2 } from "@lucide/vue";
import { toast } from "vue-sonner";

import Badge from "../components/Badge.vue";
import Card from "../components/Card.vue";
import EmptyState from "../components/EmptyState.vue";
import PageLoader from "../components/PageLoader.vue";
import Pagination from "../components/Pagination.vue";
import ReviewFormModal from "../components/ReviewFormModal.vue";
import Td from "../components/Td.vue";
import Th from "../components/Th.vue";
import { api, errorMessage } from "../lib/api";
import { useAdminReviews } from "../hooks/queries";
import type { Review } from "../lib/types";
import { cn, formatDate } from "../lib/utils";

const queryClient = useQueryClient();
const page = ref(1);
const pageSize = 20;
const editing = ref<Review | "new" | null>(null);

const { data, isLoading } = useAdminReviews(() => ({ page: page.value, pageSize }));
const reviews = computed(() => data.value?.data ?? []);
const editingInitial = computed(() =>
  editing.value && editing.value !== "new" ? editing.value : undefined
);

const del = useMutation({
  mutationFn: (id: string) => api.del(`/admin/reviews/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
    toast.success("Review deleted");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

const toggleApproval = useMutation({
  mutationFn: ({ id, isApproved }: { id: string; isApproved: boolean }) =>
    api.patch(`/admin/reviews/${id}/approve`, { is_approved: isApproved }),
  onSuccess: (_data, variables) => {
    queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
    toast.success(variables.isApproved ? "Review approved" : "Review hidden");
  },
  onError: (error) => toast.error(errorMessage(error)),
});

function confirmDelete(id: string) {
  if (window.confirm("Delete this review?")) {
    del.mutate(id);
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Reviews</h1>
        <p class="text-sm text-slate-500">
          Moderate, edit and create verified-buyer product reviews.
        </p>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-full bg-brand-orange px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600"
        @click="editing = 'new'"
      >
        <Plus :size="16" /> New Review
      </button>
    </div>

    <Card class="overflow-hidden">
      <PageLoader v-if="isLoading" label="Loading reviews…" />
      <div v-else-if="reviews.length === 0" class="p-6">
        <EmptyState title="No reviews yet" />
      </div>
      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50">
              <tr>
                <Th>Rating</Th>
                <Th>Comment</Th>
                <Th>Status</Th>
                <Th>Date</Th>
                <Th class="text-right">Actions</Th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="review in reviews"
                :key="review.id"
                class="border-t border-slate-100"
              >
                <Td>
                  <div class="flex items-center gap-1">
                    <Star
                      v-for="value in [1, 2, 3, 4, 5]"
                      :key="value"
                      :size="14"
                      :class="
                        value <= review.rating
                          ? 'fill-amber-400 text-amber-400'
                          : 'fill-slate-200 text-slate-200'
                      "
                    />
                  </div>
                </Td>
                <Td class="max-w-md">
                  <p class="text-slate-600">{{ review.comment }}</p>
                  <p class="text-xs text-slate-400">
                    Product {{ review.product_id.slice(0, 8) }}…
                  </p>
                </Td>
                <Td>
                  <Badge
                    :class="
                      cn(
                        review.is_approved
                          ? 'bg-brand-orange-soft text-brand-orange-dark'
                          : 'bg-amber-100 text-amber-700'
                      )
                    "
                  >
                    {{ review.is_approved ? "Approved" : "Pending" }}
                  </Badge>
                </Td>
                <Td>{{ formatDate(review.created_at) }}</Td>
                <Td class="text-right">
                  <div class="flex justify-end gap-1">
                    <button
                      class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-brand-orange"
                      aria-label="Edit review"
                      @click="editing = review"
                    >
                      <Pencil :size="16" />
                    </button>
                    <button
                      :disabled="toggleApproval.isPending.value"
                      :class="
                        cn(
                          'rounded-lg p-2 text-slate-500 disabled:opacity-50',
                          review.is_approved
                            ? 'hover:bg-amber-50 hover:text-amber-600'
                            : 'hover:bg-brand-orange-soft hover:text-brand-orange'
                        )
                      "
                      :aria-label="
                        review.is_approved ? 'Hide review' : 'Approve review'
                      "
                      :title="review.is_approved ? 'Hide' : 'Approve'"
                      @click="
                        toggleApproval.mutate({
                          id: review.id,
                          isApproved: !review.is_approved,
                        })
                      "
                    >
                      <EyeOff v-if="review.is_approved" :size="16" />
                      <Check v-else :size="16" />
                    </button>
                    <button
                      class="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600"
                      aria-label="Delete review"
                      @click="confirmDelete(review.id)"
                    >
                      <Trash2 :size="16" />
                    </button>
                  </div>
                </Td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :page="page"
          :page-size="pageSize"
          :total="data?.total ?? 0"
          @page="page = $event"
        />
      </template>
    </Card>

    <ReviewFormModal
      v-if="editing"
      :initial="editingInitial"
      @close="editing = null"
    />
  </div>
</template>
