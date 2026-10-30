import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../store/auth";

/**
 * Returns a guard function. Call it inside a click handler; it returns `true`
 * when the user is authenticated, otherwise it redirects to
 * `/login?next=<current path>` and returns `false`.
 */
export function useRequireAuth(): () => boolean {
  const auth = useAuthStore();
  const router = useRouter();
  const route = useRoute();

  return () => {
    if (auth.token) return true;
    router.push({ path: "/login", query: { next: route.fullPath } });
    return false;
  };
}
