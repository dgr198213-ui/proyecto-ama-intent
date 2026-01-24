import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Database configuration
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Check if we're in a serverless environment
IS_SERVERLESS = bool(
    os.getenv("VERCEL")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("LAMBDA_TASK_ROOT")
)

# Initialize Supabase client if configured
supabase_client = None
_use_supabase_actual = USE_SUPABASE  # Track actual state separately
if USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import Client, create_client

        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
        logger.warning("⚠️ Falling back to SQLite storage")
        _use_supabase_actual = False


def _is_using_supabase() -> bool:
    """Check if Supabase is actually being used (not just configured)."""
    return _use_supabase_actual and supabase_client is not None


# SQLite configuration (fallback or local development)
if IS_SERVERLESS and not _use_supabase_actual:
    # Use /tmp directory for serverless (ephemeral storage)
    DB_PATH = "/tmp/ama_memory.db"
    logger.info("ℹ️ Using ephemeral SQLite storage in /tmp (serverless mode)")
elif not _use_supabase_actual:
    # Use data directory for normal deployments
    DB_PATH = "data/ama_memory.db"
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    logger.info("ℹ️ Using local SQLite storage in data/")
else:
    DB_PATH = None
    logger.info("ℹ️ Using Supabase for persistent storage")


def check_database_connection() -> Dict[str, Any]:
    """
    Check database connection health.
    Returns status information about the database connection.
    """
    using_supabase = _is_using_supabase()
    result = {
        "type": "supabase" if using_supabase else "sqlite",
        "connected": False,
        "message": "",
        "url": SUPABASE_URL if using_supabase else DB_PATH,
    }

    try:
        if using_supabase:
            # Test Supabase connection by querying the table
            response = (
                supabase_client.table("interactions").select("id").limit(1).execute()
            )
            result["connected"] = True
            result["message"] = "Supabase connection successful"
            logger.info("✅ Supabase connection check passed")
        elif DB_PATH:
            # Test SQLite connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result["connected"] = True
                result["message"] = "SQLite connection successful"
                logger.info("✅ SQLite connection check passed")
        else:
            result["message"] = "No database configured"
            logger.warning("⚠️ No database configured")
    except Exception as e:
        result["connected"] = False
        result["message"] = f"Connection failed: {str(e)}"
        logger.error(f"❌ Database connection check failed: {e}")

    return result


@contextmanager
def get_db_connection():
    """
    Context manager for SQLite database connections.

    Raises:
        RuntimeError: If Supabase is enabled. When using Supabase, access the database
                     through the module-level `supabase_client` object and its table() methods.
    """
    if _is_using_supabase():
        raise RuntimeError(
            "SQLite connection requested but Supabase is enabled. "
            "Use the module-level 'supabase_client' object instead. "
            "Example: supabase_client.table('interactions').select('*').execute()"
        )

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
    if _is_using_supabase():
        # Supabase table should be created via SQL migration
        # Check if table exists and is accessible
        try:
            supabase_client.table("interactions").select("id").limit(1).execute()
            logger.info("✅ Supabase table 'interactions' is accessible")
        except Exception as e:
            logger.error(f"❌ Supabase table check failed: {e}")
            logger.info("""
            ⚠️ Please create the 'interactions' table in Supabase with the following SQL:
            
            CREATE TABLE IF NOT EXISTS interactions (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                input TEXT NOT NULL,
                output TEXT NOT NULL,
                intent TEXT
            );
            
            CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
            CREATE INDEX idx_interactions_intent ON interactions(intent);
            """)
            raise
    else:
        # Initialize SQLite
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


