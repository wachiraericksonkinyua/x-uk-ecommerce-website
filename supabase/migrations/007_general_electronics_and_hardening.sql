-- 007_general_electronics_and_hardening.sql
-- ---------------------------------------------------------------------------
-- General electronics catalogue support + admin sales/refund hardening.
--
-- Run after 001..006. Safe to re-run.
-- ---------------------------------------------------------------------------

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- 1. Product technical details
-- ---------------------------------------------------------------------------
alter table public.products
    add column if not exists specs jsonb not null default '{}'::jsonb;

alter table public.products
    add column if not exists compatibility text;

create index if not exists idx_products_specs on public.products using gin (specs);

-- ---------------------------------------------------------------------------
-- 2. Standard electronics categories (idempotent seed)
-- ---------------------------------------------------------------------------
insert into public.categories (name, slug, description, active)
values
    ('Smartphones', 'smartphones', 'New and UK-used smartphones.', true),
    ('Headphones & Earphones', 'headphones-earphones', 'Over-ear, on-ear and in-ear audio.', true),
    ('Chargers & Cables', 'chargers-cables', 'Wall chargers, power adapters and charging cables.', true),
    ('Power Banks', 'power-banks', 'Portable battery packs for travel and everyday power.', true),
    ('Smartwatches & Wearables', 'smartwatches-wearables', 'Smartwatches, fitness bands and wearable tech.', true)
on conflict (name) do update
    set slug = excluded.slug,
        description = excluded.description,
        active = true;

-- ---------------------------------------------------------------------------
-- 3. Order verification / refund metadata
-- ---------------------------------------------------------------------------
alter table public.orders
    add column if not exists is_verified boolean not null default false;
alter table public.orders
    add column if not exists verified_at timestamptz;
alter table public.orders
    add column if not exists verified_by uuid;
alter table public.orders
    add column if not exists verification_note text;

alter table public.orders
    add column if not exists refunded_at timestamptz;
alter table public.orders
    add column if not exists refunded_by uuid;
alter table public.orders
    add column if not exists refund_reason text;
alter table public.orders
    add column if not exists refund_amount numeric;

-- M-Pesa receipts are unique across orders. Empty/NULL values are excluded.
-- If this fails, find duplicates first:
--   select receipt_number, count(*) from public.orders
--   where receipt_number is not null and receipt_number <> ''
--   group by receipt_number having count(*) > 1;
create unique index if not exists idx_orders_receipt_number_unique
    on public.orders (receipt_number)
    where receipt_number is not null and receipt_number <> '';

-- ---------------------------------------------------------------------------
-- 4. Inventory movement ledger (sales + stock alerts + unit history)
-- ---------------------------------------------------------------------------
create table if not exists public.inventory_movements (
    id              uuid primary key default gen_random_uuid(),
    product_id      uuid references public.products(id) on delete set null,
    order_id        uuid references public.orders(id) on delete set null,
    change_qty      integer not null,
    quantity_before integer,
    quantity_after  integer,
    unit_price      numeric,
    reason          text not null,
    note            text,
    created_by      uuid,
    created_at      timestamptz not null default now()
);

create index if not exists idx_inventory_movements_product
    on public.inventory_movements(product_id, created_at desc);
create index if not exists idx_inventory_movements_order
    on public.inventory_movements(order_id);
create index if not exists idx_inventory_movements_created
    on public.inventory_movements(created_at desc);

alter table public.inventory_movements enable row level security;

drop policy if exists "inventory_movements_admin_read" on public.inventory_movements;
create policy "inventory_movements_admin_read"
    on public.inventory_movements for select
    using (public.is_admin());

drop policy if exists "inventory_movements_admin_write" on public.inventory_movements;
create policy "inventory_movements_admin_write"
    on public.inventory_movements for all
    using (public.is_admin())
    with check (public.is_admin());
