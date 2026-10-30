<script setup lang="ts">
import { computed, ref } from "vue";
import { useQueryClient } from "@tanstack/vue-query";
import {
  ChevronDown,
  Heart,
  LogOut,
  Menu,
  Package,
  Search,
  ShoppingBag,
  Store,
  Truck,
  User,
  X,
} from "@lucide/vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";

import { useCategories, useCart, useWishlist } from "../hooks/queries";
import { useAuthStore } from "../store/auth";
import { cn } from "../lib/utils";
import AiAssistant from "./AiAssistant.vue";

const router = useRouter();
const route = useRoute();
const queryClient = useQueryClient();
const auth = useAuthStore();

const search = ref("");
const mobileOpen = ref(false);
const accountOpen = ref(false);
const menuOpen = ref(false);

const { data: categories } = useCategories();
const { data: cart } = useCart(() => Boolean(auth.token));
const { data: wishlist } = useWishlist(() => Boolean(auth.token));

const cartCount = computed(() =>
  (cart.value ?? []).reduce((sum, item) => sum + item.quantity, 0)
);

function navClass(active: boolean) {
  return active
    ? "text-sm font-semibold text-blue-700"
    : "text-sm font-medium text-slate-600 transition hover:text-blue-700";
}

function submitSearch() {
  const term = search.value.trim();
  router.push(term ? `/shop?search=${encodeURIComponent(term)}` : "/shop");
  mobileOpen.value = false;
  menuOpen.value = false;
}

function handleLogout() {
  auth.logout();
  queryClient.clear();
  accountOpen.value = false;
  toast.success("Signed out");
  router.push("/");
}

