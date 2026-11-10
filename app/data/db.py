"""SQLite access. Foreign keys enforced on every connection."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id        TEXT PRIMARY KEY,                 -- e.g. SOP-LOTO-04-v1
    doc_key       TEXT NOT NULL,
    title         TEXT NOT NULL,
    category      TEXT NOT NULL CHECK (category IN ('safety','maintenance','quality')),
    version       INTEGER NOT NULL CHECK (version >= 1),
    status        TEXT NOT NULL CHECK (status IN ('draft','published','rejected','retired')),
    owner         TEXT NOT NULL,
    equipment     TEXT NOT NULL DEFAULT '',
    content       TEXT NOT NULL,
    created_by    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    reviewed_by   TEXT,
    reviewed_at   TEXT,
    review_note   TEXT,
    guardrail_flags TEXT NOT NULL DEFAULT '[]',
    is_synthetic  INTEGER NOT NULL DEFAULT 1,
    UNIQUE (doc_key, version)
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id   TEXT PRIMARY KEY,                    -- <doc_id>#s<n>
    doc_id     TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    section_no INTEGER NOT NULL,
    section    TEXT NOT NULL,
    text       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS queries (
    query_id          TEXT PRIMARY KEY,
    request_id        TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    user_name         TEXT NOT NULL,
    role              TEXT NOT NULL CHECK (role IN ('supervisor','manager')),
    question_masked   TEXT NOT NULL,
    routed_categories TEXT NOT NULL DEFAULT '[]',
    primary_category  TEXT CHECK (primary_category IN ('safety','maintenance','quality')),
    route_confidence  REAL,
    safety_flag       INTEGER NOT NULL DEFAULT 0,
    broad_search      INTEGER NOT NULL DEFAULT 0,
    emergency         INTEGER NOT NULL DEFAULT 0,
    status            TEXT NOT NULL CHECK (status IN ('ok','abstained','blocked','error')),
    answer_confidence TEXT,
    equipment_tag     TEXT,
    latency_ms        REAL NOT NULL DEFAULT 0,
    tokens_in         INTEGER NOT NULL DEFAULT 0,
    tokens_out        INTEGER NOT NULL DEFAULT 0,
    model             TEXT NOT NULL,
    guardrail_flags   TEXT NOT NULL DEFAULT '[]',
    error             TEXT,
    is_synthetic      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS citations (
    query_id TEXT NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id),
    rank     INTEGER NOT NULL,
    score    REAL NOT NULL,
    PRIMARY KEY (query_id, chunk_id)
);
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id      TEXT NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
    created_at    TEXT NOT NULL,
    user_name     TEXT NOT NULL,
    rating        INTEGER NOT NULL CHECK (rating IN (1,-1)),
    comment       TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL CHECK (review_status IN ('n/a','pending','approved','rejected')),
    reviewed_by   TEXT,
    reviewed_at   TEXT,
    review_note   TEXT,
    is_synthetic  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    actor      TEXT NOT NULL,
    role       TEXT NOT NULL,
    action     TEXT NOT NULL,
    target     TEXT NOT NULL,
    decision   TEXT,
    model      TEXT,
    request_id TEXT,
    details    TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_queries_created ON queries(created_at);
CREATE INDEX IF NOT EXISTS ix_docs_status ON documents(status, category);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def tx():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with tx() as c:
        c.executescript(SCHEMA)


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with tx() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]
