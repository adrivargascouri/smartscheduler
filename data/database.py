import sqlite3
from models.person import Client, Employee
from models.appointment import Appointment


DB_PATH = "smartscheduler.db"

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        role TEXT NOT NULL,
        availability TEXT NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )''')

    conn.commit()
    conn.close()

def get_client_by_name(name: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        client = Client(name=row[1], email=row[2], phone=row[3])
        client.id = row[0]
        return client
    return None

def get_employee_by_email(email):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        # Asegúrate de que availability sea un string, o asigna una lista vacía si es None
        availability_str = row[5] if row[5] is not None else ""
        employee = Employee(
            name=row[1],
            email=row[2],
            phone=row[3],
            role=row[4],
            # Usa split solo si availability_str es una cadena no vacía
            availability=availability_str.split(",") if availability_str else []
        )
        employee.id = row[0]  # Asignar el id al objeto Employee
        return employee
    return None


def add_client(client: Client):
    existing_client = get_client_by_name(client.name)
    if existing_client:
        client.id = existing_client.id # asignar el id existente
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clients (name, email, phone)
        VALUES (?, ?, ?)
    ''', (client.name, client.email, client.phone))
    client.id = cursor.lastrowid
    conn.commit()
    conn.close()

def add_employee(employee: Employee):
    existing_employee = get_employee_by_email(employee.email)
    if existing_employee:
        employee.id = existing_employee.id  # ✅ CORREGIDO
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO employees (name, email, phone, role, availability)
        VALUES (?, ?, ?, ?, ?)
    ''', (employee.name, employee.email, employee.phone, employee.role, ",".join(employee.availability)))
    employee.id = cursor.lastrowid
    conn.commit()
    conn.close()


def add_appointment(appointment):
    conn = create_connection()
    cursor = conn.cursor()
    
    start_str = appointment.start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = appointment.end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO appointments (client_id, employee_id, start_time, end_time, status) 
        VALUES (?, ?, ?, ?, ?)
    """, (appointment.client.id, appointment.employee.id, start_str, end_str, appointment.status))
    
    conn.commit()
    conn.close()


def get_clients():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients')
    rows = cursor.fetchall()
    conn.close()

    clients = []
    for row in rows:
        client = Client(name=row[1], email=row[2], phone=row[3])
        client.id = row[0]
        clients.append(client)
    return clients


def get_employees():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    rows = cursor.fetchall()
    conn.close()
    
    employees = []
    for row in rows:
        availability = row[5].split(",") if row[5] else []
        emp = Employee(name=row[1], email=row[2], phone=row[3], role=row[4], availability=availability)
        emp.id = row[0]
        employees.append(emp)
    return employees



def get_appointments():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            appointments.id,
            clients.name AS client_name,
            employees.name AS employee_name,
            appointments.start_time,
            appointments.end_time,
            appointments.status
        FROM appointments
        JOIN clients ON appointments.client_id = clients.id
        JOIN employees ON appointments.employee_id = employees.id
    ''')
    appointments = cursor.fetchall()
    conn.close()
    return appointments

from datetime import datetime, timedelta

from datetime import datetime, timedelta

def is_employee_available(employee_id: int, start_time: datetime, end_time: datetime) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM appointments
        WHERE employee_id = ?
        AND status = 'Scheduled'
        AND (
            (start_time < ? AND end_time > ?)  -- Nueva cita empieza dentro de una cita existente
            OR
            (start_time < ? AND end_time > ?)  -- Nueva cita termina dentro de una cita existente
            OR
            (start_time >= ? AND end_time <= ?) -- Nueva cita está dentro de una cita existente
        )
        LIMIT 1
    """, (
        employee_id,
        end_time.strftime("%Y-%m-%d %H:%M:%S"), start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"), start_time.strftime("%Y-%m-%d %H:%M:%S"),
        start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"),
    ))

    result = cursor.fetchone()
    conn.close()

    return result is None  # Si no hay resultados, está disponible


def reset_database():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments')
    cursor.execute('DELETE FROM clients')
    cursor.execute('DELETE FROM employees')
    conn.commit()
    conn.close()

