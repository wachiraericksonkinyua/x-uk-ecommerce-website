# GWV-xuk / X-UK — Project Overview & Recommendations

> **Last reviewed:** 2026-11-03
> **Scope:** full repository — FastAPI backend, Vue storefront, Vue admin app,
> Supabase schema, payment/WhatsApp integrations, and tests.
>
> **Verification run during this review:**
> - `venv/bin/pytest -q` → **46 tests passed**
> - `npm run typecheck` (both Vue apps) → **passed**
>
> The older docs (`BACKEND_GUIDE.md`, `FRONTEND_ROADMAP.md`, etc.) describe React
> in places, but the actual frontend is **Vue 3 + Vite**. Treat this file as the
> current snapshot.

---

## 1. Executive summary

This is a working e-commerce platform for selling **UK-used smartphones in Kenya**:

- **Backend:** FastAPI + Supabase (Postgres, Auth, Storage).
- **Payments:** Safaricom M-Pesa Daraja STK Push + callback reconciliation.
- **Storefront:** Vue 3 SPA with browsing, cart, wishlist, checkout, tracking,
  profile, reviews, and an AI shopping assistant.
- **Admin:** Vue 3 dashboard for products, orders, categories, delivery zones,
  inventory, customers, review moderation, and WhatsApp lead triage.
- **Automation:** WhatsApp Cloud API webhook + LLM lead qualification
  (`hot` / `warm` / `cold`) with owner notifications.
- **Quality:** service layer, RBAC, idempotent stock release, typed API client,
  46 backend tests, and a clean TypeScript build.

