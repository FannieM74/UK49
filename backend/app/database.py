import sqlite3
import os
from datetime import datetime, timedelta

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "uk49.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT NOT NULL,
            draw_type TEXT NOT NULL,
            n1 INTEGER NOT NULL,
            n2 INTEGER NOT NULL,
            n3 INTEGER NOT NULL,
            n4 INTEGER NOT NULL,
            n5 INTEGER NOT NULL,
            n6 INTEGER NOT NULL,
            bonus INTEGER NOT NULL,
            UNIQUE(draw_date, draw_type)
        );
        CREATE INDEX IF NOT EXISTS idx_draws_date ON draws(draw_date);
        CREATE INDEX IF NOT EXISTS idx_draws_type ON draws(draw_type);

        CREATE TABLE IF NOT EXISTS prediction_cache (
            draw_type TEXT PRIMARY KEY,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def insert_draw(draw_date, draw_type, numbers):
    conn = get_connection()
    conn.execute(
        """INSERT OR IGNORE INTO draws (draw_date, draw_type, n1, n2, n3, n4, n5, n6, bonus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (draw_date, draw_type, *numbers)
    )
    conn.commit()
    conn.close()

def get_draws(limit=50, offset=0, draw_type=None):
    conn = get_connection()
    query = "SELECT * FROM draws"
    params = []
    if draw_type:
        query += " WHERE draw_type = ?"
        params.append(draw_type)
    query += " ORDER BY draw_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_draw_date(draw_type=None):
    conn = get_connection()
    if draw_type:
        row = conn.execute("SELECT MAX(draw_date) as max_date FROM draws WHERE draw_type = ?", (draw_type,)).fetchone()
    else:
        row = conn.execute("SELECT MAX(draw_date) as max_date FROM draws").fetchone()
    conn.close()
    return row["max_date"] if row else None

def get_draws_count():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as count FROM draws").fetchone()
    conn.close()
    return row["count"]

def get_draws_by_type_count(draw_type):
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as count FROM draws WHERE draw_type = ?", (draw_type,)).fetchone()
    conn.close()
    return row["count"]

def get_cached_prediction(draw_type: str, max_age_days: int = 3):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM prediction_cache WHERE draw_type = ?",
        (draw_type,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    created = datetime.fromisoformat(row["created_at"])
    if datetime.now() - created > timedelta(days=max_age_days):
        return None
    return row["result_json"]

def set_cached_prediction(draw_type: str, result_json: str):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO prediction_cache (draw_type, result_json, created_at)
           VALUES (?, ?, ?)""",
        (draw_type, result_json, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def clear_prediction_cache():
    conn = get_connection()
    conn.execute("DELETE FROM prediction_cache")
    conn.commit()
    conn.close()
