import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "users.db"

# ------------------- Initialize Database -------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            language TEXT
        )
    """)
    conn.commit()

    # Add timestamp columns if missing
    for col in ["account_created", "last_login", "last_profile_update"]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()

    # Create chat log table
    c.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_message TEXT,
            bot_response TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- User Operations -------------------
def register_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO users (username, password, account_created)
            VALUES (?, ?, ?)
        """, (username, hash_password(password), now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    user = c.fetchone()
    if user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET last_login=? WHERE username=?", (now, username))
        conn.commit()
    conn.close()
    return user

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT age, gender, language, account_created, last_login, last_profile_update 
        FROM users WHERE username=?
    """, (username,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(username, age, gender, language):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        UPDATE users SET age=?, gender=?, language=?, last_profile_update=?
        WHERE username=?
    """, (age, gender, language, now, username))
    conn.commit()
    conn.close()

def delete_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def reset_password(username, new_password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?", 
              (hash_password(new_password), username))
    conn.commit()
    conn.close()

# ------------------- Chat Logging -------------------
def log_user_query(username, user_msg, bot_resp):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO query_log (username, user_message, bot_response, timestamp)
        VALUES (?, ?, ?, ?)
    """, (username, user_msg, bot_resp, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ------------------- Language Preference Helpers -------------------
def update_language(username, language):
    """Update only language preference for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET language=? WHERE username=?", (language, username))
    conn.commit()
    conn.close()

def get_language(username):
    """Fetch user’s language preference. Defaults to English if not set."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else "en"
