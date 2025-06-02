import sqlite3

DB_PATH = "smartscheduler.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'empleado';")
    print("✅ Columna 'role' agregada correctamente.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Ya existe o error: {e}")

conn.commit()
conn.close()


