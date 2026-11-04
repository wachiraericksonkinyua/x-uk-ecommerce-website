<script setup lang="ts">
import { ref } from "vue";
import { ArrowUpRight, Mail, MessageCircle } from "@lucide/vue";
import { RouterLink } from "vue-router";
import { toast } from "vue-sonner";

const email = ref("");
const whatsappUrl = "https://wa.me/254112323814";

function subscribe() {
  const value = email.value.trim();
  if (!value || !value.includes("@")) {
    toast.error("Enter a valid email address");
    return;
  }
  toast.success("You are on the list for new arrivals");
  email.value = "";
}
</script>

<template>
  <div class="mx-auto mt-16 max-w-7xl px-4 sm:px-6">
    <section
      id="whatsapp"
      class="relative overflow-hidden rounded-3xl bg-slate-950 px-6 py-8 text-white shadow-[0_30px_70px_-40px_rgba(15,23,42,0.8)] sm:px-8 lg:px-10"
    >
      <div
        class="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-brand-orange/25 blur-3xl"
      />
      <div
        class="pointer-events-none absolute -bottom-24 left-1/4 h-48 w-48 rounded-full bg-brand-blue/20 blur-3xl"
      />
      <div class="relative grid gap-6 lg:grid-cols-[1.1fr_1fr] lg:items-center">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-brand-blue-300">
            New arrivals first
          </p>
          <h2 class="mt-2 max-w-xl text-2xl font-black tracking-tight sm:text-3xl">
            Ready to Get Our New Stuff?
          </h2>
          <p class="mt-2 max-w-xl text-sm text-slate-400">
            Join the drop list for fresh electronics, limited restocks and
            members-only pricing.
          </p>
        </div>

        <div class="space-y-3">
          <form class="flex flex-col gap-2 sm:flex-row" @submit.prevent="subscribe">
            <label
              class="flex min-w-0 flex-1 items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-3 text-sm backdrop-blur"
            >
              <Mail :size="16" class="shrink-0 text-brand-blue-300" />
              <input
                v-model="email"
                type="email"
                placeholder="you@example.com"
                class="min-w-0 flex-1 bg-transparent text-white placeholder:text-slate-500 outline-none"
              />
            </label>
            <button
              type="submit"
              class="inline-flex items-center justify-center gap-2 rounded-full bg-brand-orange px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 hover:shadow-[0_14px_30px_-12px_rgba(255,79,0,0.8)]"
            >
              Join the list <ArrowUpRight :size="15" />
            </button>
          </form>
          <a
            :href="whatsappUrl"
            target="_blank"
            rel="noreferrer"
            class="inline-flex items-center gap-2 text-xs font-medium text-brand-blue-300 transition hover:text-white"
          >
            <MessageCircle :size="15" /> Or talk to us on WhatsApp
          </a>
        </div>
      </div>
    </section>
  </div>

  <footer class="mt-10 border-t border-slate-800 bg-slate-950 text-slate-300">
    <div class="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4">
      <div>
        <RouterLink to="/" class="inline-flex items-center gap-2 text-white">
          <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto rounded-md" />
        </RouterLink>
        <p class="mt-3 max-w-xs text-sm text-slate-400">
          Curated electronics and accessories, tested and delivered countrywide.
        </p>
      </div>

      <div>
        <h4 class="text-sm font-semibold text-white">Shop</h4>
        <ul class="mt-3 space-y-2 text-sm">
          <li>
            <RouterLink
              to="/shop"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              All Products
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/shop?sort_by=created_at&order=desc"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              New Arrivals
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/track"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              Track Order
            </RouterLink>
          </li>
        </ul>
      </div>

      <div>
        <h4 class="text-sm font-semibold text-white">Account</h4>
        <ul class="mt-3 space-y-2 text-sm">
          <li>
            <RouterLink
              to="/profile"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              My Profile
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/orders"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              My Orders
            </RouterLink>
          </li>
          <li>
            <RouterLink
              to="/wishlist"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              Wishlist
            </RouterLink>
          </li>
        </ul>
      </div>

      <div>
        <h4 class="text-sm font-semibold text-white">Support</h4>
        <ul class="mt-3 space-y-2 text-sm">
          <li>
            <RouterLink
              to="/track"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              Fast delivery
            </RouterLink>
          </li>
          <li>
            <a
              :href="whatsappUrl"
              target="_blank"
              rel="noreferrer"
              class="inline-flex text-slate-400 transition hover:translate-x-0.5 hover:text-brand-orange"
            >
              WhatsApp Support
            </a>
          </li>
        </ul>
      </div>
    </div>

    <div class="border-t border-white/10 py-5 text-center text-xs text-slate-500">
      &copy; {{ new Date().getFullYear() }} GWV-xuk. All rights reserved.
    </div>
  </footer>
</template>
