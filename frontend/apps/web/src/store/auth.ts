import { defineStore } from "pinia";
import { ref } from "vue";

import {
  clearSession,
  getAccessToken,
  getStoredUser,
  saveSession,
} from "../lib/api";
import type { AuthUser, Session } from "../lib/types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<AuthUser | null>(getStoredUser());
  const token = ref<string | null>(getAccessToken());

  function setSession(session: Session, nextUser: AuthUser | null = null) {
    saveSession(session, nextUser);
    user.value = nextUser ?? getStoredUser();
    token.value = session.access_token;
  }

  function logout() {
    clearSession();
    user.value = null;
    token.value = null;
  }

  return { user, token, setSession, logout };
});
