-- 001_create_categories.sql
-- Product categories, plus a nullable FK on products so the existing text
-- `products.category` column keeps working while you migrate to ids.

create extension if not exists "pgcrypto";

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
