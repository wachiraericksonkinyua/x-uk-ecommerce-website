import { createRouter, createWebHistory } from "vue-router";

import Layout from "../components/Layout.vue";
import { useAuthStore } from "../store/auth";
import CartPage from "../pages/CartPage.vue";
import CheckoutPage from "../pages/CheckoutPage.vue";
import ForgotPasswordPage from "../pages/ForgotPasswordPage.vue";
import HomePage from "../pages/HomePage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MyOrdersPage from "../pages/MyOrdersPage.vue";
import NotFoundPage from "../pages/NotFoundPage.vue";
import OrderTrackingPage from "../pages/OrderTrackingPage.vue";
import ProductDetailPage from "../pages/ProductDetailPage.vue";
import ProfilePage from "../pages/ProfilePage.vue";
import ShopPage from "../pages/ShopPage.vue";
import SignupPage from "../pages/SignupPage.vue";
import WishlistPage from "../pages/WishlistPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginPage },
    { path: "/signup", component: SignupPage },
    { path: "/forgot-password", component: ForgotPasswordPage },

    {
      path: "/",
      component: Layout,
      children: [
        { path: "", component: HomePage },
        { path: "shop", component: ShopPage },
        { path: "products/:id", component: ProductDetailPage },
        { path: "track", component: OrderTrackingPage },
        { path: "track/:orderRef", component: OrderTrackingPage },
        { path: "cart", component: CartPage, meta: { requiresAuth: true } },
        {
          path: "checkout",
          component: CheckoutPage,
          meta: { requiresAuth: true },
        },
        {
          path: "wishlist",
          component: WishlistPage,
          meta: { requiresAuth: true },
        },
        {
          path: "profile",
          component: ProfilePage,
          meta: { requiresAuth: true },
        },
        {
          path: "orders",
          component: MyOrdersPage,
          meta: { requiresAuth: true },
        },
        { path: ":pathMatch(.*)*", component: NotFoundPage },
      ],
    },
  ],
});

router.beforeEach((to) => {
  if (!to.meta.requiresAuth) return true;
  const auth = useAuthStore();
  if (auth.token) return true;
  return { path: "/login", query: { next: to.fullPath } };
});

export default router;
