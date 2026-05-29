import sqlite3

conn = sqlite3.connect("data/registry.db")
cur = conn.cursor()

print("TABLES:")
tables = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for t in tables:
    print(t)

conn.close()