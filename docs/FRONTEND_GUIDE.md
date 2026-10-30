# Frontend Guide — React, the Two Apps, and How It All Fits Together

> This is the companion to `docs/FRONTEND_ROADMAP.md` (the plan) and
> `docs/BACKEND_GUIDE.md` (the API). The roadmap told you *what* to build; this
> guide explains *what we actually built* and teaches you the React/TypeScript
> ideas behind every file, assuming you have never written React before.
>
> Read it top-to-bottom once, then keep it open while you poke at the code.

---

## Table of contents

1. [How to read this guide](#1-how-to-read-this-guide)
2. [The big picture: where the frontend sits](#2-the-big-picture-where-the-frontend-sits)
3. [React in ~20 minutes (the only concepts you need)](#3-react-in-20-minutes-the-only-concepts-you-need)
4. [The stack, and why every tool exists](#4-the-stack-and-why-every-tool-exists)
5. [Project layout](#5-project-layout)
6. [Running the apps](#6-running-the-apps)
7. [The API layer: `@gwx/api`, tokens, refresh, the guest guard](#7-the-api-layer-gwxapi-tokens-refresh-the-guest-guard)
8. [Data fetching with TanStack Query](#8-data-fetching-with-tanstack-query)
9. [Routing and pages (React Router)](#9-routing-and-pages-react-router)
10. [Reusable components](#10-reusable-components)
11. [Global UI state with Zustand](#11-global-ui-state-with-zustand)
12. [Styling with Tailwind CSS v4 (the "TechNova" look)](#12-styling-with-tailwind-css-v4-the-technova-look)
13. [Auth end to end](#13-auth-end-to-end)
14. [The storefront, page by page](#14-the-storefront-page-by-page)
15. [The admin app, page by page](#15-the-admin-app-page-by-page)
16. [A TypeScript crash course (only what we use)](#16-a-typescript-crash-course-only-what-we-use)
17. [Debugging playbook](#17-debugging-playbook)
18. [Troubleshooting auth (read this when login fails)](#18-troubleshooting-auth-read-this-when-login-fails)
19. [Glossary](#19-glossary)
20. [Exercises and next steps](#20-exercises-and-next-steps)

---

## 1. How to read this guide

You do **not** need to memorise anything. Read a section, then open the file it
talks about and follow along. The fastest way to learn React is to change one
small thing, save, and watch the browser update (Vite does this instantly).

Conventions in this guide:

- Code you can find in the repo is shown as `path/to/File.tsx`.
- The backend lives in `app/`; the frontends live in `frontend/`.
- "Component" = a function that returns UI. "Hook" = a function starting with
  `use` that adds super-powers.

---

## 2. The big picture: where the frontend sits

Think of a restaurant:

- **Backend (`app/`)** = the kitchen + pantry. It owns the *truth*: prices,
  stock, who you are, what an order costs.
- **Frontend (`frontend/apps/*`)** = the dining room. It shows menus, takes
  your order, and **asks** the kitchen for things.

The rule that never changes:

> **The frontend is untrusted.** Anyone can open DevTools and change what the
> UI "sends". So the frontend never decides prices, totals, or permissions —
> the backend already does. Your job is to send the right shape and display the
> answer.

A single user action looks like this:

```
User clicks "Add to Cart"
        │
        ▼
React component handler runs            (frontend/apps/web/src/components/ProductCard.tsx)
        │
        ▼
api.post("/cart/add", {...})            (frontend/apps/web/src/lib/api.ts -> @gwx/api)
        │  attaches Authorization: Bearer <access_token>
        ▼
FastAPI backend                         (app/routers/cart.py)
        │  validates the JWT, reads/writes Supabase
        ▼
JSON response  ──►  React Query cache   (invalidates ["cart"])
        │
        ▼
Nav bar cart badge re-renders           (frontend/apps/web/src/components/Layout.tsx)
```

Everything in the app is a variation of that loop.

---

## 3. React in ~20 minutes (the only concepts you need)

### 3.1 A component is a function that returns UI

```tsx
function Hello() {
  return <h1>Hello, GWV-xuk!</h1>;
}
```

That `<h1>...</h1>` syntax is **JSX**. It looks like HTML but it is really
JavaScript. Vite compiles it into function calls for you.

### 3.2 Props: inputs passed into a component

```tsx
function Greeting({ name }: { name: string }) {
  return <p>Hi {name}!</p>;
}

<Greeting name="Erickson" />   // renders "Hi Erickson!"
```

`{ name }: { name: string }` means "this component receives one prop called
`name`, and it is a string". This is TypeScript, explained later.

Real example: `ProductCard` receives a whole `product`
(`frontend/apps/web/src/components/ProductCard.tsx`).

### 3.3 State: data that changes over time

```tsx
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);   // count starts at 0
  return <button onClick={() => setCount(count + 1)}>Clicked {count}</button>;
}
```

- `useState(0)` returns a pair: the current value and a setter.
- Calling the setter tells React "re-render this component with the new value".
- **Never edit state directly** (`count++` does nothing). Always use the setter.

Real example: the Shop search box, the quantity stepper on the product page,
and the chat messages in `AiAssistant`.

### 3.4 Effects: run code after render

```tsx
import { useEffect, useState } from "react";

function User() {
  const [user, setUser] = useState(null);
  useEffect(() => {
    // runs once after the first render
    fetch("/auth/me").then(r => r.json()).then(setUser);
  }, []);   // the [] means "run only on mount"
  return <p>{user ? user.email : "Loading…"}</p>;
}
```

We use effects sparingly — mostly to seed form fields from loaded data (see
`ProfilePage` and the checkout form). **Fetching data is usually done by React
Query instead** (section 8), which handles loading/error/caching for you.

### 3.5 Rendering lists (and the `key` rule)

```tsx
{products.map((product) => (
  <ProductCard key={product.id} product={product} />
))}
```

- `.map()` turns an array of data into an array of components.
- Every item needs a stable `key` (usually the database `id`) so React can
  track which item is which when the list changes.

### 3.6 Conditional rendering

```tsx
{isLoading && <Spinner />}
{error ? <ErrorBox /> : <List />}
{token && <WishlistButton />}
```

`&&` means "render the right side only if the left is truthy".

### 3.7Events and controlled inputs

```tsx
const [email, setEmail] = useState("");
<input value={email} onChange={(e) => setEmail(e.target.value)} />
```

Because `value` comes from state and every keystroke updates state, this is a
**controlled input**. Every form in our apps works this way.

### 3.8 Hooks rules (important!)

1. Only call hooks at the **top level** of a component (never inside `if`,
   loops, or nested functions).
2. Only call them from **components** or **other hooks**.

We package shared logic in our own hooks, e.g. `useRequireAuth`
(`frontend/apps/web/src/hooks/useRequireAuth.ts`).

### 3.9 Props down, events up

Data flows **down** via props. Children tell parents what happened by calling a
**function prop** (a callback). This is the single most important mental model
in React.

---

## 4. The stack, and why every tool exists

| Tool | What it does | Why we chose it |
|---|---|---|
| **Vite** | Dev server + production bundler | Instant hot-reload; tiny config |
| **React** | Builds the UI from components | The industry standard |
| **TypeScript** | JavaScript + types | Catches mistakes before you run |
| **React Router** | Maps URLs to pages | `/shop`, `/products/:id`, `/track/:ref` |
| **TanStack Query** | Server-data fetching/caching | Removes ~50% of boilerplate |
| **Zustand** | Tiny global state store | Auth token/user shared everywhere |
| **Tailwind CSS v4** | Utility-first styling | Style without leaving JSX |
| **lucide-react** | Icon set | Clean, consistent icons |
| **sonner** | Toasts | "Added to cart" notifications |
| **clsx** | Conditional class names | `cn("base", active && "on")` |
| **`@gwx/api`** | Our generated typed API client | One source of truth for the API |

The technical writer's summary: **Vite builds, React renders, Router navigates,
Query fetches, Zustand remembers, Tailwind styles, `@gwx/api` talks.**

---

## 5. Project layout

```
frontend/
├── package.json                 # npm workspaces: ["packages/*", "apps/*"]
├── packages/
│   └── api/                     # @gwx/api — generated client (DO NOT EDIT schema.d.ts)
│       └── src/
│           ├── schema.d.ts      # types auto-generated from the backend OpenAPI
│           ├── client.ts        # createApiClient / ApiError
│           └── index.ts         # re-exports (type-only for schema!)
├── apps/
│   ├── web/                     # Customer storefront  → http://localhost:5173
│   └── admin/                   # Admin + WhatsApp CRM → http://localhost:5174
```

Each app is its own Vite project but shares `@gwx/api` through npm workspaces.
That is why `npm install` is run **once** in `frontend/` and links the package
into `node_modules/@gwx/api`.

Inside `apps/web/src`:

| Folder | Purpose |
|---|---|
| `pages/` | One file per route (Home, Shop, Cart…) |
| `components/` | Reusable UI (Layout, ProductCard, AiAssistant…) |
| `hooks/` | Custom hooks (`queries.ts`, `useRequireAuth.ts`) |
| `lib/` | Non-UI helpers: `api.ts`, `types.ts`, `utils.ts` |
| `store/` | Zustand stores (`auth.ts`) |

`apps/admin/src` mirrors this, with `components/AdminGuard.tsx` and
`components/AdminLayout.tsx` added.

---

## 6. Running the apps

From `frontend/`:

```bash
npm install            # once; installs all workspaces (hoisted to frontend/node_modules)

npm run dev:web        # storefront  → http://localhost:5173
npm run dev:admin      # admin       → http://localhost:5174

npm run typecheck      # tsc --noEmit across both apps
npm run build:web      # typecheck + production build
npm run build:admin
```

The backend must be running too (from the repo root):

```bash
source venv/bin/activate
uvicorn app.main:app --reload      # http://127.0.0.1:8000
```

And the repo `.env` must allow the browser origins:

```
CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000"
```

Each app reads `VITE_API_URL` (defaults to `http://127.0.0.1:8000`). See
`apps/web/.env.example`.

---

## 7. The API layer: `@gwx/api`, tokens, refresh, the guest guard

### 7.1 The generated client

`frontend/packages/api/src/client.ts` exports `createApiClient`. It is a tiny
wrapper around `fetch` that:

- prefixes `baseUrl`,
- attaches `Authorization: Bearer <token>` when a token exists,
- serialises JSON bodies (and leaves `FormData` alone so the browser sets the
  multipart boundary),
- throws a typed `ApiError` on non-2xx.

The types in `schema.d.ts` are generated from the backend's OpenAPI. That means
your editor autocompletes endpoints and payloads.

> **Lesson learned (real bug we fixed):** `index.ts` originally did
> `export * from "./schema"`. Because `schema.d.ts` has **only types and no
> runtime code**, the bundler tried to load a file that does not exist at
> runtime and failed. The fix is `export type * from "./schema"`. Rule of
> thumb: if a module is types-only, re-export it with `export type`.

### 7.2 One `api.ts` per app

Both apps have `src/lib/api.ts`. It builds the client with the base URL and
the auth hooks:

```ts
// frontend/apps/web/src/lib/api.ts
export const api = createApiClient({
  baseUrl: API_URL,
  getToken: getAccessToken,                 // reads "access_token" from localStorage
  onUnauthorized: async () => {             // called on any 401
    // try POST /auth/refresh once; if it fails, clear + redirect to /login
  },
});
```

We also create a **bare** client, `authApi`, with no hooks:

```ts
export const authApi = createApiClient({ baseUrl: API_URL });
```

Why two clients? If `authApi` (used for login/refresh) also triggered
`onUnauthorized` on a 401, a failed login could call refresh, which could call
`onUnauthorized` again — an **infinite loop**. The bare client breaks that
cycle.

### 7.3 Token refresh (why 401s heal themselves)

Access tokens expire. When the API returns **401**, `onUnauthorized` runs:

1. If a refresh is already in flight, wait for it (we store it in
   `refreshInFlight`) — this stops ten parallel requests from firing ten
   refreshes.
2. Otherwise, `POST /auth/refresh` with the stored `refresh_token`.
3. On success, save the new tokens and continue.
4. On failure, clear storage and send the browser to `/login`.

### 7.4 The guest-browsing guard

The backend decides what is public. The frontend mirrors it:

- **Public (no token):** products, categories, reviews, delivery locations,
  order tracking.
- **Private:** cart, wishlist, checkout, my orders, profile, reviews (write),
  AI chat.

When a guest clicks **Add to Cart**, **Wishlist**, or **Checkout**, we do not
show an error. We send them to login with a return path:

```ts
// frontend/apps/web/src/hooks/useRequireAuth.ts
if (!token) navigate(`/login?next=${encodeURIComponent(currentPath)}`);
```

After login, `LoginPage` reads `?next=` and returns the user where they meant
to go.

---

## 8. Data fetching with TanStack Query

### 8.1 The idea

React Query is your **server-state cache**. You describe *what data you want*
and *where it comes from*; it gives you `data`, `isLoading`, `error`, retries,
and automatic refetching:

```ts
// frontend/apps/web/src/hooks/queries.ts
export function useProducts(filters: ProductFilters = {}) {
  return useQuery({
    queryKey: ["products", filters],          // the cache identity
    queryFn: async () => {
      const res = await api.get<{ data: Product[] }>("/products/", filters);
      return res.data ?? [];
    },
  });
}
```

**Components, not pages, read the cache.** Hundreds of `ProductCard`s can call
`useWishlist()` and only one network request is made — they share the cache
entry `["wishlist"]`.

### 8.2 Query keys

A query key is the cache's name tag. Change it and you get different data:

- `["products", { brand: "Apple" }]` and `["products", {}]` are separate
  entries.
- `["product", id]` is unique per product.

### 8.3 Mutations and cache invalidation

A **mutation** changes data on the server (POST/PATCH/DELETE). After it
succeeds, we tell React Query which cached queries are now stale:

```ts
const addToCart = useMutation({
  mutationFn: () => api.post("/cart/add", { product_id: product.id, quantity: 1 }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["cart"] });   // refetch the cart
    toast.success("Added to cart");
  },
  onError: (error) => toast.error(errorMessage(error)),
});
```

That is the whole loop: **mutate → invalidate → React refetches → the UI
updates.** No manual "reload" logic anywhere.

### 8.4 Polling for live order status

`useTrackOrder` polls every 3 seconds **only while the status is
`"Pending PIN"`**, then stops:

```ts
refetchInterval: (query) =>
  (query.state.data as Order | undefined)?.status === "Pending PIN" ? 3000 : false,
```

This is how the tracking page updates itself after the M-Pesa prompt.

---

## 9. Routing and pages (React Router)

`App.tsx` declares URL → component mappings:

```tsx
<Routes>
  <Route path="/login" element={<LoginPage />} />     {/* no navbar/footer */}
  <Route element={<Layout />}>                        {/* navbar + footer + AI widget */}
    <Route path="/" element={<HomePage />} />
    <Route path="/shop" element={<ShopPage />} />
    <Route path="/products/:id" element={<ProductDetailPage />} />
    <Route path="/track/:orderRef" element={<OrderTrackingPage />} />
    <Route path="/cart" element={protect(<CartPage />)} />
    ...
  </Route>
</Routes>
```

Two important ideas:

1. **Nested routes.** The `<Route element={<Layout />}>` wraps its children in
   the navbar/footer. Inside `Layout`, `<Outlet />` is where the child page
   renders.
2. **`protect(...)`.** A small helper wraps a page in `<ProtectedRoute>`, which
   checks for a token and redirects to `/login?next=…` if missing.

Reading URL parameters:

```ts
const { id } = useParams();                    // /products/:id
const [params] = useSearchParams();            // /shop?brand=Apple
const navigate = useNavigate();                // programmatic navigation
```

`ShopPage` uses `useSearchParams` so filters survive a refresh and can be
linked (e.g. `HomePage` links to `/shop?brand=Apple`).

---

## 10. Reusable components

### 10.1 `ProductCard` — the heart of the storefront

`frontend/apps/web/src/components/ProductCard.tsx` shows the pattern:
props in, events out, mutations for actions. It:

- shows a badge (`Only X left` when stock ≤ 5, `Best Seller` otherwise),
- has a wishlist heart (`POST /wishlist/` or `DELETE /wishlist/{id}`),
- has an `Add to Cart` pill (`POST /cart/add`),
- guards both actions with `useRequireAuth()`.

### 10.2 `Layout` — the app frame

`frontend/apps/web/src/components/Layout.tsx` renders the sticky navbar,
category dropdown, search, cart/wishlist counts, account menu, footer, and the
floating AI assistant. The counts come straight from the same React Query
cache (`useCart`, `useWishlist`), so they update everywhere automatically.

### 10.3 `ui.tsx` — the admin's shared kit

`frontend/apps/admin/src/components/ui.tsx` collects `Card`, `Modal`,
`Badge`, `Pagination`, `PageLoader`, `EmptyState`, and table cells `Th`/`Td`.
Reusing these keeps every admin screen consistent (rule: *consistency beats
cleverness*).

---

## 11. Global UI state with Zustand

Server data lives in React Query. **Client/auth state** lives in Zustand:

```ts
// frontend/apps/web/src/store/auth.ts
export const useAuthStore = create<AuthState>((set) => ({
  user: getStoredUser(),
  token: getAccessToken(),
  setSession: (session, user) => { saveSession(session, user); set({ token: session.access_token, user }); },
  logout: () => { clearSession(); set({ user: null, token: null }); },
}));
```

Any component can read it with a selector, e.g.
`const token = useAuthStore((s) => s.token)`. On login we `setSession`; on
logout we `logout()` and `queryClient.clear()` so a previous user's cached
cart/wishlist never leaks into the next session.

**When to use which?** Server data → React Query. Ephemeral UI and auth →
Zustand. Don't mix them.

---

## 12. Styling with Tailwind CSS v4 (the "TechNova" look)

Tailwind lets you style with class names instead of separate CSS files:

```tsx
<button className="rounded-full bg-blue-700 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-800">
  Add to Cart
</button>
```

Tailwind v4 is configured **in CSS**, not a JS config file. Look at
`frontend/apps/web/src/index.css`:

```css
@import "tailwindcss";

@theme {
  --color-brand-600: #1565c0;   /* Royal Blue accent */
  --color-brand-700: #0b3578;
  --color-brand-900: #061a40;
}
```

The design tokens we used everywhere:

| Token | Class | Use |
|---|---|---|
| Page canvas | `bg-slate-50` (`#F4F7FB`) | App background |
| Card | `bg-white rounded-2xl shadow-sm border border-slate-100` | Elevated panels |
| Hero gradient | `bg-gradient-to-r from-[#061A40] via-[#0B3578] to-[#1565C0] text-white` | Banners |
| Primary button | `bg-blue-700 hover:bg-blue-800 text-white rounded-full` | CTAs |
| Positive badge | `bg-blue-600 text-white text-xs font-semibold px-2.5 py-1 rounded-full` | New/Best Seller |
| Warning badge | `bg-rose-500 text-white text-xs font-semibold px-2.5 py-1 rounded-full` | Low stock/discount |

`cn()` (from `lib/utils.ts`) merges conditional classes:

```ts
cn("rounded-full px-3 py-1", isActive ? "bg-blue-700 text-white" : "bg-slate-100")
```

---

## 13. Auth end to end

```
SIGNUP                      LOGIN                         PROTECTED REQUEST
──────                      ─────                         ─────────────────
POST /auth/signup           POST /auth/login              GET /cart/
  {email,password}            {email,password}              Authorization: Bearer <access>
        │                          │                             │
        ▼                          ▼                             ▼
Supabase creates user       Supabase verifies          Backend validates JWT
        │                   returns session            (Depends(get_current_user))
        ▼                          │
if "confirm email" OFF:     save access_token +           401?  → onUnauthorized
  session returned          refresh_token in                → POST /auth/refresh
  → auto-login              localStorage                    → retry / or /login
if ON:
  user must click
  the email link first
```

Key files: `lib/api.ts` (tokens + refresh), `store/auth.ts` (state),
`pages/LoginPage.tsx`, `pages/SignupPage.tsx`, `pages/ForgotPasswordPage.tsx`,
`components/ProtectedRoute.tsx`, `hooks/useRequireAuth.ts`.

### Why check `next=`?

A guest clicks "Checkout" on `/checkout` → we send them to
`/login?next=%2Fcheckout`. After a successful login, `LoginPage` navigates to
`next`, so they land exactly where they wanted.

---

## 14. The storefront, page by page

| Page | File | Talks to |
|---|---|---|
| Home | `pages/HomePage.tsx` | `GET /products/` (popular + deals), brand links |
| Shop | `pages/ShopPage.tsx` | `GET /products/` with all filters, `GET /categories/` |
| Product | `pages/ProductDetailPage.tsx` | `GET /products/{id}`, `GET /reviews/{id}`, `POST /cart/add`, `POST /reviews/`, `POST /wishlist/` |
| Cart | `pages/CartPage.tsx` | `GET /cart/`, `PATCH /cart/{id}`, `DELETE /cart/{id}` |
| Checkout | `pages/CheckoutPage.tsx` | `GET /delivery/locations`, `POST /orders/checkout`, `DELETE /cart/` |
| Tracking | `pages/OrderTrackingPage.tsx` | `GET /orders/track/{ref}`, `POST /orders/{id}/cancel` |
| Login/Signup/Forgot | `pages/*Page.tsx` | `/auth/*` |
| Profile | `pages/ProfilePage.tsx` | `GET/PATCH /profiles/me`, `POST /upload/profile-picture` |
| My Orders | `pages/MyOrdersPage.tsx` | `GET /orders/me`, cancel |
| Wishlist | `pages/WishlistPage.tsx` | `GET /wishlist/`, `DELETE /wishlist/{id}`, add to cart |
| AI widget | `components/AiAssistant.tsx` | `POST /ai/chat` |

Checkout deserves a note: **the backend computes the real total.** We display an
estimate (items + selected delivery cost) but send the exact schema
(`phone, email, fulfillment, location_id, delivery_address, payment_method,
items[], total`). After success we go straight to the "waiting for M-Pesa"
state and then to `/track/{order_id}`. We never mark an order "Paid" in the UI —
only the backend/webhook can do that.

---

## 15. The admin app, page by page

| Page | File | Talks to |
|---|---|---|
| Login | `pages/LoginPage.tsx` | `POST /auth/login` then guard check |
| Dashboard | `pages/DashboardPage.tsx` | `GET /admin/dashboard/summary`, `GET /admin/inventory/low-stock`, `PATCH /admin/inventory/{id}` |
| Products | `pages/ProductsPage.tsx` | `GET /admin/products`, `POST /products/` (FormData), `PATCH /admin/products/{id}`, image add/delete, delete |
| Categories | `pages/CategoriesPage.tsx` | `/admin/categories` CRUD |
| Delivery | `pages/DeliveryPage.tsx` | `/admin/delivery-locations` CRUD |
| Orders | `pages/OrdersPage.tsx` | `GET /admin/orders`, `PATCH /admin/orders/{id}/status`, `PATCH /orders/verify-payment/{id}`, `POST /admin/orders/{id}/cancel` |
| Customers | `pages/CustomersPage.tsx` | `GET /admin/customers`, `GET /admin/customers/{id}` |
| Reviews | `pages/ReviewsPage.tsx` | `GET /admin/reviews`, `DELETE /admin/reviews/{id}` |
| Leads CRM | `pages/LeadsPage.tsx` | `GET /admin/leads/stats`, `GET /admin/leads`, `GET /admin/leads/{id}/messages`, `PATCH /admin/leads/{id}`, `POST .../assign`, `POST .../reply` |

### The Admin Guard

`components/AdminGuard.tsx` is the important security-shaped piece:

```ts
// on mount, ask the server "am I an admin?"
api.get("/admin/dashboard/summary")
  .then(() => setStatus("ok"))        // admin confirmed
  .catch(() => setStatus("forbidden")); // 403 → blocked immediately
```

This means **the frontend never decides admin-ness by itself** — it asks the
backend. A 403 shows the "Access denied" screen. (401, from an expired token,
is handled by the refresh logic in `api.ts`.)

### Multipart uploads

Product creation and image upload need `FormData`. The client detects it and
does **not** set `Content-Type`, so the browser adds the multipart boundary:

```ts
const body = new FormData();
body.append("name", form.name);
Array.from(files).forEach((f) => body.append("images", f));
await api.post("/products/", body);
```

---

## 16. A TypeScript crash course (only what we use)

TypeScript is JavaScript plus types. Types vanish when the code runs; their job
is to catch mistakes in your editor and at build time.

```ts
let n: number = 5;                 // primitive types: string, number, boolean, null, undefined
let tags: string[] = ["apple"];    // array of strings

interface Product {                // an object shape
  id: string;
  name: string;
  price: number;
  stock_quantity?: number | null;  // "?" = optional; "| null" = may be null
}

function formatKES(amount: number | null | undefined): string { ... }  // return type after ":"
```

**Union types** describe "one of these":

```ts
type Status = "Paid" | "Processing" | "Cancelled" | "Payment Failed";
```

**Generics** are types with a blank to fill in — that is what the `<T>` in our
API client means:

```ts
api.get<{ data: Product[] }>("/products/")   // "the response has a data: Product[] field"
```

**`unknown` vs `any`:** we use `unknown` for caught errors and narrow it
(`error instanceof ApiError`) before use — safer than `any`.

Where our types live: `frontend/apps/web/src/lib/types.ts` and the same path in
`apps/admin`. They describe the actual JSON the backend returns (which often
differs slightly from the generated OpenAPI types because the FastAPI handlers
return dictionaries).

---

## 17. Debugging playbook

1. **Open the browser Network tab first.** It shows the exact request URL,
   headers (is `Authorization` present?), status code, and response body. Nine
   out of ten frontend bugs are visible here.
2. **CORS errors** (`blocked by CORS policy`) mean the backend's
   `CORS_ORIGINS` does not list your origin. Add
   `http://localhost:5173` / `:5174` and restart uvicorn.
3. **401** → not logged in, or the token expired. Our `api.ts` tries a refresh;
   if that fails you get bounced to `/login`.
4. **403** → logged in but not allowed (this is the admin case).
5. **"Failed to fetch" / status 000** → the backend is not running, or wrong
   `VITE_API_URL`.
6. **Blank screen with a red console error** → often a missing `key`, a null
   value you assumed existed, or a hook called conditionally. Read the stack
   trace; it names the file and line.
7. **`npm run typecheck`** before you commit. It catches most silly mistakes.

Handy commands:

```bash
npm run typecheck                 # from frontend/
curl http://127.0.0.1:8000/health # is the backend up?
curl http://127.0.0.1:8000/products/ | head
```

---

## 18. Troubleshooting auth (read this when login fails)

We actually hit these bugs while building, so they are real. Here is what each
one is and how to fix it.

### 18.1 "I can't create an account"

**Cause:** In Supabase, *email confirmation* is ON. Check the project
(`Auth settings`: `mailer_autoconfirm = false`). When it is on:

- `POST /auth/signup` creates the user but returns **no session** (you must
  confirm your email first).
- If SMTP/Resend is not configured, the confirmation email may never arrive,
  so you can never log in.
- Signing up again with the same email returns "User already registered".

**Fixes (pick one):**

1. **Supabase Dashboard → Authentication → Sign In / Providers → Email → turn
   OFF "Confirm email".** Then signup returns a session and our `SignupPage`
   auto-logs you in. (Easiest for development.)
2. Configure SMTP (your `.env` has `RESEND_API_KEY`) so confirmation emails are
   delivered, then click the link.
3. Have an admin confirm the user from the Supabase dashboard.

> Our `SignupPage` now detects whether a session came back: if yes it logs you
> in, if no it tells you to confirm your email. So after fix #1 the flow is
> seamless.

### 18.2 "I can't log in as admin"

There are **two** gates for admin access (`app/dependencies.py::require_admin`):

1. Your email is listed in `ADMIN_EMAILS` (in the repo `.env`), **or**
2. Your profile is flagged admin in the database.

We found that:

- `.env` had `ADMIN_EMAILS="owner@x-uk.com"`, but the real account was
  `ericksonkinyua681@gmail.com` — so the email gate failed.
- The code looked for a `profiles.role` column, but the actual database has an
  **`is_admin` boolean** (`role` does not exist), so the DB gate failed too.
- The single profile row had `user_id = null` (its `id` held the auth user id),
  so the lookup by `user_id` found nothing anyway.

**What we fixed:**

- `.env` now reads
  `ADMIN_EMAILS="ericksonkinyua681@gmail.com,owner@x-uk.com"`.
- `app/dependencies.py` now checks **both** `role == "admin"` and
  `is_admin == true`, and looks the profile up by `user_id` **or** `id`. So the
  database gate works with either schema.

**After editing `.env`, restart the backend** (env vars are read at boot):

```bash
pkill -f "uvicorn app.main:app"
source venv/bin/activate
uvicorn app.main:app --reload
```

**Optional DB tidy-up** so the profile page works too (the profile endpoints
match on `user_id`, but your row stored the id in `id`):

```sql
-- run once in the Supabase SQL editor
update public.profiles set user_id = id where user_id is null;
```

To grant admin purely in the database instead of via `ADMIN_EMAILS`:

```sql
update public.profiles set is_admin = true where user_id = '<your-auth-uuid>';
```

### 18.3 Checklist

- [ ] Backend running (`curl http://127.0.0.1:8000/health` → `{"status":"ok"}`)?
- [ ] `CORS_ORIGINS` includes your app's origin, backend restarted?
- [ ] Email confirmation handled (section 18.1)?
- [ ] Your email in `ADMIN_EMAILS`, backend restarted (section 18.2)?
- [ ] Logging in to the **correct app** (storefront `:5173` for customers,
      admin `:5174` for admins)?

### 18.4 `500 Internal Server Error` from the API (missing database tables)

If endpoints like `GET /categories/`, `POST /cart/add`, or
`GET /admin/leads/{id}/messages` return **500**, read the JSON `detail` — it
usually says something like:

```json
{"detail": "{'message': \"Could not find the table 'public.categories'...\", 'code': 'PGRST205'}"}
```

That means the table does not exist in Supabase. The live database had drifted
from the backend code: `categories`, `cart_items`, and `whatsapp_messages` were
missing, `leads` had the wrong shape, `products.category_id` was missing, and
`profiles.user_id` was `NULL`.

**Fix:** run `supabase/migrations/005_reconcile_backend_schema.sql` in the
Supabase Dashboard → **SQL Editor**. It creates/reconciles everything the
backend queries and is safe to re-run. (It drops + recreates the empty `leads`
table, so export first if you ever have real leads.)

Quick ways to check whether a table exists:

```bash
curl http://127.0.0.1:8000/categories/      # 200 = good, 500 = table missing
```

---

## 19. Glossary

| Term | Meaning |
|---|---|
| **JSX** | HTML-like syntax inside JS that compiles to function calls |
| **Component** | A function returning UI |
| **Props** | Inputs to a component |
| **State** | Data a component owns and can change (`useState`) |
| **Hook** | A `use*` function adding React features |
| **Render** | React turning your components into DOM |
| **Controlled input** | A form field whose value is state |
| **Route** | A URL mapped to a page |
| **Query key** | The cache identity for a React Query query |
| **Mutation** | A request that changes server data |
| **Invalidate** | Tell React Query a cached query is stale so it refetches |
| **Token** | The JWT proving who you are |
| **Refresh token** | A longer-lived token used to get a new access token |
| **CORS** | Browser rule: the server must allow your origin |
| **FormData** | The browser type for multipart file uploads |
| **Guard** | Code that blocks a route/action until a condition holds |

---

## 20. Exercises and next steps

Small, safe things to try (each teaches one concept):

1. **Props/state:** Add a "Clear filters" button to `ShopPage` that resets the
   URL (`setParams(new URLSearchParams())`).
2. **Lists/keys:** On `HomePage`, change the "Popular" slice from 8 to 4 and
   watch the grid.
3. **Mutations:** Add a "Remove" button to each row on `MyOrdersPage` only for
   `Cancelled` orders (just hide it — no API needed).
4. **Query keys:** Add a `refetchOnWindowFocus: true` option to `useProducts`
   and observe refetches.
5. **Tailwind:** Recolour the primary button using the brand token
   (`bg-[#1565C0]`).
6. **Admin:** Add a "Total Revenue" card variant to `DashboardPage` using
   `summary.total_revenue`.
7. **TypeScript:** Give `Order.status` a union type and see the editor complain
   when you compare it to a typo.

Where to go next:

- Read `docs/FRONTEND_ROADMAP.md` Phase 6 (Expo mobile) — you can reuse
  `@gwx/api`, `types.ts`, and the query hooks, and only rewrite the screens.
- Add react-hook-form + zod for form validation (the roadmap recommends it).
- Add a shared `packages/ui` if the web and admin apps start duplicating
  components.

**The one sentence to remember:** *the frontend asks, the backend decides.* Keep
that straight and the rest is just arranging components.
