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
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL
                    )
                 ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            availability TEXT NOT NULL
                   )
              '''  )
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_clients_by_email(email:str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE email = ?', (email,))
    client = cursor.fetchone()
    print(f"Searching client by email {email}: {client}")
    conn.close()
    return client

def get_employee_by_email(email:str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees WHERE email = ?', (email,))
    employee = cursor.fetchone()
    conn.close()
    return employee

def add_client(client: Client):
    existing_client = get_clients_by_email(client.email)
    if existing_client:
        client.id = existing_client[0]  # asignar el id existente
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
        employee.id = existing_employee[0]  # asignar el id existente
        return

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO employees (name, email, phone, role, availability)
                   VALUES (?, ?, ?, ?, ?)
                   ''', 
                   (employee.name, employee.email, employee.phone, employee.role, ",".join(employee.availability)))
    employee.id = cursor.lastrowid
    conn.commit()
    conn.close()

def add_appointment(appointment: Appointment):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO appointments (client_id, employee_id, start_time
                   , end_time, status) VALUES (?, ?, ?, ?, ?)
                   ''', (appointment.client.id, appointment.employee.id, appointment.start_time.isoformat(), appointment.end_time.isoformat(), appointment.status))
    conn.commit()
    conn.close()

def get_clients():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients')
    clients = cursor.fetchall()
    conn.close()
    return clients

def get_employees():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    conn.close()
    return employees

def get_appointments():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments')
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def reset_database():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments')
    cursor.execute('DELETE FROM clients')
    cursor.execute('DELETE FROM employees')
    conn.commit()
    conn.close()


reset_database()