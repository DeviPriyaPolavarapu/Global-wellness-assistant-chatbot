# db.py
import sqlite3
import hashlib
from datetime import datetime
import os
import json

# File locations
DB_NAME = "users.db"
KB_DB = "knowledge_base.db"

def _connect(dbfile):
    # Use check_same_thread False for some cases where the app might call DB from different threads
    return sqlite3.connect(dbfile, check_same_thread=False)

def init_db():
    # Users DB
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            language TEXT,
            account_created TEXT,
            last_login TEXT,
            last_profile_update TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    # ensure a default admin exists (safe insert)
    try:
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                  ("admin", hash_password("adminpass")))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    # Knowledge base DB (single DB file)
    conn = _connect(KB_DB)
    c = conn.cursor()
    # canonical table name: knowledge_base (used by app)
    c.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT UNIQUE NOT NULL,
            description TEXT,
            symptoms TEXT,
            first_aid TEXT,
            prevention TEXT,
            disclaimer TEXT
        )
    """)
    # legacy table (some earlier imports / scripts might have used this)
    # Note: some older scripts used 'disease' as the column name; we create a legacy table with 'condition' to be canonical.
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_kb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT UNIQUE NOT NULL,
            description TEXT,
            symptoms TEXT,
            first_aid TEXT,
            prevention TEXT,
            disclaimer TEXT
        )
    """)
    # chat history in KB DB
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

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- utility helpers for varying schemas ----------------
def _table_columns(table_name: str):
    """
    Return a list of column names (lowercased) for table_name in KB_DB.
    If the table doesn't exist or on error returns [].
    """
    conn = _connect(KB_DB)
    c = conn.cursor()
    cols = []
    try:
        c.execute(f"PRAGMA table_info({table_name})")
        info = c.fetchall()
        cols = [row[1].lower() for row in info]  # second column is name
    except Exception:
        cols = []
    conn.close()
    return cols

def _kb_col_for_name(preferred="condition"):
    """
    Determine whether KB tables (knowledge_base / health_kb) have 'condition' column
    or older 'disease' column. Returns the column name to use (string).
    Preference: 'condition' then 'disease'. If neither found, returns None.
    """
    for tbl in ("knowledge_base", "health_kb"):
        cols = _table_columns(tbl)
        # prefer 'condition'
        if "condition" in cols:
            return "condition"
        if "disease" in cols:
            return "disease"
    # if none found, still return 'condition' to attempt operations (may error later)
    return "condition"

# ---------------- User functions ----------------
def register_user(username: str, password: str) -> bool:
    conn = _connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (username, password, account_created) VALUES (?, ?, ?)",
                  (username, hash_password(password), now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username: str, password: str):
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    user = c.fetchone()
    if user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET last_login=? WHERE username=?", (now, username))
        conn.commit()
    conn.close()
    return user

def get_user(username: str):
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT age, gender, language, account_created, last_login, last_profile_update FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_users():
    conn = _connect(DB_NAME)
    c = conn.cursor()
    # return rows in descending id (newest first)
    c.execute("SELECT id, username, age, gender, language, account_created, last_login FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def update_user(username: str, age=None, gender=None, language=None) -> bool:
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT age, gender, language FROM users WHERE username=?", (username,))
    current = c.fetchone()
    if not current:
        conn.close()
        return False
    new_age = age if age is not None else current[0]
    new_gender = gender if gender is not None else current[1]
    new_language = language if language is not None else current[2]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET age=?, gender=?, language=?, last_profile_update=? WHERE username=?",
              (new_age, new_gender, new_language, now, username))
    conn.commit()
    conn.close()
    return True

def delete_user(username: str):
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def reset_password(username: str, new_password: str):
    conn = _connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new_password), username))
    conn.commit()
    conn.close()

# ---------------- Knowledge base functions ----------------
def add_kb_entry(condition: str, description: str = "", symptoms: str = "", first_aid: str = "", prevention: str = "", disclaimer: str = "") -> bool:
    """
    Always add to canonical knowledge_base table (with 'condition' column).
    """
    conn = _connect(KB_DB)
    c = conn.cursor()
    try:
        # ensure canonical table has 'condition' column; fail gracefully otherwise
        cols = _table_columns("knowledge_base")
        if "condition" not in cols:
            # try to create canonical column if missing (best-effort)
            try:
                c.execute("ALTER TABLE knowledge_base ADD COLUMN condition TEXT")
                conn.commit()
            except Exception:
                pass
        c.execute("INSERT INTO knowledge_base (condition, description, symptoms, first_aid, prevention, disclaimer) VALUES (?, ?, ?, ?, ?, ?)",
                  (condition, description, symptoms, first_aid, prevention, disclaimer))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def edit_kb_entry(condition: str, description: str = "", symptoms: str = "", first_aid: str = "", prevention: str = "", disclaimer: str = "") -> bool:
    """
    Edit canonical knowledge_base entry (case-insensitive). Returns True if updated.
    """
    if not condition:
        return False
    condition_clean = condition.strip().lower()
    conn = _connect(KB_DB)
    c = conn.cursor()
    try:
        # Use lower(condition) comparison to be case-insensitive
        c.execute("UPDATE knowledge_base SET description=?, symptoms=?, first_aid=?, prevention=?, disclaimer=? WHERE lower(condition)=?",
                  (description, symptoms, first_aid, prevention, disclaimer, condition_clean))
        updated = c.rowcount
        conn.commit()
        return updated > 0
    finally:
        conn.close()

