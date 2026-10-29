-- Enable pgvector
create extension if not exists vector;

-- ============================================================
-- USERS
-- ============================================================
create table users (
    id              uuid primary key default gen_random_uuid(),
    phone_number    text unique not null,
    telegram_id     bigint unique,
    name            text not null,
    persona_name    text not null,
    timezone        text not null default 'UTC',
    active          boolean not null default true,
    created_at      timestamptz not null default now()
);

create index users_telegram_id_idx on users(telegram_id);

-- ============================================================
-- CONVERSATIONS
-- ============================================================
create table conversations (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,
    channel     text not null,   -- 'telegram'
    role        text not null,   -- 'user', 'model'
    content     text not null,
    created_at  timestamptz not null default now()
);

create index conversations_user_channel_idx on conversations(user_id, channel, created_at desc);

-- ============================================================
-- CALL SESSIONS
-- ============================================================
create table call_sessions (
    id          text primary key,   -- Twilio CallSid
    user_id     uuid not null references users(id) on delete cascade,
    mission     text not null,
    status      text not null default 'complete',
    transcript  jsonb not null default '[]',
    created_at  timestamptz not null default now()
);

-- ============================================================
-- EMBEDDINGS (pgvector semantic memory)
-- ============================================================
create table embeddings (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,
    content     text not null,
    vector      vector(3072) not null,   -- gemini-embedding-001 dimensions
    metadata    jsonb not null default '{}',
    created_at  timestamptz not null default now()
);

create index embeddings_user_idx on embeddings(user_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table users          enable row level security;
alter table conversations  enable row level security;
alter table call_sessions  enable row level security;
alter table embeddings     enable row level security;

-- Service role bypasses RLS (our backend uses the service role key)
create policy "users: service role only"         on users          using (false);
create policy "conversations: service role only" on conversations  using (false);
create policy "call_sessions: service role only" on call_sessions  using (false);
create policy "embeddings: service role only"    on embeddings     using (false);

-- ============================================================
-- SEMANTIC SEARCH FUNCTION
-- ============================================================
create or replace function match_embeddings(
    query_vector    vector(3072),
    match_user_id   uuid,
    match_count     int default 5
)
returns table (
    id          uuid,
    content     text,
    metadata    jsonb,
    similarity  float
)
language plpgsql
as $$
begin
    return query
    select
        e.id,
        e.content,
        e.metadata,
        1 - (e.vector <=> query_vector) as similarity
    from embeddings e
    where e.user_id = match_user_id
    order by e.vector <=> query_vector
    limit match_count;
end;
$$;
