-- 003_create_leads.sql
-- Tables for the WhatsApp triage bot: leads, message transcript, event log.

create extension if not exists "pgcrypto";

create table if not exists public.leads (
    id              uuid primary key default gen_random_uuid(),
    phone           text not null unique,
    name            text,
    source          text default 'whatsapp',
    interest        text,
    budget          numeric,
    location        text,
    timeline        text,
    status          text not null default 'new',
    score           integer not null default 0,
    assigned_to     uuid,
    last_message_at timestamptz,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

alter table public.leads drop constraint if exists leads_status_check;
alter table public.leads
    add constraint leads_status_check
    check (status in ('new', 'warm', 'hot', 'cold', 'won', 'lost'));

create index if not exists idx_leads_status on public.leads(status);
create index if not exists idx_leads_score on public.leads(score desc);
create index if not exists idx_leads_assigned on public.leads(assigned_to);

create table if not exists public.whatsapp_messages (
    id            uuid primary key default gen_random_uuid(),
    lead_id       uuid not null references public.leads(id) on delete cascade,
    direction     text not null check (direction in ('inbound', 'outbound')),
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

-- Keep leads.updated_at fresh
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
