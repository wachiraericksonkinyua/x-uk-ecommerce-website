# GWV-xuk Frontend (Phase 0 scaffold)

This folder is the starting point for the storefront, admin dashboard, and mobile
app. It currently contains a **generated, typed API client** so you never
hand-write request/response shapes.

See `../docs/FRONTEND_ROADMAP.md` for the full phase plan.

## Layout

```
frontend/
├── openapi.json              # exported from the running backend (generated)
├── scripts/
│   └── generate-api.sh       # regenerate openapi.json + TS types
└── packages/
    └── api/                  # @gwx/api — typed fetch client
        ├── package.json
        ├── tsconfig.json
        └── src/
            ├── schema.d.ts   # AUTO-GENERATED — do not edit
            ├── client.ts     # thin fetch wrapper (auth-aware)
            └── index.ts
```

Later you will add:
```
frontend/apps/web      # Vue storefront
frontend/apps/admin    # Vue admin dashboard
frontend/apps/mobile   # Expo (React Native) app
frontend/packages/ui   # shared components
```

## Running the apps

Both apps are Vite + Vue 3 + TypeScript + Tailwind v4 and consume `@gwx/api`.
Make sure the backend allows their origins: set
`CORS_ORIGINS="http://localhost:5173,http://localhost:5174"` in the repo `.env`.

```bash
# from frontend/
npm install            # installs all workspaces (root hoisting)

npm run dev:web        # Customer storefront  -> http://localhost:5173
npm run dev:admin      # Admin & WhatsApp CRM -> http://localhost:5174

npm run typecheck      # tsc --noEmit across both apps
npm run build:web      # production build (typecheck + vite build)
npm run build:admin
```

Each app reads `VITE_API_URL` (see `apps/*/.env.example`, default
`http://127.0.0.1:8000`).

### What lives where

| App | Port | Highlights |
|---|---|---|
| `apps/web` | 5173 | Home, Shop (filters), Product detail + reviews, Cart, M-Pesa checkout + live tracking, Wishlist, Profile/avatar, My Orders, floating AI assistant |
| `apps/admin` | 5174 | Admin guard, dashboard KPIs + low-stock restock, product/image CRUD, orders (status/verify/cancel), categories, delivery zones, customers, review moderation, WhatsApp lead triage CRM |

Public storefront endpoints (no token): products, categories, reviews, delivery
locations, order tracking. Everything else requires a login and is guarded by a
route guard that redirects to `/login?next=<path>`.


## Regenerate the API types

Whenever the backend changes:

```bash
# terminal 1
uvicorn app.main:app --reload

# terminal 2
bash frontend/scripts/generate-api.sh
```

This writes `frontend/openapi.json` and `frontend/packages/api/src/schema.d.ts`.

## Using the client

```ts
import { createApiClient, type paths } from "@gwx/api";

const api = createApiClient({
  baseUrl: import.meta.env.VITE_API_URL, // e.g. http://127.0.0.1:8000
  getToken: () => localStorage.getItem("access_token"),
  onUnauthorized: async () => {
    // call /auth/refresh here, or redirect to /login
  },
});

// untyped convenience
const res = await api.get<{ data: unknown[] }>("/products/", { search: "iphone" });

// fully-typed (from the generated schema)
type ProductList = paths["/products/"]["get"]["responses"][200]["content"]["application/json"];
```

## Next step (Phase 0 → 1)

```bash
cd frontend/apps
npm create vite@latest web -- --template vue-ts
cd web
npm install vue-router pinia @tanstack/vue-query @lucide/vue vue-sonner
npm install tailwindcss @tailwindcss/vite
```

Then follow `../docs/FRONTEND_ROADMAP.md` Phase 1: browse products. The current
`apps/web` and `apps/admin` already implement the storefront and admin flows
with Vue 3, Vue Router, Pinia, TanStack Vue Query, and `vue-sonner`.
