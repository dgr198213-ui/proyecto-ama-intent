import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# SQLite configuration for local development
DB_PATH = "data/ama_memory.db"
# Ensure the data directory exists
os.makedirs("data", exist_ok=True)
logger.info("ℹ️ Using local SQLite storage in data/")


def check_database_connection() -> Dict[str, Any]:
    """
    Check database connection health.
    Returns status information about the database connection.
    """
    result = {
        "type": "sqlite",
        "connected": False,
        "message": "",
        "error_type": None,
        "details": None,
    }

    try:
        # Test SQLite connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result["connected"] = True
            result["message"] = "SQLite connection successful"
            logger.info("✅ SQLite connection check passed")
    except Exception as e:
        result["connected"] = False
        result["error_type"] = "unknown_error"
        result["message"] = "Database connection check failed"
        logger.error(f"❌ Database connection check failed: {e}")

    return result


@contextmanager
def get_db_connection():
    """Context manager for SQLite database connections."""
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
    """Initialize database schema."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS interactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT NOT NULL,
                      input TEXT NOT NULL,
                      output TEXT NOT NULL,
                      intent TEXT)""")
        # Create indexes for better performance
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions(timestamp DESC)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_intent ON interactions(intent)")
    logger.info("✅ SQLite database initialized")


def enforce_memory_limit():
    """Ensure the database does not exceed MEMORY_MAX_ENTRIES."""
    max_entries = int(os.getenv("MEMORY_MAX_ENTRIES", "1000"))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM interactions")
        count = c.fetchone()[0]

        if count > max_entries:
            # Delete the oldest entries to stay within limit
            to_delete = count - max_entries
            c.execute(
                "DELETE FROM interactions WHERE id IN (SELECT id FROM interactions ORDER BY id ASC LIMIT ?)",
                (to_delete,),
            )
            logger.info(f"♻️ Memory limit reached. Removed {to_delete} oldest entries.")


def save_thought(user_input: str, output: str, intent: str):
    """Save a thought/interaction to the database."""
    timestamp = datetime.now().isoformat()

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO interactions (timestamp, input, output, intent) VALUES (?, ?, ?, ?)",
            (timestamp, user_input, output, intent),
        )

    # Automatically enforce memory limits
    try:
        enforce_memory_limit()
    except Exception as e:
        logger.warning(f"⚠️ Failed to enforce memory limit: {e}")


def get_last_thoughts(limit: int = 3) -> str:
    """Get the last N thoughts as formatted context string."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT input, output FROM interactions ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()

    return "\n".join([f"Usuario: {r[0]} | AMA: {r[1]}" for r in rows])


def search_thoughts(query: str, limit: int = 10) -> List[Dict[str, Any]]:
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


def get_memory_stats() -> Dict[str, Any]:
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


def cleanup_old_thoughts(days: int = 30) -> int:
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


def get_thoughts_by_intent(intent: str, limit: int = 10) -> List[Dict[str, Any]]:
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
