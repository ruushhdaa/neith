# backend/database.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Persistence Layer
# Job: Write alert records to SQLite so they survive restarts

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# ── Configuration ──────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "neith_alerts.db")

# ── Schema ─────────────────────────────────────────────────────
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ip          TEXT    NOT NULL,
    score       REAL    NOT NULL,
    window      INTEGER NOT NULL,
    timestamp   TEXT    NOT NULL,
    recorded_at TEXT    NOT NULL,
    mitre_id    TEXT,
    mitre_name  TEXT,
    tactic      TEXT,
    role        TEXT
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_alerts_recorded_at ON alerts (recorded_at);
"""

# ── Connection ─────────────────────────────────────────────────
def _connect() -> sqlite3.Connection:
    """Open a connection with row_factory so results come back as dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Initialise ─────────────────────────────────────────────────
def init_db():
    """
    Called once at API startup.
    Creates the alerts table and index if they do not already exist.
    Safe to call on every boot — IF NOT EXISTS guards are in place.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _connect()
    try:
        conn.execute(_CREATE_TABLE)
        conn.execute(_CREATE_INDEX)
        conn.commit()
        print(f"[NEITH DB] Database ready at {os.path.abspath(DB_PATH)}")
    finally:
        conn.close()

# ── Write ───────────────────────────────────────────────────────
def insert_alert(
    ip:         str,
    score:      float,
    window:     int,
    timestamp:  str,
    mitre_id:   Optional[str] = None,
    mitre_name: Optional[str] = None,
    tactic:     Optional[str] = None,
    role:       Optional[str] = None
) -> None:
    """
    Persist one alert to the database.
    recorded_at is always the current UTC ISO timestamp so we have
    a sortable wall-clock column independent of the display timestamp.
    """
    recorded_at = datetime.utcnow().isoformat(timespec="seconds")
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO alerts (ip, score, window, timestamp, recorded_at, mitre_id, mitre_name, tactic, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ip, score, window, timestamp, recorded_at, mitre_id, mitre_name, tactic, role),
        )
        conn.commit()
    finally:
        conn.close()

# ── Read ────────────────────────────────────────────────────────
def query_alerts(
    limit: int = 100,
    since: Optional[str] = None,
) -> List[Dict]:
    """
    Return alert records in reverse-chronological order (newest first).

    Parameters
    ----------
    limit : int
        Maximum number of rows to return (default 100, max 500).
    since : str | None
        Optional ISO timestamp string. If supplied, only alerts whose
        recorded_at is strictly greater than this value are returned.
        Useful for pagination: pass the recorded_at of the last row you
        received to get the next page.
    """
    limit = min(int(limit), 500)      # hard cap — protect the UI

    conn = _connect()
    try:
        if since:
            rows = conn.execute(
                """
                SELECT id, ip, score, window, timestamp, recorded_at, mitre_id, mitre_name, tactic, role
                FROM   alerts
                WHERE  recorded_at > ?
                ORDER  BY recorded_at DESC
                LIMIT  ?
                """,
                (since, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, ip, score, window, timestamp, recorded_at, mitre_id, mitre_name, tactic, role
                FROM   alerts
                ORDER  BY recorded_at DESC
                LIMIT  ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()

# ── Utility ─────────────────────────────────────────────────────
def count_alerts() -> int:
    """Return the total number of alerts ever recorded."""
    conn = _connect()
    try:
        row = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()
