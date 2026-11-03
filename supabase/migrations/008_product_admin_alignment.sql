-- 008_product_admin_alignment.sql
-- Make admin product creation/editing self-contained:
--   * products.image_url stores the primary image
--   * existing gallery images backfill image_url where missing
--   * existing products with no category are mapped to a category
--
-- Safe to re-run after migration 007.

alter table public.products
    add column if not exists image_url text;

-- Use the first gallery image as the legacy primary image.
update public.products p
set image_url = gallery.image_url
from (
    select distinct on (product_id) product_id, image_url
    from public.product_images
    where image_url is not null and image_url <> ''
    order by product_id, id
) as gallery
where p.id = gallery.product_id
  and (p.image_url is null or p.image_url = '');

-- Ensure the default phone category exists before backfilling.
insert into public.categories (name, slug, description, active)
values ('Smartphones', 'smartphones', 'New and UK-used smartphones.', true)
on conflict (name) do update
    set slug = excluded.slug,
        active = true;

-- Match any existing category text to a real category row first.
update public.products p
set category_id = c.id,
    category = c.name
from public.categories c
where p.category_id is null
  and p.category is not null
  and (
      lower(trim(p.category)) = lower(c.name)
      or lower(trim(p.category)) = lower(c.slug)
  );

-- Default unclassified phone rows (and truly blank rows) to Smartphones.
update public.products p
set category_id = c.id,
    category = c.name
from public.categories c
where p.category_id is null
  and c.name = 'Smartphones'
  and (
      p.category is null
      or trim(p.category) = ''
      or p.category ilike '%phone%'
      or p.category ilike '%mobile%'
      or p.category ilike '%smartphone%'
  );
