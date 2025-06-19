import sqlite3
import json

DB_FILE = "smartscheduler.db"

availabilities = {
    "Laura Sanchez": {
        "Monday": ["08:00-12:00", "16:00-20:00"],
        "Tuesday": ["09:00-13:00"]
    },
    "Carlos Gomez": {
        "Monday": ["08:00-12:00"],
        "Thursday": ["09:00-12:00", "14:00-18:00"],
        "Friday": ["10:00-16:00"]
    },
    "Ana Torres": {
        "Friday": ["09:00-12:00"]
    }
  
}

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

for employee_name, availability in availabilities.items():
    cur.execute(
        "UPDATE employees SET availability=? WHERE name=?",
        (json.dumps(availability), employee_name)
    )
    print(f"Availability Updated for {employee_name}")

conn.commit()
conn.close()