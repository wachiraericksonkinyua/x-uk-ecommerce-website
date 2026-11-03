-- Standard electronics categories for the X-UK / GWV storefront.
-- Safe to run repeatedly. The same seed is included in migration 007.

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