The core business flow (browse → cart → M-Pesa checkout → webhook → order
tracking) is implemented end to end. The biggest remaining risks are around
**public order tracking, manual receipt verification, and non-atomic stock
updates** — see [Known gaps](#8-known-gaps-and-risks).

---

## 2. Technology stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.12, FastAPI 0.142, Uvicorn |
| Database / Auth / Storage | Supabase (`supabase-py`) |
| Validation | Pydantic v2 |
| Payments | Safaricom Daraja (STK Push) |
| Email | Resend |
| AI | OpenRouter (shopping assistant + WhatsApp triage) |
| Messaging | WhatsApp Cloud API (Meta Graph API) |
| Storefront | Vue 3, Vite, TypeScript, Vue Router, Pinia, TanStack Vue Query, Tailwind CSS v4 |
| Admin | Same Vue stack + custom components |
| API client | Generated OpenAPI types (`@gwx/api`) + thin auth-aware fetch wrapper |
| Tests | pytest, in-memory fake Supabase |

---

## 3. High-level architecture

```
Vue storefront (5173) ─┐
Vue admin (5174) ──────┼──► FastAPI /api ──► Supabase (Postgres/Auth/Storage)
                       │        │
Safaricom ─────────────┘        ├──► Daraja (STK Push / status query)
Meta WhatsApp ──────────────────┼──► WhatsApp Cloud API
                                ├──► OpenRouter (LLM)
                                └──► Resend (receipt emails)
```

### Backend structure

```
app/
├── main.py                 # FastAPI app, CORS, router registration
├── database.py             # shared Supabase client
├── dependencies.py         # get_current_user, get_optional_user, require_admin
├── models/review.py
├── routers/
│   ├── auth.py             # signup/login/refresh/logout/reset
│   ├── products.py         # public catalogue + legacy admin writes
│   ├── categories.py       # public categories
│   ├── cart.py             # cart CRUD
│   ├── wishlist.py         # wishlist add/list/remove
│   ├── orders.py           # checkout, tracking, cancel, receipt verify
│   ├── payments.py         # M-Pesa callback
│   ├── reviews.py          # verified-buyer reviews
│   ├── profiles.py         # profile read/upsert/update
│   ├── upload.py           # avatar upload
│   ├── delivery.py         # public delivery locations
│   ├── ai.py               # AI chat endpoint
│   ├── analytics.py        # legacy summary
│   ├── daraja_service.py   # Daraja HTTP client (NOT a router)
│   ├── admin/              # all admin routes behind require_admin
│   └── webhooks/whatsapp.py
├── services/
│   ├── inventory.py        # hold/restore/release stock (idempotent release)
│   ├── mpesa.py            # single STK reconciliation path
│   ├── ai.py               # shared OpenRouter call
│   └── whatsapp.py         # inbound parse, lead scoring, owner alerts
└── utils/
    ├── email.py            # Resend receipts
    └── pagination.py       # clamped page range
```

### Frontend structure

```
frontend/
├── apps/web/               # customer storefront (port 5173)
├── apps/admin/             # admin dashboard (port 5174)
├── packages/api/           # generated OpenAPI types + fetch client
├── openapi.json
└── scripts/generate-api.sh
```

---

## 4. Backend features (implemented)

### 4.1 Authentication & identity

- Email/password signup and login via Supabase Auth.
- `GET /auth/me` — current user identity.
- `POST /auth/refresh` — exchange refresh token.
- `POST /auth/logout` — best-effort token revocation.
- `POST /auth/forgot-password` — anti-enumeration response.
- `POST /auth/reset-password` — supports both `access_token`/`refresh_token`
  and newer `token_hash` OTP recovery links.
- JWT-based dependencies: `get_current_user`, `get_optional_user`.
- Admin authorization via `ADMIN_EMAILS` allowlist or `profiles.role` /
  `profiles.is_admin`.

### 4.2 Catalogue

- Public product list with:
  - search across name, brand, description,
  - category (slug/name/id resolution),
  - brand, color, min/max price,
  - sort by price or creation date, asc/desc.
- Public single product with related images.
- Public categories (active only).
- Public delivery locations (active only).
- Admin product management: paginated list, search, low-stock filter,
  partial update, delete (with storage cleanup), image add/remove.
- Product image upload to Supabase Storage.

### 4.3 Cart & wishlist

- Authenticated cart: add/increment, list with product join, set quantity
  (stock-aware), remove line, clear cart.
- Authenticated wishlist: add, list with product join, remove by product id.

### 4.4 Orders & checkout

- Login-required checkout.
- Delivery or free store pickup.
- Server-side price lookup — client-supplied prices/totals are ignored.
- Server-side stock validation.
- Delivery cost resolved from the database.
- Kenyan phone normalization to `254XXXXXXXXX`.
- Order persisted with `user_id`.
- Short order reference (`GWV-xxxx`).
- Stock decremented with rollback on partial failure.
- M-Pesa STK Push initiated; failure to initiate does **not** fail the order.
- Customer order list (`/orders/me`).
- Customer self-cancel (blocked for shipped/delivered/cancelled).
- Public tracking by reference, with live Daraja status polling while
  `Pending PIN`.
- Customer receipt fallback (`/orders/{id}/verify-receipt`).
- Legacy/admin order status and payment verification routes.

### 4.5 Payments

- Daraja service: OAuth token, STK push, STK status query, transaction check.
- Single reconciliation function (`services/mpesa.py`) shared by:
  - `POST /payments/callback`,
  - legacy `POST /orders/status-result`,
  - tracking poll.
- Handles string/int `ResultCode` mismatch.
- `ResultCode 0` → Paid + receipt saved + email.
- `ResultCode 1032` → Cancelled + stock restored.
- Other failures → Payment Failed + stock restored.
- Idempotent success transition (won't overwrite an already-Paid order).
- Idempotent stock release (status-guarded update).

### 4.6 Reviews

- Only logged-in users.
- Verified-buyer check against order history.
- Rating constrained to 1–5.
- New reviews default to unapproved.
- Public listing returns only approved reviews.
- Admins can list all, approve/hide, or delete.

### 4.7 Profiles & uploads

- `GET /profiles/me`, `POST /profiles/me` (upsert), `PATCH /profiles/me`.
- Profile fields: name, phone, address, avatar, banner, date of birth.
- Avatar upload stored under the authenticated user's folder.

### 4.8 AI shopping assistant

- Authenticated `POST /ai/chat`.
- Loads product catalogue into the system prompt.
- Stores user/assistant messages in `chat_history`.
- Uses the last 6 messages as context.
- Returns the raw OpenRouter completion to the frontend.

### 4.9 Admin API (`/admin/*`, admin-only at the parent router)

| Area | Capabilities |
|---|---|
| Dashboard | Revenue (total/daily), order counts, pending orders, customer count, low-stock list |
| Orders | Paginated/filterable/searchable list, detail, status update, cancel with stock restore |
| Products | Paginated list, search, low-stock filter, detail, update, delete + storage cleanup, image add/remove |
| Categories | List, create with auto-slug, update, delete |
| Customers | Paginated/searchable list, profile + order history, role update (`admin`/`staff`/`customer`) |
| Inventory | Low-stock report, set absolute stock |
| Delivery | List, create, update, delete locations |
| Reviews | Paginated list, approve/hide, delete |
| Leads | Stats/funnel, paginated/searchable list, detail, message transcript, update, manual WhatsApp reply, assignment |

### 4.10 WhatsApp lead triage bot

- `GET /webhooks/whatsapp` — Meta verification challenge.
- `POST /webhooks/whatsapp` — HMAC-SHA256 signature verification
  (`X-Hub-Signature-256`) when `WHATSAPP_APP_SECRET` is configured.
- Fast acknowledgement + background processing.
- Parses Meta's nested payload.
- Creates/updates leads by phone number.
- Stores full inbound/outbound message transcript.
- Uses an LLM to ask one qualifying question at a time.
- LLM returns structured JSON with intent, interest, budget, timeline,
  location, score, and stage.
- Score is clamped to 0–100 and mapped to `hot` / `warm` / `cold`.
- Notifies the owner once when a lead becomes hot.
- Admin can send manual replies from the dashboard.

### 4.11 Data / schema

Migrations in `supabase/migrations/`:

- `001_create_categories.sql`
- `002_add_profiles_role.sql`
- `003_create_leads.sql` (leads, messages, events, updated-at trigger)
- `004_rls_new_tables.sql` (admin helper + RLS for new tables)
- `005_reconcile_backend_schema.sql`
- `006_add_reviews_is_approved.sql`

Plus `supabase/rls_policies.sql` for Row Level Security.

---

## 5. Storefront features (Vue app)

| Route | Feature |
|---|---|
| `/` | Hero, animated product marquee, trust badges, popular products, brand shortcuts, best deals, WhatsApp CTA |
| `/shop` | Product grid with URL-synced search, category, brand, color, price range, sorting, mobile filter drawer |
| `/products/:id` | Image gallery, price, stock state, quantity picker, add to cart, wishlist, average rating, review list, review form |
| `/cart` | Authenticated cart with quantity controls, remove, totals |
| `/checkout` | Delivery/pickup, location + address, email/phone, M-Pesa STK flow, success/waiting state, auto-redirect to tracking |
| `/track` and `/track/:orderRef` | Public order lookup, status progress timeline, items, delivery details, receipt verification, cancellation |
| `/login`, `/signup` | Authentication |
| `/forgot-password`, `/reset-password` | Full password reset flow |
| `/profile` | Profile editing, avatar |
| `/orders` | My orders |
| `/wishlist` | Saved products |
| global | Floating AI assistant, toast notifications, route guards with `?next=` redirect |

---

## 6. Admin dashboard features (Vue app)

| Route | Feature |
|---|---|
| `/login` | Admin login |
| `/` | KPI cards (daily revenue, pending orders, low stock, customers) + inline restock table |
| `/orders` | Search/filter/paginate, order detail, status updates, verify payment, cancel |
| `/products` | Search, low-stock filter, pagination, create/edit/delete, image manager |
| `/categories` | Category CRUD |
| `/delivery` | Delivery location CRUD |
| `/customers` | Search/paginate, customer detail with orders, role management |
| `/reviews` | Moderation queue, approve/hide/delete |
| `/leads` | WhatsApp CRM: funnel stats, lead list, conversation transcript, manual reply, assignment |

`AdminGuard.vue` verifies admin access by calling
`GET /admin/dashboard/summary` before rendering the dashboard.

---

## 7. Testing & quality status

### What is covered

- **46 pytest tests**, all passing.
- Test areas:
  - pagination clamping,
  - inventory restore correctness + idempotency,
  - WhatsApp scoring, JSON parsing, payload extraction, signature validation,
  - security boundaries (guests blocked from cart/wishlist/checkout/admin),
  - M-Pesa reconciliation (string/int codes, stale callbacks, cancellation),
  - reviews moderation visibility,
  - password reset token handling,
  - receipt verification stock behavior,
  - checkout resilience when Daraja times out.
- In-memory fake Supabase means tests run fast without network.
- Both Vue apps pass `vue-tsc --noEmit`.

### What is not covered

- No frontend unit/component tests.
- No browser E2E tests (Playwright/Cypress).
- No live Supabase integration tests.
- No load/performance tests.
- No CI workflow (`.github/workflows` missing).
- No Python lint/type gate (`ruff`, `mypy`) or frontend lint (ESLint).

---

## 8. Known gaps and risks

### 🔴 P0 — fix before taking real traffic/money

| # | Risk | Where | Why it matters |
|---|---|---|---|
| 1 | **Public tracking leaks PII** | `app/routers/orders.py` → `GET /orders/track/{order_ref}` | Returns the full order row (`customer_email`, `customer_phone`, `delivery_address`, `user_id`) to anyone with a reference. References are only `GWV-` + first 4 hex chars, so they are short and guessable/enumerable. |
| 2 | **Receipt verification trusts the client** | `POST /orders/{order_id}/verify-receipt` | Anyone can mark an order Paid with an arbitrary receipt string. There is no authentication/ownership check, no Daraja verification, and no uniqueness check on receipts. This is a direct payment-bypass path. |
| 3 | **Admin payment verification does not verify** | `PATCH /orders/verify-payment/{order_id}` | The Daraja `check_transaction` call is commented out; the endpoint simply flips the order to `Paid`. An admin mistake or compromised admin account becomes free orders. |
| 4 | **Order reference collisions** | `orders.py` checkout | `order_uuid[:4]` gives only 65,536 combinations. As order volume grows, duplicate `order_reference` values are likely; tracking/verification then become ambiguous. Needs a longer reference + DB unique constraint. |

### 🟠 P1 — fix soon

| # | Risk | Where | Recommendation |
|---|---|---|---|
| 5 | **Non-atomic stock updates** | `orders.py` checkout, `services/inventory.py` | Checkout does read → compute → write per line. Two concurrent buyers can oversell. Move stock hold/release into a Postgres RPC/transaction with row locks and a stock constraint. |
| 6 | **No checkout idempotency** | `POST /orders/checkout` | A retried request can create duplicate orders and duplicate STK pushes. Accept an idempotency key and return the existing order. |
| 7 | **Search filter injection** | `products.py` `.or_(...)`, admin search | User text is interpolated into PostgREST filter syntax. Commas/parentheses can alter the query. Strip/escape filter metacharacters or use structured filters. |
| 8 | **Cart add does not validate stock/product** | `app/routers/cart.py` | Users can add arbitrary product ids or quantities beyond stock. Checkout catches some of it, but the cart should validate at write time. |
| 9 | **Admin product create ignores fields** | `CreateProductModal.vue` + `POST /products/` | The modal collects `category_id` and `stock_quantity` but never appends them; the backend endpoint does not accept them. New products silently start with no category and default stock. |
| 10 | **Weak password/rate-limit policy** | `auth.py` | Signup has no password length/strength check; reset requires 8+. No login/OTP/AI/checkout rate limiting or lockout. Add per-IP + per-account throttling. |
| 11 | **No upload size/type enforcement** | `upload.py`, `admin/products.py` | Files are read fully into memory and accepted based on filename/content type. Enforce max size, allowlist image MIME types, and verify magic bytes. |
| 12 | **Non-M-Pesa payment methods accepted** | `orders.py` checkout | Any `payment_method` string is accepted; non-M-Pesa orders are marked “Processing” without collecting money. Restrict to M-Pesa or implement COD/invoice flows. |
| 13 | **Review eligibility is loose** | `reviews.py` | A user only needs an order containing the product — even if the order is failed/cancelled. Require `Paid`/`Delivered`. |

### 🟡 P2 — quality and scale

| # | Area | Recommendation |
|---|---|---|
| 14 | Public catalogue pagination | `GET /products/` returns every row. Add limit/offset or cursor pagination and only the fields the grid needs. |
| 15 | Frontend performance | Add pagination/infinite scroll, image `srcset`, lazy loading, and response caching. |
| 16 | SEO | Vite SPA has no SSR/prerender. Consider Nuxt/prerender for product pages, plus meta tags, canonical URLs, sitemap, robots.txt, structured data. |
| 17 | Observability | Add structured logging, request IDs, Sentry (backend + frontend), and alerting for payment/webhook failures. |
| 18 | CI/CD | Add GitHub Actions: `pytest`, `ruff`, `mypy`, `npm run typecheck`, `npm run build:web`, `npm run build:admin`. |
| 19 | E2E tests | Playwright happy paths: signup → browse → cart → checkout (mock Daraja) → track; admin login → product create → order status. |
| 20 | Docs accuracy | `FRONTEND_ROADMAP.md` and `BACKEND_GUIDE.md` still describe React and some endpoints as “missing”. Update them to match the Vue implementation. |
| 21 | AI cost/abuse | Rate-limit `/ai/chat`, cap history/tokens, add a system-prompt injection guard, and use KES (not `$`) in the product context. |
| 22 | Data model cleanup | `profiles.role` vs `profiles.is_admin` fallbacks are defensive but messy. Pick one schema, migrate, and remove the fallback logic. |
| 23 | Product variants | Smartphones usually need storage/RAM/condition variants. Current model is one product row per configuration. |
| 24 | Coupons & promotions | No discount codes, automatic promotions, or referral tracking. |
| 25 | Addresses | Single free-text address field; add a reusable address book. |
| 26 | Refunds/returns | No refund workflow, return requests, or restocking audit trail. |
| 27 | Notifications | Only a paid-receipt email. Add order confirmation, shipped/delivered emails, and SMS/WhatsApp updates. |

### 🟢 P3 — growth / later

- Mobile app (Expo/React Native) sharing `packages/api`.
- PWA/offline shell.
- Multi-currency / multi-region support.
- Product recommendations and recently viewed.
- Stock alerts for wishlist items.
- Advanced analytics: conversion funnel, top products, cohort/repeat buyers, per-location revenue.
- Multi-admin audit log for sensitive actions (price changes, refunds, role changes).
- Automated database backups and restore drills.

---

## 9. Recommended roadmap

### Week 1 — secure the money paths
1. Redact public tracking responses and generate longer, unique order references
   (`GWV-XXXXXXXX`) with a DB unique index.
2. Add auth + ownership to receipt verification.
3. Verify receipts server-to-server with Daraja; reject duplicate receipt numbers.
4. Fix admin `verify-payment` to actually verify before marking Paid.
5. Add an audit record for every manual payment/status change.

### Weeks 2–3 — correctness & abuse resistance
6. Move stock hold/release into a Postgres transaction/RPC.
7. Add checkout idempotency keys.
8. Add rate limiting to auth, checkout, AI, and webhooks.
9. Sanitize all PostgREST search filters.
10. Validate cart writes against product existence/stock.
11. Fix admin product creation to persist category, stock, and images.
12. Enforce upload size/type limits.

### Weeks 4–5 — launch quality
13. Add CI (tests + lint + typecheck + builds).
14. Add Sentry + structured logs.
15. Add Playwright E2E for the purchase and admin flows.
16. Add public catalogue pagination and image optimization.
17. Update all documentation to the Vue implementation.

### Next quarter — growth
18. Coupons, address book, refunds/returns, order notifications.
19. SEO/SSR and PWA.
20. Analytics and conversion tracking.
21. Product variants and recommendation engine.
22. Mobile app.

---

## 10. How to run

### Backend

```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Swagger UI: http://127.0.0.1:8000/docs
```

Required env: `SUPABASE_URL`, `SUPABASE_KEY`.
Optional: `ADMIN_EMAILS`, `CORS_ORIGINS`, `DARAJA_*`, `RESEND_API_KEY`,
`OPENROUTER_API_KEY`, `WHATSAPP_*`, `OWNER_WHATSAPP_NUMBER`.
See `.env.example`.

### Storefront & admin

```bash
cd frontend
npm install
npm run dev:web      # http://localhost:5173
npm run dev:admin    # http://localhost:5174
npm run typecheck
npm run build:web
npm run build:admin
```

### Tests

```bash
venv/bin/pytest -q
venv/bin/pytest tests/test_inventory.py -v
```

### Database

Run migrations in order in the Supabase SQL editor:

```
001_create_categories.sql
002_add_profiles_role.sql
003_create_leads.sql
004_rls_new_tables.sql
005_reconcile_backend_schema.sql
006_add_reviews_is_approved.sql
rls_policies.sql
```

---

## 11. Suggested next task

Start with **P0 items 1–4** in `app/routers/orders.py` and
`app/routers/admin/orders.py`. They are small, localized changes that close the
most serious money/privacy holes before any marketing or real customer traffic.

After that, add regression tests for:
- a guest/stranger cannot verify someone else's receipt,
- a duplicate receipt cannot mark two orders Paid,
- tracking never returns email/phone/address,
- two concurrent checkouts cannot oversell the last unit.

Those tests will lock in the fixes the same way the existing 46 tests protect
the earlier security work.