function closeMenu() {
  menuOpen.value = false;
}
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header
      class="sticky top-0 z-30 border-b border-slate-100 bg-white/95 backdrop-blur"
    >
      <div class="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <RouterLink
          to="/"
          class="flex items-center gap-2"
          aria-label="Gadgets With Vin"
        >
          <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto" />
        </RouterLink>

        <nav class="hidden items-center gap-6 lg:flex">
          <RouterLink to="/" :class="navClass(route.path === '/')">
            Home
          </RouterLink>
          <RouterLink to="/shop" :class="navClass(route.path === '/shop')">
            Shop
          </RouterLink>
          <div class="group relative">
            <button
              class="flex items-center gap-1 text-sm font-medium text-slate-600 transition hover:text-blue-700"
            >
              Categories <ChevronDown :size="15" />
            </button>
            <div
              class="invisible absolute left-0 top-full z-40 w-56 translate-y-1 rounded-2xl border border-slate-100 bg-white p-2 opacity-0 shadow-lg transition-all group-hover:visible group-hover:translate-y-0 group-hover:opacity-100"
            >
              <p
                v-if="!categories?.length"
                class="px-3 py-2 text-xs text-slate-400"
              >
                No categories yet
              </p>
              <RouterLink
                v-for="category in categories ?? []"
                :key="category.id"
                :to="`/shop?category=${encodeURIComponent(category.name)}`"
                class="block rounded-xl px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-50 hover:text-blue-700"
              >
                {{ category.name }}
              </RouterLink>
            </div>
          </div>
          <RouterLink
            to="/track"
            :class="navClass(route.path.startsWith('/track'))"
          >
            Track Order
          </RouterLink>
        </nav>

        <form
          class="ml-auto hidden flex-1 max-w-md items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 md:flex"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="search"
            placeholder="Search phones, brands…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>

        <div class="ml-auto flex items-center gap-3 md:ml-0">
          <RouterLink
            to="/wishlist"
            class="relative hidden rounded-full p-2 text-slate-600 transition hover:bg-slate-50 hover:text-rose-500 sm:block"
            aria-label="Wishlist"
          >
            <Heart :size="20" />
            <span
              v-if="(wishlist?.length ?? 0) > 0"
              class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white"
            >
              {{ wishlist?.length }}
            </span>
          </RouterLink>
          <RouterLink
            to="/cart"
            class="relative rounded-full p-2 text-slate-600 transition hover:bg-slate-50 hover:text-blue-700"
            aria-label="Cart"
          >
            <ShoppingBag :size="20" />
            <span
              v-if="cartCount > 0"
              class="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-700 px-1 text-[10px] font-bold text-white"
            >
              {{ cartCount }}
            </span>
          </RouterLink>

          <div v-if="auth.token" class="relative hidden sm:block">
            <button
              class="flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:text-blue-700"
              @click="accountOpen = !accountOpen"
            >
              <User :size="16" />
              <span class="max-w-[7rem] truncate">
                {{ auth.user?.email?.split("@")[0] ?? "Account" }}
              </span>
              <ChevronDown :size="14" />
            </button>
            <div
              v-if="accountOpen"
              class="absolute right-0 top-full mt-2 w-48 rounded-2xl border border-slate-100 bg-white p-2 shadow-lg"
            >
              <RouterLink
                to="/profile"
                class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                @click="accountOpen = false"
              >
                <User :size="15" /> My Profile
              </RouterLink>
              <RouterLink
                to="/orders"
                class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                @click="accountOpen = false"
              >
                <Package :size="15" /> My Orders
              </RouterLink>
              <button
                class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
                @click="handleLogout"
              >
                <LogOut :size="15" /> Sign out
              </button>
            </div>
          </div>
          <RouterLink
            v-else
            to="/login"
            class="hidden rounded-full bg-blue-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-800 sm:inline-flex"
          >
            Login
          </RouterLink>

          <button
            class="rounded-full p-2 text-slate-600 lg:hidden"
            aria-label="Menu"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" :size="20" />
            <Menu v-else :size="20" />
          </button>
        </div>
      </div>

      <div
        v-if="menuOpen"
        class="border-t border-slate-100 bg-white px-4 py-3 lg:hidden"
      >
        <form
          class="mb-3 flex items-center gap-2 rounded-full bg-slate-50 px-4 py-2"
          @submit.prevent="submitSearch"
        >
          <Search :size="16" class="text-slate-400" />
          <input
            v-model="search"
            placeholder="Search phones…"
            class="w-full bg-transparent text-sm outline-none"
          />
        </form>
        <div class="flex flex-col gap-1">
          <RouterLink
            to="/"
            class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
            @click="closeMenu"
          >
            Home
          </RouterLink>
          <RouterLink
            to="/shop"
            class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
            @click="closeMenu"
          >
            Shop
          </RouterLink>
          <RouterLink
            to="/track"
            class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
            @click="closeMenu"
          >
            Track Order
          </RouterLink>
          <RouterLink
            to="/wishlist"
            class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
            @click="closeMenu"
          >
            Wishlist
          </RouterLink>
          <template v-if="auth.token">
            <RouterLink
              to="/profile"
              class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
              @click="closeMenu"
            >
              My Profile
            </RouterLink>
            <RouterLink
              to="/orders"
              class="rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
              @click="closeMenu"
            >
              My Orders
            </RouterLink>
            <button
              class="rounded-xl px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
              @click="handleLogout"
            >
              Sign out
            </button>
          </template>
          <RouterLink
            v-else
            to="/login"
            class="rounded-xl bg-blue-700 px-3 py-2 text-center text-sm font-medium text-white"
            @click="closeMenu"
          >
            Login
          </RouterLink>
        </div>
      </div>
    </header>

    <main class="flex-1">
      <RouterView />
    </main>

    <footer class="mt-16 bg-[#061A40] text-slate-300">
      <div
        class="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4"
      >
        <div>
          <div class="flex items-center gap-2 text-white">
            <img src="/logo.png" alt="Gadgets With Vin" class="h-10 w-auto" />
          </div>
          <p class="mt-3 text-sm text-slate-400">
            Premium UK-used smartphones delivered countrywide. 100% M-Pesa
            verified.
          </p>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-white">Shop</h4>
          <ul class="mt-3 space-y-2 text-sm">
            <li>
              <RouterLink to="/shop" class="hover:text-white">
                All Products
              </RouterLink>
            </li>
            <li>
              <RouterLink
                to="/shop?sort_by=created_at&order=desc"
                class="hover:text-white"
              >
                New Arrivals
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/track" class="hover:text-white">
                Track Order
              </RouterLink>
            </li>
          </ul>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-white">Account</h4>
          <ul class="mt-3 space-y-2 text-sm">
            <li>
              <RouterLink to="/profile" class="hover:text-white">
                My Profile
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/orders" class="hover:text-white">
                My Orders
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/wishlist" class="hover:text-white">
                Wishlist
              </RouterLink>
            </li>
          </ul>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-white">Support</h4>
          <ul class="mt-3 space-y-2 text-sm">
            <li class="flex items-center gap-2"><Truck :size="15" /> Fast delivery</li>
            <li class="flex items-center gap-2"><Store :size="15" /> Physical store</li>
          </ul>
        </div>
      </div>
      <div class="border-t border-white/10 py-5 text-center text-xs text-slate-400">
        &copy; {{ new Date().getFullYear() }} GWV-xuk. All rights reserved.
      </div>
    </footer>

    <AiAssistant />
  </div>
</template>
