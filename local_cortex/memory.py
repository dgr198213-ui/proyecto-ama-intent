import sqlite3
from datetime import datetime
from contextlib import contextmanager

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
        c.execute('''CREATE TABLE IF NOT EXISTS interactions
                     (id INTEGER PRIMARY KEY, timestamp TEXT, input TEXT, output TEXT, intent TEXT)''')


def save_thought(user_input, output, intent):
    timestamp = datetime.now().isoformat()
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO interactions (timestamp, input, output, intent) VALUES (?, ?, ?, ?)",
                  (timestamp, user_input, output, intent))


def get_last_thoughts(limit=3):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT input, output FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
    return "\n".join([f"Usuario: {r[0]} | AMA: {r[1]}" for r in rows])
