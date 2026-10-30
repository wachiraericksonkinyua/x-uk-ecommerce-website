import { createApiClient, ApiError } from "@gwx/api";
import type { AuthUser, Session } from "./types";

export const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const ACCESS_TOKEN_KEY = "access_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
export const USER_KEY = "user";

/** A bare client with no auth hooks — used for login/signup/refresh to avoid recursion. */
export const authApi = createApiClient({ baseUrl: API_URL });

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function saveSession(session: Session, user?: AuthUser | null) {
  if (session?.access_token) localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token);
  if (session?.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return false;
  try {
    const res = await authApi.post<{ session: Session; user?: AuthUser }>(
      "/auth/refresh",
      { refresh_token: refreshToken }
    );
    if (res?.session?.access_token) {
      saveSession(res.session, res.user ?? null);
      return true;
    }
  } catch {
    /* fall through to failure */
  }
  return false;
}

function redirectToLogin() {
  const { pathname, search } = window.location;
  if (pathname.startsWith("/login")) return;
  const next = encodeURIComponent(pathname + search);
  window.location.assign(`/login?next=${next}`);
}

export const api = createApiClient({
  baseUrl: API_URL,
  getToken: getAccessToken,
  onUnauthorized: async () => {
    if (!refreshInFlight) {
      refreshInFlight = refreshTokens().finally(() => {
        refreshInFlight = null;
      });
    }
    const ok = await refreshInFlight;
    if (!ok) {
      clearSession();
      redirectToLogin();
    }
  },
});

export { ApiError };

/** Normalise any thrown value into a human-readable message. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    if (Array.isArray(error.detail) && error.detail.length > 0) {
      const first = error.detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}
