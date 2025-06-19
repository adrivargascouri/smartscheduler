import sqlite3
import json
from datetime import datetime
from typing import List, Optional

from smartscheduler.models.person import Client, Employee
from smartscheduler.models.appointment import Appointment

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STATUS_SCHEDULED = "Scheduled"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"

DB_PATH = "smartscheduler.db"


# ---------------------------------------------------------------------------
# Low‑level helpers
# ---------------------------------------------------------------------------
def create_connection() -> sqlite3.Connection:
    """Return a SQLite connection to the main DB."""
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def create_tables() -> None:
    """Create all tables if they don't exist yet."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT
        )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            availability TEXT NOT NULL
        )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )"""
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
def get_client_by_name(name: str) -> Optional[Client]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE LOWER(name) = LOWER(?)", (name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    client = Client(name=row[1], email=row[2], phone=row[3])
    client.id = row[0]
    return client


def add_client(client: Client) -> None:
    """
    Add a client if it does not exist yet.
    Updates the ``client.id`` field with the DB id.
    """
    existing = get_client_by_name(client.name)
    if existing:
        client.id = existing.id
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)",
        (client.name, client.email, client.phone),
    )
    client.id = cursor.lastrowid
    conn.commit()
    conn.close()


def get_clients() -> List[Client]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    rows = cursor.fetchall()
    conn.close()

    clients: List[Client] = []
    for row in rows:
        c = Client(name=row[1], email=row[2], phone=row[3])
        c.id = row[0]
        clients.append(c)
    return clients


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------
def get_employee_by_email(email: str) -> Optional[Employee]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    availability_raw = row[5] or "{}"
    try:
        availability = json.loads(availability_raw)
    except Exception:
        availability = {}
    emp = Employee(
        name=row[1],
        email=row[2],
        phone=row[3],
        role=row[4],
        availability=availability,
    )
    emp.id = row[0]
    return emp

def get_employee_by_name(name: str) -> Optional[Employee]:
    """Get an employee by their name."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE LOWER(name) = LOWER(?)", (name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    availability_raw = row[5] or "{}"
    try:
        availability = json.loads(availability_raw)
    except Exception:
        availability = {}
    emp = Employee(
        name=row[1],
        email=row[2],
        phone=row[3],
        role=row[4],
        availability=availability,
    )
    emp.id = row[0]
    return emp


def add_employee(employee: Employee) -> None:
    """
    Add an employee if it does not exist yet.
    Updates the ``employee.id`` field with the DB id.
    """
    existing = get_employee_by_email(employee.email)
    if existing:
        employee.id = existing.id
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO employees (name, email, phone, role, availability)
           VALUES (?, ?, ?, ?, ?)""",
        (
            employee.name,
            employee.email,
            employee.phone,
            employee.role,
            json.dumps(employee.availability),
        ),
    )
    employee.id = cursor.lastrowid
    conn.commit()
    conn.close()


def get_employees() -> List[Employee]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    rows = cursor.fetchall()
    conn.close()

    employees: List[Employee] = []
    for row in rows:
        availability_raw = row[5] or "{}"
        try:
            availability= json.loads(availability_raw)
            if not isinstance(availability,dict):
                availability = {}
        except Exception:
            availability = {}
        emp = Employee(
            name=row[1],
            email=row[2],
            phone=row[3],
            role=row[4],
            availability=availability,
        )
        emp.id = row[0]
        employees.append(emp)
    return employees


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------
def add_appointment(appointment: Appointment) -> None:
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO appointments
           (client_id, employee_id, start_time, end_time, status)
           VALUES (?, ?, ?, ?, ?)""",
        (
            appointment.client.id,
            appointment.employee.id,
            appointment.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            appointment.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            appointment.status,
        ),
    )
    appointment.id = cursor.lastrowid  # keep the ID in memory
    conn.commit()
    conn.close()


def update_appointment_status(appointment_id: int, new_status: str) -> None:
    """Update the *status* field of a single appointment."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE appointments SET status = ? WHERE id = ?",
        (new_status, appointment_id),
    )
    conn.commit()
    conn.close()


def cancel_appointments_by_client_id(client_id: int) -> int:
    """
    Mark all *scheduled* appointments for a client as CANCELLED.
    Returns the number of affected rows.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE appointments SET status = ? WHERE client_id = ? AND status = ?",
        (STATUS_CANCELLED, client_id, STATUS_SCHEDULED),
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected


def get_appointments():
    """Return a list of rows with ALL appointments (joined with client / employee names)."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT
                appointments.id,
                clients.name        AS client_name,
                employees.name      AS employee_name,
                appointments.start_time,
                appointments.end_time,
                appointments.status
            FROM appointments
            JOIN clients   ON appointments.client_id   = clients.id
            JOIN employees ON appointments.employee_id = employees.id"""
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def is_employee_available(employee_id: int, start_time: datetime, end_time: datetime) -> bool:
    """
    Return True if the employee **has no overlapping appointments** in the
    *Scheduled* status during the given time window.
    """
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT 1 FROM appointments
           WHERE employee_id = ?
             AND status = ?
             AND (
                    (start_time < ? AND end_time > ?)  -- overlap at start
                 OR (start_time < ? AND end_time > ?)  -- overlap at end
                 OR (start_time >= ? AND end_time <= ?) -- contained within
             )
           LIMIT 1""",
        (
            employee_id,
            STATUS_SCHEDULED,
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    result = cursor.fetchone()
    conn.close()
    # Available if no overlap found
    return result is None


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def add_user(username: str, password: str, role: str) -> None:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Username already exists – ignore
        pass
    finally:
        conn.close()


def validate_user(username: str, password: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_user_by_username(username: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


# ---------------------------------------------------------------------------
# Maintenance helpers
# ---------------------------------------------------------------------------
def reset_database() -> None:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.executescript(
        """DELETE FROM appointments;
           DELETE FROM clients;
           DELETE FROM employees;
           DELETE FROM users;"""
    )
    conn.commit()
    conn.close()