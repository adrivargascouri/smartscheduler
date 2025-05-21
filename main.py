import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Agrega la carpeta raíz al path

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk
from tkinter import messagebox
from data.database import (
    create_connection, add_appointment, get_appointments, add_employee,
    get_employee_by_email, get_employees, add_client, is_employee_available
)
from models.appointment import Appointment
from models.person import Client, Employee
from datetime import datetime, timedelta
from data.database import create_tables
create_tables()

# Create main window
app = tb.Window(themename="minty")
app.title("SmartScheduler")
app.geometry("600x500")

# Header
header = tb.Label(app, text="SmartScheduler", font=("Helvetica", 24, "bold"), bootstyle="primary")
header.pack(pady=20)

# Create Notebook (tabs)
notebook = ttk.Notebook(app)
notebook.pack(expand=True, fill="both", padx=20, pady=20)

# --- Tab 1: Schedule Appointment ---
tab_schedule = tb.Frame(notebook)
notebook.add(tab_schedule, text="📅 Schedule Appointment")

tb.Label(tab_schedule, text="Client Name:", bootstyle="info").grid(row=0, column=0, padx=15, pady=15, sticky="e")
name_entry = tb.Entry(tab_schedule, width=35, bootstyle="light")
name_entry.grid(row=0, column=1, padx=15, pady=15)

tb.Label(tab_schedule, text="Employee:", bootstyle="info").grid(row=1, column=0, padx=15, pady=15, sticky="e")
employee_options = {}
employee_combobox = ttk.Combobox(tab_schedule, values=[], state="readonly", width=32)
employee_combobox.grid(row=1, column=1, padx=15, pady=15)

tb.Label(tab_schedule, text="Date (dd/mm/yyyy):", bootstyle="info").grid(row=2, column=0, padx=15, pady=15, sticky="e")
date_entry = tb.Entry(tab_schedule, width=35, bootstyle="light")
date_entry.grid(row=2, column=1, padx=15, pady=15)

tb.Label(tab_schedule, text="Time (HH:MM):", bootstyle="info").grid(row=3, column=0, padx=15, pady=15, sticky="e")
time_entry = tb.Entry(tab_schedule, width=35, bootstyle="light")
time_entry.grid(row=3, column=1, padx=15, pady=15)

def load_employees():
    employees = get_employees()
    employee_options.clear()
    employee_labels = []

    for emp in employees:
        label = f"{emp[1]} ({emp[2]})"  # Nombre (Correo)
        employee_options[label] = emp[2]  # Guarda el correo
        employee_labels.append(label)

    employee_combobox['values'] = employee_labels

# Dummy employees if not present
if not get_employee_by_email("laura@example.com"):
    emp1 = Employee(name="Laura Sánchez", email="laura@example.com", phone="3011234567", role="Dentist", availability=["Monday", "Tuesday"])
    add_employee(emp1)

if not get_employee_by_email("carlos@example.com"):
    emp2 = Employee(name="Carlos Gómez", email="carlos@example.com", phone="3027654321", role="Therapist", availability=["Wednesday", "Thursday"])
    add_employee(emp2)

if not get_employee_by_email("ana@example.com"):
    emp3 = Employee(name="Ana Torres", email="ana@example.com", phone="3039876543", role="Nutritionist", availability=["Friday"])
    add_employee(emp3)

load_employees()

