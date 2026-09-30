-- BidGuard AI frontend/admin workflow migration
-- Run once in Supabase SQL Editor. Safe to run more than once.

alter table public.tenders
  add column if not exists reference text,
  add column if not exists tender_value numeric,
  add column if not exists bidder_type text,
  add column if not exists deadline timestamptz,
  add column if not exists requirements jsonb default '[]'::jsonb;

alter table public.users
  add column if not exists mobile_number text,
  add column if not exists business_name text,
  add column if not exists bidder_id text;

create unique index if not exists users_username_unique_idx
  on public.users(username);

create unique index if not exists users_mobile_number_unique_idx
  on public.users(mobile_number)
  where mobile_number is not null and mobile_number <> '';
