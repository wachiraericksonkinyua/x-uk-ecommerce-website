-- 004_rls_new_tables.sql
-- Row Level Security for the new tables. Includes the is_admin() helper so this
-- migration is self-contained even if rls_policies.sql has not been run.

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.profiles
    where user_id = auth.uid() and lower(coalesce(role, '')) = 'admin'
  );
$$;

-- categories: public read (active), admin write
alter table public.categories enable row level security;

drop policy if exists "categories_read_active" on public.categories;
create policy "categories_read_active"
    on public.categories for select
    using (active = true or public.is_admin());

drop policy if exists "categories_admin_write" on public.categories;
create policy "categories_admin_write"
    on public.categories for all
    using (public.is_admin())
    with check (public.is_admin());

-- leads / whatsapp_messages / lead_events: admins only
alter table public.leads enable row level security;
drop policy if exists "leads_admin_all" on public.leads;
create policy "leads_admin_all"
    on public.leads for all
    using (public.is_admin())
    with check (public.is_admin());

alter table public.whatsapp_messages enable row level security;
drop policy if exists "wa_messages_admin_all" on public.whatsapp_messages;
create policy "wa_messages_admin_all"
    on public.whatsapp_messages for all
    using (public.is_admin())
    with check (public.is_admin());

alter table public.lead_events enable row level security;
drop policy if exists "lead_events_admin_all" on public.lead_events;
create policy "lead_events_admin_all"
    on public.lead_events for all
    using (public.is_admin())
    with check (public.is_admin());