def schedule_appointment():
    client_name = name_entry.get()
    selected_label = employee_combobox.get()
    employee_email = employee_options.get(selected_label, "")

    date_str = date_entry.get()  # Ajusta según tu variable del calendario
    time_str = time_entry.get()

    if client_name and employee_email and date_str and time_str:
        try:
            appointment_date = datetime.strptime(date_str, "%d/%m/%Y")
            appointment_time = datetime.strptime(time_str, "%H:%M").time()
            start_time = datetime.combine(appointment_date, appointment_time)
            end_time = start_time + timedelta(hours=1)

            employee = get_employee_by_email(employee_email)
            if not employee:
                messagebox.showerror("Error", "Employee not found.")
                return

            # Validar disponibilidad
            if not is_employee_available(employee.id, start_time, end_time):
                messagebox.showerror("Error", "The employee already has an appointment at that time.")
                return

            client = Client(name=client_name, email="", phone="")
            add_client(client)

            appointment = Appointment(client, employee, start_time, end_time, "Scheduled")
            add_appointment(appointment)

            messagebox.showinfo("Appointment Scheduled", f"Appointment for {client_name} scheduled for {start_time}.")
            name_entry.delete(0, 'end')
            employee_combobox.set("")
            time_entry.delete(0, 'end')

        except ValueError:
            messagebox.showerror("Error", "Invalid date or time format.")
    else:
        messagebox.showerror("Error", "Please fill in all the fields.")

schedule_button = tb.Button(tab_schedule, text="Schedule Appointment", bootstyle="success", command=schedule_appointment)
schedule_button.grid(row=4, columnspan=2, pady=25)

# --- Tab 2: View Appointments ---
tab_view = tb.Frame(notebook)
notebook.add(tab_view, text="👁 View Appointments")

tree = ttk.Treeview(tab_view, columns=("Client", "Employee", "Start Time", "End Time", "Status"), show="headings")
tree.heading("Client", text="Client")
tree.heading("Employee", text="Employee")
tree.heading("Start Time", text="Start Time")
tree.heading("End Time", text="End Time")
tree.heading("Status", text="Status")
tree.column("Client", width=150)
tree.column("Employee", width=150)
tree.column("Start Time", width=150)
tree.column("End Time", width=150)
tree.column("Status", width=100)
tree.pack(fill="both", expand=True, padx=10, pady=10)

def load_appointments():
    appointments = get_appointments()
    for row in tree.get_children():
        tree.delete(row)
    for appointment in appointments:
        client_name = appointment[1]
        employee_name = appointment[2]
        start_time = appointment[3]
        end_time = appointment[4]
        status = appointment[5]
        tree.insert("", "end", values=(client_name, employee_name, start_time, end_time, status))

load_button = tb.Button(tab_view, text="Load Appointments", bootstyle="info", command=load_appointments)
load_button.pack(pady=10)

# --- Tab 3: Cancel Appointment ---
tab_cancel = tb.Frame(notebook)
notebook.add(tab_cancel, text="❌ Cancel Appointment")

tb.Label(tab_cancel, text="Search by Client Name:", bootstyle="info").grid(row=0, column=0, padx=15, pady=15, sticky="e")
name_cancel_entry = tb.Entry(tab_cancel, width=35, bootstyle="light")
name_cancel_entry.grid(row=0, column=1, padx=15, pady=15)

def cancel_appointment():
    client_name = name_cancel_entry.get()
    if client_name:
        conn = create_connection()
        cursor = conn.cursor()

        # Verifica si existe alguna cita para ese cliente
        cursor.execute('''
            SELECT a.id FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE c.name = ?
        ''', (client_name,))
        appointments = cursor.fetchall()

        if appointments:
            # Si existen, cancelar (eliminar)
            cursor.execute('''
                DELETE FROM appointments
                WHERE client_id IN (SELECT id FROM clients WHERE name = ?)
            ''', (client_name,))
            conn.commit()
            messagebox.showinfo("Appointment Canceled", f"The appointment(s) for {client_name} have been canceled.")
        else:
            messagebox.showwarning("Not Found", f"No appointments found for '{client_name}'.")
        
        conn.close()
        name_cancel_entry.delete(0, 'end')
    else:
        messagebox.showerror("Error", "Please enter the name of the appointment to cancel.")

# Botón para cancelar cita
cancel_button = tb.Button(tab_cancel, text="Cancel Appointment", bootstyle="danger", command=cancel_appointment)
cancel_button.grid(row=1, columnspan=2, pady=25)


def clear_appointments():
    for row in tree.get_children():
        tree.delete(row)

clear_button = tb.Button(tab_view, text="Clear List", bootstyle="warning", command=clear_appointments)
clear_button.pack(pady=5)

# Run the app
app.mainloop()

