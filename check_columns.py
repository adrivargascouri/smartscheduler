import sqlite3

DB_PATH = "smartscheduler.db"

def check_appointments_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(appointments);")
    columns = cursor.fetchall()
    conn.close()

    print("Columnas en la tabla 'appointments':")
    for col in columns:
        print(f" - {col[1]} ({col[2]})")

if __name__ == "__main__":
    check_appointments_columns()
