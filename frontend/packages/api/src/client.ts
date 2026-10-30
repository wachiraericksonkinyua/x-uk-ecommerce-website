/**
 * A tiny, dependency-free fetch client for the GWV-xuk API.
 *
 * Usage:
 *   const api = createApiClient({
 *     baseUrl: import.meta.env.VITE_API_URL,
 *     getToken: () => localStorage.getItem("access_token"),
 *     onUnauthorized: async () => { /* refresh token or redirect to /login *\/ },
 *   });
 *
 *   const products = await api.get<{ data: Product[] }>("/products/", { search: "iphone" });
 *
 * For fully-typed calls, import the generated `paths` / `components` types from
 * "./schema" and narrow the response yourself.
 */

export type { paths, components, operations } from "./schema";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface ApiClientOptions {
  baseUrl: string;
  /** Return the current access token, or null/undefined if logged out. */
  getToken?: () => string | null | undefined;
  /** Called on a 401 so you can refresh the token or redirect to login. */
  onUnauthorized?: () => void | Promise<void>;
}

interface RequestOptions {
  params?: Record<string, unknown>;
  body?: unknown;
}

export class ApiClient {
  private baseUrl: string;
  private getToken?: () => string | null | undefined;
  private onUnauthorized?: () => void | Promise<void>;

  constructor(options: ApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.getToken = options.getToken;
    this.onUnauthorized = options.onUnauthorized;
  }

  private buildUrl(path: string, params?: Record<string, unknown>): string {
    const url = new URL(this.baseUrl + path);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== "") {
          url.searchParams.append(key, String(value));
        }
      }
    }
    return url.toString();
  }

  async request<T>(path: string, method: string, options: RequestOptions = {}): Promise<T> {
    const headers: Record<string, string> = {};
    const token = this.getToken?.();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let body: BodyInit | undefined;
    if (options.body !== undefined) {
      if (options.body instanceof FormData) {
        body = options.body; // the browser sets the multipart boundary itself
      } else {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(options.body);
      }
    }

    const response = await fetch(this.buildUrl(path, options.params), { method, headers, body });

    if (response.status === 401) {
      await this.onUnauthorized?.();
    }

    const text = await response.text();
    const data = text ? JSON.parse(text) : undefined;

    if (!response.ok) {
      throw new ApiError(response.status, (data as { detail?: unknown } | undefined)?.detail ?? data);
    }
    return data as T;
  }

  get<T = unknown>(path: string, params?: Record<string, unknown>) {
    return this.request<T>(path, "GET", { params });
  }

  post<T = unknown>(path: string, body?: unknown) {
    return this.request<T>(path, "POST", { body });
  }

  patch<T = unknown>(path: string, body?: unknown) {
    return this.request<T>(path, "PATCH", { body });
  }

  put<T = unknown>(path: string, body?: unknown) {
    return this.request<T>(path, "PUT", { body });
  }

  del<T = unknown>(path: string, params?: Record<string, unknown>) {
    return this.request<T>(path, "DELETE", { params });
  }
}

export function createApiClient(options: ApiClientOptions): ApiClient {
  return new ApiClient(options);
}
