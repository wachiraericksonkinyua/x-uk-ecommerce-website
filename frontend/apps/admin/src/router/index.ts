import { createRouter, createWebHistory } from "vue-router";

import AdminGuard from "../components/AdminGuard.vue";
import CategoriesPage from "../pages/CategoriesPage.vue";
import CustomersPage from "../pages/CustomersPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import DeliveryPage from "../pages/DeliveryPage.vue";
import LeadsPage from "../pages/LeadsPage.vue";
import AdminLoginPage from "../pages/LoginPage.vue";
import OrdersPage from "../pages/OrdersPage.vue";
import ProductsPage from "../pages/ProductsPage.vue";
import ReviewsPage from "../pages/ReviewsPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: AdminLoginPage },
    {
      path: "/",
      component: AdminGuard,
      children: [
        { path: "", component: DashboardPage },
        { path: "orders", component: OrdersPage },
        { path: "products", component: ProductsPage },
        { path: "categories", component: CategoriesPage },
        { path: "delivery", component: DeliveryPage },
        { path: "customers", component: CustomersPage },
        { path: "reviews", component: ReviewsPage },
        { path: "leads", component: LeadsPage },
      ],
    },
  ],
});

export default router;
