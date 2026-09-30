-- Run this once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run

create table if not exists government_records (
  source     text not null,          -- GST, PAN, UDYAM, EPFO, ESIC, MCA, TURNOVER, OEM, MAKE_IN_INDIA, ITR
  identifier text not null,          -- GSTIN, PAN number, Udyam number, CIN ...
  data       jsonb not null,         -- e.g. {"status":"ACTIVE","legal_name":"..."}
  updated_at timestamptz default now(),
  primary key (source, identifier)
);

create table if not exists blacklist (
  identifier text primary key,       -- store UPPERCASE: PAN number or company name
  reason     text,
  added_at   timestamptz default now()
);

-- Lock the tables down: only the backend (service_role key) may read them.
alter table government_records enable row level security;
alter table blacklist enable row level security;