def delete_kb_entry(condition: str) -> bool:
    """
    Deletes a KB entry by condition (case-insensitive).
    Returns True if any row was deleted.
    Robust to either 'condition' or legacy 'disease' column names in tables.
    """
    if not condition:
        return False
    cond_clean = condition.strip().lower()
    conn = _connect(KB_DB)
    c = conn.cursor()
    total_deleted = 0
    tables = ["knowledge_base", "health_kb"]
    for tbl in tables:
        cols = _table_columns(tbl)
        # determine which name to use
        colname = None
        if "condition" in cols:
            colname = "condition"
        elif "disease" in cols:
            colname = "disease"
        else:
            # no usable column in this table, skip
            continue
        try:
            c.execute(f"DELETE FROM {tbl} WHERE lower({colname}) = ?", (cond_clean,))
            total_deleted += c.rowcount
        except Exception:
            # skip any error and continue to next
            continue
    conn.commit()
    conn.close()
    return total_deleted > 0

def _fetch_from_table(tbl: str, colname: str):
    """
    Helper to fetch (condition, description, symptoms, first_aid, prevention, disclaimer)
    from a table that may use 'condition' or 'disease' as the key column.
    Returns list of tuples.
    """
    conn = _connect(KB_DB)
    c = conn.cursor()
    rows_out = []
    try:
        c.execute(f"SELECT {colname}, description, symptoms, first_aid, prevention, disclaimer FROM {tbl}")
        rows = c.fetchall()
        for r in rows:
            # ensure tuple length and replace None
            rows_out.append((r[0], r[1] or "", r[2] or "", r[3] or "", r[4] or "", r[5] or ""))
    except Exception:
        pass
    conn.close()
    return rows_out

def get_all_kb_entries():
    """
    Return a merged list of KB entries from knowledge_base and health_kb,
    handling both 'condition' and legacy 'disease' column names.
    Results sorted alphabetically by condition.
    """
    entries = []
    for tbl in ("knowledge_base", "health_kb"):
        cols = _table_columns(tbl)
        if not cols:
            continue
        # choose column name
        col = "condition" if "condition" in cols else ("disease" if "disease" in cols else None)
        if not col:
            continue
        rows = _fetch_from_table(tbl, col)
        for r in rows:
            # avoid duplicates by case-insensitive condition
            if not any((e[0] or "").strip().lower() == (r[0] or "").strip().lower() for e in entries):
                entries.append((r[0], r[1], r[2], r[3], r[4], r[5]))
    entries_sorted = sorted(entries, key=lambda x: (x[0] or "").lower())
    return entries_sorted

def get_kb_entry(condition: str):
    """
    Return single KB entry tuple (condition, description, symptoms, first_aid, prevention, disclaimer)
    searching both tables, case-insensitive. Returns None if not found.
    """
    if not condition:
        return None
    cond_clean = condition.strip().lower()
    conn = _connect(KB_DB)
    c = conn.cursor()
    # check canonical table first
    try:
        cols = _table_columns("knowledge_base")
        if "condition" in cols:
            c.execute("SELECT condition, description, symptoms, first_aid, prevention, disclaimer FROM knowledge_base WHERE lower(condition)=?", (cond_clean,))
            row = c.fetchone()
            if row:
                conn.close()
                return (row[0], row[1] or "", row[2] or "", row[3] or "", row[4] or "", row[5] or "")
    except Exception:
        pass
    # check legacy table with either column name
    try:
        cols2 = _table_columns("health_kb")
        if "condition" in cols2:
            c.execute("SELECT condition, description, symptoms, first_aid, prevention, disclaimer FROM health_kb WHERE lower(condition)=?", (cond_clean,))
            row2 = c.fetchone()
            if row2:
                conn.close()
                return (row2[0], row2[1] or "", row2[2] or "", row2[3] or "", row2[4] or "", row2[5] or "")
        elif "disease" in cols2:
            c.execute("SELECT disease, description, symptoms, first_aid, prevention, disclaimer FROM health_kb WHERE lower(disease)=?", (cond_clean,))
            row3 = c.fetchone()
            if row3:
                conn.close()
                return (row3[0], row3[1] or "", row3[2] or "", row3[3] or "", row3[4] or "", row3[5] or "")
    except Exception:
        pass
    conn.close()
    return None

# ---------------- Chat history helpers ----------------
def count_queries_per_day():
    conn = _connect(KB_DB)
    c = conn.cursor()
    c.execute("SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM chat_history GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def total_queries_count():
    conn = _connect(KB_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM chat_history")
    r = c.fetchone()[0]
    conn.close()
    return r

# Initialize DBs on import
init_db()
