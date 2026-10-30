-- 006_add_reviews_is_approved.sql
-- Review moderation: reviews are hidden from the storefront until approved.

alter table public.reviews
    add column if not exists is_approved boolean not null default false;

create index if not exists idx_reviews_is_approved on public.reviews(is_approved);

-- Only approved reviews are world-readable (admins can still read everything).
drop policy if exists "reviews_read_all" on public.reviews;
create policy "reviews_read_all"
  on public.reviews for select
  using (is_approved = true or public.is_admin());
