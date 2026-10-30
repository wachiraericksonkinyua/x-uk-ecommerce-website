-- 005_reconcile_backend_schema.sql
-- ---------------------------------------------------------------------------
-- The live Supabase project had drifted from what the backend code expects.
-- Symptoms this fixes:
--   * GET /categories/                          -> 500 (table missing)
--   * POST /cart/add                            -> 500 (table missing)
--   * GET /admin/leads/{id}/messages            -> 500 (table missing)
--   * WhatsApp triage bot could not save leads  -> `leads` had the wrong shape
--   * Admin product create/edit w/ category_id  -> column missing
--   * GET /profiles/me                          -> 404 (profiles.user_id NULL)
--
-- Safe to re-run. At the time of writing `public.leads` held 0 rows, so the
-- DROP + recreate below loses nothing. If you have real leads, export them
-- first (or comment out section 3 and migrate the columns manually).
--
-- Run this in: Supabase Dashboard -> SQL Editor -> paste -> Run.
-- ---------------------------------------------------------------------------

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- 1. Categories  (storefront + admin + products.category_id)
-- ---------------------------------------------------------------------------
create table if not exists public.categories (
    id          uuid primary key default gen_random_uuid(),
    name        text not null unique,
    slug        text not null unique,
    description text,
    image_url   text,
    active      boolean not null default true,
    created_at  timestamptz not null default now()
);

alter table public.products
    add column if not exists category_id uuid references public.categories(id) on delete set null;

create index if not exists idx_products_category_id on public.products(category_id);

-- ---------------------------------------------------------------------------
-- 2. Cart items  (POST/GET/PATCH/DELETE /cart/*)
--    The FK to products is REQUIRED so PostgREST can embed products(*).
-- ---------------------------------------------------------------------------
create table if not exists public.cart_items (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null,
    product_id uuid not null references public.products(id) on delete cascade,
    quantity   integer not null default 1 check (quantity > 0),
    created_at timestamptz not null default now()
);
create index if not exists idx_cart_items_user on public.cart_items(user_id);

-- ---------------------------------------------------------------------------
-- 3. WhatsApp triage: leads + transcript  (used by app/services/whatsapp.py
--    and the /admin/leads endpoints)
-- ---------------------------------------------------------------------------
drop table if exists public.whatsapp_messages cascade;
drop table if exists public.leads cascade;

create table public.leads (
    id              uuid primary key default gen_random_uuid(),
    phone           text not null unique,
    name            text,
    source          text default 'whatsapp',
    interest        text,
    budget          numeric,
    location        text,
    timeline        text,
    status          text not null default 'new'
        check (status in ('new','warm','hot','cold','won','lost')),
    score           integer not null default 0 check (score between 0 and 100),
    assigned_to     uuid,
    last_message_at timestamptz,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);
create index if not exists idx_leads_status on public.leads(status);
create index if not exists idx_leads_score on public.leads(score desc);

create table public.whatsapp_messages (
    id            uuid primary key default gen_random_uuid(),
    lead_id       uuid not null references public.leads(id) on delete cascade,
    direction     text not null check (direction in ('inbound','outbound')),
    body          text not null,
    wa_message_id text,
    created_at    timestamptz not null default now()
);
create index if not exists idx_wa_messages_lead on public.whatsapp_messages(lead_id, created_at);

create table if not exists public.lead_events (
    id         uuid primary key default gen_random_uuid(),
    lead_id    uuid not null references public.leads(id) on delete cascade,
    type       text not null,
    payload    jsonb,
    created_at timestamptz not null default now()
);
create index if not exists idx_lead_events_lead on public.lead_events(lead_id, created_at);

-- keep leads.updated_at fresh on every update
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_leads_updated_at on public.leads;
create trigger trg_leads_updated_at
    before update on public.leads
    for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 4. Reconcile profiles  (backend matches on profiles.user_id = auth user id)
-- ---------------------------------------------------------------------------
update public.profiles set user_id = id where user_id is null;

-- Optional: grant admin directly in the DB (the backend also reads is_admin)
-- update public.profiles set is_admin = true where user_id = '<your-auth-uuid>';

-- ---------------------------------------------------------------------------
-- 5. Optional starter categories (uncomment to seed)
-- ---------------------------------------------------------------------------
-- insert into public.categories (name, slug) values
--     ('Smartphones', 'smartphones'),
--     ('Accessories', 'accessories'),
--     ('Tablets', 'tablets')
-- on conflict (name) do nothing;
