import sqlite3

KB_DB = "C:/Users/India/Desktop/Infosys_WellBot/chatbot/knowledge_base.db"

conn = sqlite3.connect(KB_DB)
c = conn.cursor()

condition = "Fever"  # replace with your condition

# Check knowledge_base table
c.execute("SELECT * FROM knowledge_base WHERE condition=?", (condition,))
kb_res = c.fetchall()

# Check health_kb table
c.execute("SELECT * FROM health_kb WHERE condition=?", (condition,))
hk_res = c.fetchall()

conn.close()

print("knowledge_base:", kb_res)
print("health_kb:", hk_res)
