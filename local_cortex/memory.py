import sqlite3
from datetime import datetime

DB_PATH = "data/ama_memory.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS interactions
                 (id INTEGER PRIMARY KEY, timestamp TEXT, input TEXT, output TEXT, intent TEXT)''')
    conn.commit()
    conn.close()


def save_thought(user_input, output, intent):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO interactions (timestamp, input, output, intent) VALUES (?, ?, ?, ?)",
              (timestamp, user_input, output, intent))
    conn.commit()
    conn.close()


def get_last_thoughts(limit=3):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT input, output FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"Usuario: {r[0]} | AMA: {r[1]}" for r in rows])
