import os
import threading
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


class DatabaseNotConfigured(RuntimeError):
    pass


_schema_lock = threading.Lock()
_schema_ready = False

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS edith_users (
        username TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_login TIMESTAMPTZ,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS edith_documents (
        username TEXT PRIMARY KEY REFERENCES edith_users(username) ON DELETE CASCADE,
        name TEXT NOT NULL,
        blob_path TEXT NOT NULL,
        chunks JSONB NOT NULL,
        chunk_count INTEGER NOT NULL,
        character_count BIGINT NOT NULL,
        uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS edith_chat_messages (
        id BIGSERIAL PRIMARY KEY,
        username TEXT NOT NULL REFERENCES edith_users(username) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS edith_chat_messages_user_id_idx
    ON edith_chat_messages (username, id)
    """,
)


def _database_url():
    for name in ("POSTGRES_URL", "DATABASE_URL", "POSTGRES_URL_NON_POOLING"):
        value = os.getenv(name)
        if value:
            return value
    raise DatabaseNotConfigured(
        "Connect a PostgreSQL Marketplace database and set POSTGRES_URL."
    )


def _ensure_schema(conn):
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        with conn.cursor() as cursor:
            for statement in _SCHEMA:
                cursor.execute(statement)
        conn.commit()
        _schema_ready = True


@contextmanager
def connection():
    conn = psycopg.connect(
        _database_url(),
        connect_timeout=8,
        row_factory=dict_row,
    )
    try:
        _ensure_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
