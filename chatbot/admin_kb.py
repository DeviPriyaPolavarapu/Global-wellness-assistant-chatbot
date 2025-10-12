import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.db")

def init_health_kb_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_kb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease TEXT UNIQUE,
            description TEXT,
            symptoms TEXT,
            first_aid TEXT,
            prevention TEXT,
            disclaimer TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_json_to_db(json_file):
    """Load health_kb JSON data into DB (initial setup)"""
    with open(json_file, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for disease, data in kb_data.items():
        c.execute("""
            INSERT OR REPLACE INTO health_kb (disease, description, symptoms, first_aid, prevention, disclaimer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            disease,
            data.get("description",""),
            json.dumps(data.get("symptoms",[])),
            json.dumps(data.get("first_aid",[])),
            json.dumps(data.get("prevention",[])),
            data.get("disclaimer","")
        ))
    conn.commit()
    conn.close()

def get_all_kb_entries():
    """Fetch all KB entries for admin dashboard"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT disease, description, symptoms, first_aid, prevention, disclaimer FROM health_kb ORDER BY disease ASC")
    rows = c.fetchall()
    conn.close()
    kb_entries = {}
    for row in rows:
        disease, description, symptoms, first_aid, prevention, disclaimer = row
        kb_entries[disease] = {
            "description": description,
            "symptoms": json.loads(symptoms),
            "first_aid": json.loads(first_aid),
            "prevention": json.loads(prevention),
            "disclaimer": disclaimer
        }
    return kb_entries

# Initialize table on import
init_health_kb_table()
