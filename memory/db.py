import json
import sqlite3
import uuid
from functools import lru_cache

from config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    phone_number    TEXT UNIQUE NOT NULL,
    telegram_id     INTEGER UNIQUE,
    name            TEXT NOT NULL,
    persona_name    TEXT NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'UTC',
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    channel     TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS conversations_user_channel_idx
    ON conversations(user_id, channel, created_at DESC);

CREATE TABLE IF NOT EXISTS call_sessions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    mission     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'complete',
    transcript  TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS embeddings (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    vector      TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS embeddings_user_idx ON embeddings(user_id);
"""


def _gen_uuid() -> str:
    return str(uuid.uuid4())


@lru_cache(maxsize=1)
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    return conn
