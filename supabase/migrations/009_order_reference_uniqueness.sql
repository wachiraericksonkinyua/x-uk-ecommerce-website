-- 009_order_reference_uniqueness.sql
-- ---------------------------------------------------------------------------
-- Order references must be unique.
--
-- New references use 8 hex characters ("GWV-A1B2C3D4"), but older rows may
-- have shorter values and duplicates. This migration:
--   1. reports any existing duplicates (no-op when clean),
--   2. adds a partial unique index so duplicates can never be inserted again.
--
-- Safe to re-run. If step 2 fails, resolve the duplicates shown by step 1
-- first (e.g. append a suffix to the older rows).
-- ---------------------------------------------------------------------------

-- 1. Inspect duplicates (this SELECT returns nothing when the data is clean).
select order_reference, count(*)
from public.orders
where order_reference is not null and order_reference <> ''
group by order_reference
having count(*) > 1;

-- 2. Enforce uniqueness for all non-empty references.
create unique index if not exists idx_orders_order_reference_unique
    on public.orders (order_reference)
    where order_reference is not null and order_reference <> '';

-- 3. Helpful index for the public tracking lookup.
create index if not exists idx_orders_order_reference
    on public.orders (order_reference);
