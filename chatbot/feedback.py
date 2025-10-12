# feedback.py
import sqlite3
import os
from datetime import datetime

FB_DB = os.path.join(os.path.dirname(__file__), "feedback.db")

def init_feedback_db():
    conn = sqlite3.connect(FB_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            username TEXT,
            thumbs_up INTEGER,
            comment TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_feedback(chat_id, username, thumbs_up, comment=""):
    conn = sqlite3.connect(FB_DB)
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO feedback (chat_id, username, thumbs_up, comment, timestamp) VALUES (?, ?, ?, ?, ?)",
              (chat_id, username, thumbs_up, comment, ts))
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = sqlite3.connect(FB_DB)
    c = conn.cursor()
    c.execute("SELECT id, chat_id, username, thumbs_up, comment, timestamp FROM feedback ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def feedback_stats():
    conn = sqlite3.connect(FB_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM feedback WHERE thumbs_up=1"); pos = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM feedback WHERE thumbs_up=0"); neg = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM feedback"); total = c.fetchone()[0]
    conn.close()
    return {"pos": pos, "neg": neg, "total": total}

# initialize
init_feedback_db()
