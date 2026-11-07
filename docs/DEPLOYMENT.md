# Deployment: Render (API) + Vercel (storefront & admin)

This repo deploys as three pieces:

| Piece | Platform | Source |
|---|---|---|
| FastAPI backend | Render Web Service | repo root (`render.yaml`) |
| Customer storefront | Vercel Project | `frontend/` → `apps/web` |
| Admin dashboard | Vercel Project | `frontend/` → `apps/admin` |

Supabase remains your database/auth/storage provider. Nothing needs to move.

---

## 1. Before deploying

1. Run the missing SQL in **Supabase → SQL Editor**:
   - `supabase/migrations/006_add_reviews_is_approved.sql`
   - `supabase/migrations/009_order_reference_uniqueness.sql`
2. Push this repo to GitHub (Render and Vercel deploy from Git).
3. Make sure `.env` is **not** committed. It is already in `.gitignore`.

---

## 2. Backend on Render

### Blueprint (recommended)

1. Render Dashboard → **New → Blueprint**.
2. Connect this repository. Render reads `render.yaml`.
3. Fill in every value marked `sync: false`:
   - `SUPABASE_URL`, `SUPABASE_KEY` (service-role key)
   - `CORS_ORIGINS` (add later after Vercel URLs exist)
   - `ADMIN_EMAILS`
   - Daraja / Resend / OpenRouter / WhatsApp credentials
4. Deploy. The service name is `gwx-xuk-api`, so the URL will look like:
   `https://gwx-xuk-api.onrender.com`

### Manual equivalent (if you skip the Blueprint)

- Environment: **Python 3**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

### After the first deploy

Set these to the real Render URL:

```env
DARAJA_CALLBACK_URL=https://gwx-xuk-api.onrender.com/payments/callback
```

Then update Safaricom/Daraja with that same callback URL.

> **Free plan note:** Render free web services sleep after 15 minutes without
> inbound traffic and take ~1 minute to wake. Keep-alive below prevents that.

---

## 3. Frontend on Vercel (two projects)

Create **two separate Vercel projects** from the same repository.

For **both** projects use:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Install Command | `npm install` |
| Framework Preset | Vite |

### Project A — Storefront

| Setting | Value |
|---|---|
| Build Command | `npm run build:web` |
| Output Directory | `apps/web/dist` |
| Environment Variable | `VITE_API_URL=https://gwx-xuk-api.onrender.com` |

### Project B — Admin

| Setting | Value |
|---|---|
| Build Command | `npm run build:admin` |
| Output Directory | `apps/admin/dist` |
| Environment Variables | `VITE_API_URL=https://gwx-xuk-api.onrender.com` |
| | `VITE_STOREFRONT_URL=https://your-storefront.vercel.app` |

`frontend/vercel.json` handles SPA routing (deep links like `/track/GWV-…` and
`/orders` work on refresh) and long-term caching for hashed assets.

> **Important:** `VITE_API_URL` is baked in at build time. If you change it,
> redeploy the Vercel project.

---

## 4. Wire CORS and redeploy

Once both Vercel projects are live, go back to Render → Environment and set:

```env
CORS_ORIGINS=https://your-storefront.vercel.app,https://your-admin.vercel.app
```

Use the exact origins, including `https://`, with **no trailing slash**.
Add custom domains too if you attach any. Save → Render redeploys automatically.

Then verify:

```bash
curl https://gwx-xuk-api.onrender.com/health
# {"status":"ok"}
```

---

## 5. Keep-alive (prevents Render free sleep)

The workflow `.github/workflows/keep-alive.yml` pings `/health` every 10 minutes.

1. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `BACKEND_URL`
3. Value: `https://gwx-xuk-api.onrender.com`
4. Open the **Actions** tab → **Keep backend awake** → **Run workflow** once to test.

Notes:

- GitHub cron runs every 10 minutes but can be delayed a few minutes. That is
  fine because Render only sleeps after 15 minutes of no traffic.
- A single always-awake free service uses roughly 730 of the 750 monthly free
  instance hours. Keep an eye on the Render billing page if you run more than
  one free service.
- Alternatives: UptimeRobot (free, 5-minute checks) or cron-job.org. Any of them
  pointing at `https://your-api.onrender.com/health` works.
- `workflow_dispatch` is included so you can trigger a manual ping.

---

## 6. Custom domains (optional)

| Platform | Where |
|---|---|
| Render | Service → Settings → Custom Domains |
| Vercel | Project → Settings → Domains |

After adding domains, update `CORS_ORIGINS` on Render and redeploy.

---

## 7. Post-deploy checklist

- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] Storefront loads products from Render
- [ ] Admin login works at the admin Vercel URL
- [ ] Admin dashboard shows revenue/recent orders
- [ ] Create a test product, then delete it
- [ ] Checkout creates an order and triggers the M-Pesa prompt
- [ ] Daraja callback URL points at `https://<render-url>/payments/callback`
- [ ] CORS has both Vercel origins and no trailing slash
- [ ] Keep-alive workflow has run successfully
- [ ] `006` and `009` SQL migrations are applied

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser shows a CORS error | Add the exact Vercel origin to `CORS_ORIGINS` on Render; redeploy |
| Frontend calls `127.0.0.1:8000` in production | `VITE_API_URL` missing at build time; set it and redeploy |
| Admin gets 403 | Email missing from `ADMIN_EMAILS` and `profiles.role` is not `admin` |
| Reviews fail with `is_approved` error | Run migration `006` |
| Order tracking broken | Run migration `009` after removing any duplicate references |
| First request after idle takes ~1 min | Expected on Render free; keep-alive prevents it |