def save_thought(user_input: str, output: str, intent: str):
    """Save a thought/interaction to the database."""
    timestamp = datetime.now().isoformat()

    if _is_using_supabase():
        try:
            supabase_client.table("interactions").insert(
                {
                    "timestamp": timestamp,
                    "input": user_input,
                    "output": output,
                    "intent": intent,
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to save thought to Supabase: {e}")
            raise
    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO interactions (timestamp, input, output, intent) VALUES (?, ?, ?, ?)",
                (timestamp, user_input, output, intent),
            )


def get_last_thoughts(limit: int = 3) -> str:
    """Get the last N thoughts as formatted context string."""
    if _is_using_supabase():
        try:
            response = (
                supabase_client.table("interactions")
                .select("input, output")
                .order("id", desc=True)
                .limit(limit)
                .execute()
            )
            rows = [(r["input"], r["output"]) for r in response.data]
        except Exception as e:
            logger.error(f"Failed to get thoughts from Supabase: {e}")
            return ""
    else:
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
    if _is_using_supabase():
        try:
            # Use Supabase full-text search or ILIKE
            response = (
                supabase_client.table("interactions")
                .select("timestamp, input, output, intent")
                .or_(f"input.ilike.%{query}%,output.ilike.%{query}%")
                .order("id", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to search thoughts in Supabase: {e}")
            return []
    else:
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
            {"timestamp": r[0], "input": r[1], "output": r[2], "intent": r[3]}
            for r in rows
        ]


def get_memory_stats() -> Dict[str, Any]:
    """Get statistics about the memory database."""
    if _is_using_supabase():
        try:
            # Get total count
            total_response = (
                supabase_client.table("interactions")
                .select("id", count="exact")
                .execute()
            )
            total_count = total_response.count or 0

            # Get counts by intent - try RPC function first, fallback to direct query
            try:
                intent_response = supabase_client.rpc("get_intent_counts").execute()
                by_intent = {
                    r["intent"]: r["count"] for r in (intent_response.data or [])
                }
            except Exception as rpc_error:
                logger.warning(
                    f"RPC function 'get_intent_counts' not available, using fallback: {rpc_error}"
                )
                # Fallback: get all intents and count manually (less efficient but works)
                intent_response = (
                    supabase_client.table("interactions").select("intent").execute()
                )
                from collections import Counter

                by_intent = dict(
                    Counter(
                        r["intent"] for r in intent_response.data if r.get("intent")
                    )
                )

            # Get date range
            date_response = (
                supabase_client.table("interactions")
                .select("timestamp")
                .order("timestamp", desc=False)
                .limit(1)
                .execute()
            )
            first_interaction = (
                date_response.data[0]["timestamp"] if date_response.data else None
            )

            date_response = (
                supabase_client.table("interactions")
                .select("timestamp")
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            last_interaction = (
                date_response.data[0]["timestamp"] if date_response.data else None
            )

            return {
                "total_interactions": total_count,
                "by_intent": by_intent,
                "first_interaction": first_interaction,
                "last_interaction": last_interaction,
            }
        except Exception as e:
            logger.error(f"Failed to get stats from Supabase: {e}")
            return {
                "total_interactions": 0,
                "by_intent": {},
                "first_interaction": None,
                "last_interaction": None,
            }
    else:
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

    if _is_using_supabase():
        try:
            # Get count first
            count_response = (
                supabase_client.table("interactions")
                .select("id", count="exact")
                .lt("timestamp", cutoff_date)
                .execute()
            )
            count = count_response.count or 0

            if count > 0:
                # Delete old records
                supabase_client.table("interactions").delete().lt(
                    "timestamp", cutoff_date
                ).execute()

            return count
        except Exception as e:
            logger.error(f"Failed to cleanup thoughts in Supabase: {e}")
            return 0
    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM interactions WHERE timestamp < ?", (cutoff_date,)
            )
            count = c.fetchone()[0]

            if count > 0:
                c.execute(
                    "DELETE FROM interactions WHERE timestamp < ?", (cutoff_date,)
                )
        return count


def get_thoughts_by_intent(intent: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve thoughts filtered by intent type."""
    if _is_using_supabase():
        try:
            response = (
                supabase_client.table("interactions")
                .select("timestamp, input, output")
                .eq("intent", intent)
                .order("id", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get thoughts by intent from Supabase: {e}")
            return []
    else:
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
