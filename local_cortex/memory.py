import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PATH = "data/ama_memory.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS interactions
                     (id INTEGER PRIMARY KEY, timestamp TEXT, input TEXT, output TEXT, intent TEXT)"""
        )


def save_thought(user_input, output, intent):
    timestamp = datetime.now().isoformat()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO interactions (timestamp, input, output, intent) VALUES (?, ?, ?, ?)",
            (timestamp, user_input, output, intent),
        )


def get_last_thoughts(limit=3):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT input, output FROM interactions ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = c.fetchall()
    return "\n".join([f"Usuario: {r[0]} | AMA: {r[1]}" for r in rows])


def search_thoughts(query, limit=10):
    """Search thoughts by keyword in input or output."""
    with get_db_connection() as conn:
        c = conn.cursor()
        search_pattern = f"%{query}%"
        c.execute(
            """SELECT timestamp, input, output, intent 
                     FROM interactions 
                     WHERE input LIKE ? OR output LIKE ?
                     ORDER BY id DESC LIMIT ?""",
            (search_pattern, search_pattern, limit),
        )
        rows = c.fetchall()
    return [
        {"timestamp": r[0], "input": r[1], "output": r[2], "intent": r[3]} for r in rows
    ]


def get_memory_stats():
    """Get statistics about the memory database."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM interactions")
        total_count = c.fetchone()[0]

        c.execute("SELECT intent, COUNT(*) FROM interactions GROUP BY intent")
        by_intent = dict(c.fetchall())

        c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM interactions")
        date_range = c.fetchone()

    return {
        "total_interactions": total_count,
        "by_intent": by_intent,
        "first_interaction": date_range[0],
        "last_interaction": date_range[1],
    }


def cleanup_old_thoughts(days=30):
    """Archive or delete thoughts older than specified days."""
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM interactions WHERE timestamp < ?", (cutoff_date,)
        )
        count = c.fetchone()[0]

        if count > 0:
            c.execute("DELETE FROM interactions WHERE timestamp < ?", (cutoff_date,))
    return count


def get_thoughts_by_intent(intent, limit=10):
    """Retrieve thoughts filtered by intent type."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """SELECT timestamp, input, output 
                     FROM interactions 
                     WHERE intent = ?
                     ORDER BY id DESC LIMIT ?""",
            (intent, limit),
        )
        rows = c.fetchall()
    return [{"timestamp": r[0], "input": r[1], "output": r[2]} for r in rows]
