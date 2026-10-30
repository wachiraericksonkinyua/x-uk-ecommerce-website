-- ============================================================================
-- GWV-xuk  |  Supabase Row Level Security (RLS) policies  --  DRAFT
-- ============================================================================
-- WHY THIS FILE EXISTS
--   Your FastAPI backend already checks who the user is, but anyone holding the
--   public "anon" Supabase key can talk to the database DIRECTLY and bypass your
--   API. RLS is a second lock on the door inside Postgres itself.
--
-- HOW TO USE
--   1. Review every table/policy below (table and column names must match yours).
--   2. Run it in the Supabase SQL Editor (or as a migration).
--   3. The backend uses the SERVICE_ROLE key? -> It bypasses RLS (good for admin
--      work). If it uses the ANON key, make sure policies cover every query.
--
-- KEY CONCEPTS
--   auth.uid()  -> the id of the logged-in user (from the JWT "sub" claim)
--   is_admin()  -> helper we create below, true when profiles.role = 'admin'
--   using       -> condition for SEEING existing rows (SELECT/UPDATE/DELETE)
--   with check  -> condition for WRITING new/changed rows (INSERT/UPDATE)
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 0. Admin helper. SECURITY DEFINER lets it read profiles regardless of RLS.
-- ---------------------------------------------------------------------------
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles
    where user_id = auth.uid()
      and lower(coalesce(role, '')) = 'admin'
  );
$$;


-- ---------------------------------------------------------------------------
-- 1. profiles  (one row per user; user_id = auth.users.id)
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = user_id or public.is_admin());

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
  on public.profiles for insert
  with check (auth.uid() = user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = user_id or public.is_admin())
  with check (auth.uid() = user_id or public.is_admin());


-- ---------------------------------------------------------------------------
-- 2. products  (catalogue: everyone reads, only admins write)
-- ---------------------------------------------------------------------------
alter table public.products enable row level security;

drop policy if exists "products_read_all" on public.products;
create policy "products_read_all"
  on public.products for select
  using (true);

drop policy if exists "products_admin_write" on public.products;
create policy "products_admin_write"
  on public.products for all
  using (public.is_admin())
  with check (public.is_admin());


-- ---------------------------------------------------------------------------
-- 3. product_images  (same idea as products)
-- ---------------------------------------------------------------------------
alter table public.product_images enable row level security;

drop policy if exists "product_images_read_all" on public.product_images;
create policy "product_images_read_all"
  on public.product_images for select
  using (true);

drop policy if exists "product_images_admin_write" on public.product_images;
create policy "product_images_admin_write"
  on public.product_images for all
  using (public.is_admin())
  with check (public.is_admin());


-- ---------------------------------------------------------------------------
-- 4. delivery_locations  (customers read active ones, admins manage all)
-- ---------------------------------------------------------------------------
alter table public.delivery_locations enable row level security;

drop policy if exists "locations_read_active" on public.delivery_locations;
create policy "locations_read_active"
  on public.delivery_locations for select
  using (active = true or public.is_admin());

drop policy if exists "locations_admin_write" on public.delivery_locations;
create policy "locations_admin_write"
  on public.delivery_locations for all
  using (public.is_admin())
  with check (public.is_admin());


-- ---------------------------------------------------------------------------
-- 5. orders  (a user only sees their own; admins see everything)
--    NOTE: writes normally happen from the backend (service role) which
--    bypasses RLS, so we only need to lock down direct client access here.
-- ---------------------------------------------------------------------------
alter table public.orders enable row level security;

drop policy if exists "orders_select_own" on public.orders;
create policy "orders_select_own"
  on public.orders for select
  using (auth.uid() = user_id or public.is_admin());

-- Guests (no login) may place orders through the backend; the backend uses the
-- service role. If you want to allow direct anon inserts, uncomment:
-- create policy "orders_insert_any" on public.orders for insert with check (true);

drop policy if exists "orders_admin_update" on public.orders;
create policy "orders_admin_update"
  on public.orders for update
  using (public.is_admin())
  with check (public.is_admin());

drop policy if exists "orders_admin_delete" on public.orders;
create policy "orders_admin_delete"
  on public.orders for delete
  using (public.is_admin());


-- ---------------------------------------------------------------------------
-- 6. cart_items  (strictly private to the owner)
-- ---------------------------------------------------------------------------
alter table public.cart_items enable row level security;

drop policy if exists "cart_owner_all" on public.cart_items;
create policy "cart_owner_all"
  on public.cart_items for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 7. wishlists  (strictly private to the owner)
-- ---------------------------------------------------------------------------
alter table public.wishlists enable row level security;

drop policy if exists "wishlist_owner_all" on public.wishlists;
create policy "wishlist_owner_all"
  on public.wishlists for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);


-- ---------------------------------------------------------------------------
-- 8. reviews  (everyone reads; a user may only write their own)
-- ---------------------------------------------------------------------------
alter table public.reviews enable row level security;

drop policy if exists "reviews_read_all" on public.reviews;
create policy "reviews_read_all"
  on public.reviews for select
  using (true);

drop policy if exists "reviews_owner_insert" on public.reviews;
create policy "reviews_owner_insert"
  on public.reviews for insert
  with check (auth.uid() = user_id);

drop policy if exists "reviews_owner_update" on public.reviews;
create policy "reviews_owner_update"
  on public.reviews for update
  using (auth.uid() = user_id or public.is_admin())
  with check (auth.uid() = user_id or public.is_admin());

drop policy if exists "reviews_admin_delete" on public.reviews;
create policy "reviews_admin_delete"
  on public.reviews for delete
  using (auth.uid() = user_id or public.is_admin());


-- ---------------------------------------------------------------------------
-- 9. chat_history  (AI assistant conversation: private to the owner)
-- ---------------------------------------------------------------------------
alter table public.chat_history enable row level security;

drop policy if exists "chat_owner_all" on public.chat_history;
create policy "chat_owner_all"
  on public.chat_history for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);


-- ===========================================================================
-- 10. FUTURE TABLES for the WhatsApp triage bot / leads
--     (create these when you build that feature)
-- ===========================================================================
-- alter table public.leads enable row level security;
-- create policy "leads_admin_all" on public.leads for all
--   using (public.is_admin()) with check (public.is_admin());
--
-- alter table public.whatsapp_messages enable row level security;
-- create policy "wa_admin_all" on public.whatsapp_messages for all
--   using (public.is_admin()) with check (public.is_admin());
--
-- alter table public.lead_events enable row level security;
-- create policy "lead_events_admin_all" on public.lead_events for all
--   using (public.is_admin()) with check (public.is_admin());


-- ===========================================================================
-- STORAGE (buckets: product-images, profile-assets)
--   Public read for product images; authenticated users write only into a
--   folder named after their own user id.
-- ===========================================================================
-- create policy "product_images_public_read"
--   on storage.objects for select
--   using (bucket_id = 'product-images');
--
-- create policy "profile_assets_own_folder"
--   on storage.objects for all
--   using (
--     bucket_id = 'profile-assets'
--     and (storage.foldername(name))[1] = auth.uid()::text
--   )
--   with check (
--     bucket_id = 'profile-assets'
--     and (storage.foldername(name))[1] = auth.uid()::text
--   );
