-- 002_add_profiles_role.sql
-- Role column used by app/dependencies.py::require_admin.

alter table public.profiles
    add column if not exists role text not null default 'customer';

-- Only allow known roles
alter table public.profiles drop constraint if exists profiles_role_check;
alter table public.profiles
    add constraint profiles_role_check check (role in ('customer', 'staff', 'admin'));

create index if not exists idx_profiles_role on public.profiles(role);

-- Promote the first admin manually, e.g.:
--   update public.profiles set role = 'admin' where user_id = '<your-auth-user-uuid>';
