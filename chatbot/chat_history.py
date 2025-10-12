# chat_history.py
import sqlite3
import os
from datetime import datetime

KB_DB = os.path.join(os.path.dirname(__file__), "knowledge_base.db")

def init_chat_history():
    conn = sqlite3.connect(KB_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            query TEXT NOT NULL,
            intent TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_chat(username, query, intent, response):
    conn = sqlite3.connect(KB_DB)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO chat_history (username, query, intent, response, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, query, intent, response, timestamp))
    chat_id = c.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def get_all_chats():
    conn = sqlite3.connect(KB_DB)
    c = conn.cursor()
    c.execute("SELECT id, username, query, intent, response, timestamp FROM chat_history ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_chat_history(username):
    conn = sqlite3.connect(KB_DB)
    c = conn.cursor()
    c.execute("SELECT id, query, intent, response, timestamp FROM chat_history WHERE username=? ORDER BY timestamp DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_user_chats(username):
    conn = sqlite3.connect(KB_DB)
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE username=?", (username,))
    conn.commit()
    conn.close()

# initialize
init_chat_history()
