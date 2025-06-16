import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from tkinter import ttk, messagebox, PhotoImage
from datetime import datetime, timedelta
import tkinter as tk

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
from smartscheduler.data.database import (
    create_tables,
    add_client,
    add_employee,
    get_employee_by_email,
    get_employees,
    is_employee_available,
    add_appointment,
    get_appointments,
    update_appointment_status,
    cancel_appointments_by_client_id,
    get_client_by_name,
    STATUS_SCHEDULED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
)
from smartscheduler.models.appointment import Appointment
from smartscheduler.models.person import Client, Employee

# ---------------------------------------------------------------------------
# Bootstrap DB
# ---------------------------------------------------------------------------
create_tables()

CURRENT_THEME = "superhero"  # Try others like "cyborg", "morph", "minty"
root = tb.Window(themename=CURRENT_THEME)
root.title("SmartScheduler")
root.geometry("950x700")
root.minsize(900, 600)

tree = None

# ---------------------------------------------------------------------------
# Helper callbacks
# ---------------------------------------------------------------------------
def schedule_appointment(name_entry, employee_opts, employee_combo, date_picker, time_combo):
    client_name = name_entry.get().strip()
    employee_label = employee_combo.get()
    employee_email = employee_opts.get(employee_label, "")

    date_str = date_picker.entry.get().strip()
    time_str = time_combo.get().strip()

    if not all((client_name, employee_email, date_str, time_str)):
        messagebox.showerror("Error", "Please fill in all the fields.")
        return

    try:
        date_selected = datetime.strptime(date_str, "%d/%m/%Y").date()
        time_selected = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        messagebox.showerror("Error", "Invalid date or time format.")
        return

    start_time = datetime.combine(date_selected, time_selected)
    end_time = start_time + timedelta(hours=1)

    employee = get_employee_by_email(employee_email)
    if not employee:
        messagebox.showerror("Error", "Employee not found.")
        return

    if not is_employee_available(employee.id, start_time, end_time):
        messagebox.showerror("Error", "The employee already has an appointment at that time.")
        return

    client = Client(name=client_name)
    add_client(client)

    appt = Appointment(client, employee, start_time, end_time, STATUS_SCHEDULED)
    add_appointment(appt)

    messagebox.showinfo(
        "Scheduled",
        f"Appointment booked for {client_name} on {start_time:%d/%m/%Y %H:%M}."
    )

    name_entry.delete(0, "end")
    employee_combo.set("")
    date_picker.entry.delete(0, "end")
    date_picker.entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
    time_combo.set("")

    refresh_tree()


def refresh_tree():
    tree.delete(*tree.get_children())
    for ap in get_appointments():
        ap_id, client_name, employee_name, start, end, status = ap
        tag = {"Scheduled": "scheduled", "Completed": "completed", "Cancelled": "cancelled"}.get(status, "")
        tree.insert(
            "",
            "end",
            iid=ap_id,
            values=(client_name, employee_name, start, end, status),
            tags=(tag,)
        )

    tree.tag_configure("scheduled", background="#0099ff", foreground="#fff")
    tree.tag_configure("completed", background="#43d97b", foreground="#fff")
    tree.tag_configure("cancelled", background="#e04f5f", foreground="#fff")


def mark_selected(new_status: str):
    selected_iid = tree.focus()
    if not selected_iid:
        messagebox.showerror("Error", "Please select an appointment.")
        return

    update_appointment_status(int(selected_iid), new_status)
    refresh_tree()
    messagebox.showinfo("Success", f"Appointment marked as {new_status}.")


def cancel_by_client(name_entry):

    client_name = name_entry.get().strip()
    if not client_name:
        messagebox.showerror("Error", "Please enter the client's name.")
        return

    client = get_client_by_name(client_name)
    if not client:
        messagebox.showinfo("Not Found", f"No client found with name '{client_name}'.")
        return

    affected = cancel_appointments_by_client_id(client.id)
    msg = ("No scheduled appointments were found."
           if affected == 0 else
           f"{affected} appointment(s) cancelled.")
    messagebox.showinfo("Cancelled", msg)
    refresh_tree()
    name_entry.delete(0, "end")

# ---------------------------------------------------------------------------
# Main Dashboard Layout
# ---------------------------------------------------------------------------
def launch_dashboard():
    # HEADER (navbar)
    header = tb.Frame(root, bootstyle="dark")
    header.pack(side="top", fill="x")

    logo_img = None
    try:
        logo_img = PhotoImage(file="logo.png").subsample(8, 8)  # If you have a PNG logo
        tb.Label(header, image=logo_img).pack(side="left", padx=12, pady=8)
    except Exception:
        pass  # Ignore if no logo

    tb.Label(header, text="SmartScheduler", font=("Helvetica", 24, "bold")).pack(side="left", padx=8, pady=4)
    
    def toggle_theme():
        global CURRENT_THEME
        CURRENT_THEME = "cyborg" if CURRENT_THEME == "superhero" else "superhero"
        root.style.theme_use(CURRENT_THEME)
    tb.Button(header, text="🌓 Theme", bootstyle="secondary", command=toggle_theme).pack(side="right", padx=16, pady=10)

    # --- MAIN BODY ---
    main_frame = tb.Frame(root)
    main_frame.pack(expand=True, fill="both", padx=0, pady=0)

    # --- SUMMARY CARDS ---
    cards_frame = tb.Frame(main_frame)
    cards_frame.pack(fill="x", padx=30, pady=18)

    # Data for summary cards
    employees = get_employees()
    clients_count = len(set(ap[1] for ap in get_appointments()))
    appointments_today = sum(
        1 for ap in get_appointments()
        if datetime.strptime(ap[3], "%Y-%m-%d %H:%M:%S").date() == datetime.now().date()
    )
    available_employees = len(employees)

    cards = [
        ("👩‍⚕️ Employees", len(employees), "info"),
        ("🧑‍🤝‍🧑 Clients", clients_count, "success"),
        ("📅 Appointments today", appointments_today, "warning"),
        ("🟢 Available", available_employees, "primary"),
    ]

    for i, (title, value, style) in enumerate(cards):
        card = tb.Frame(cards_frame)  # No outline bootstyle for Frame!
        card.grid(row=0, column=i, padx=18, ipadx=10, ipady=6, sticky="ew")
        tb.Label(card, text=title, font=("Helvetica", 12, "bold"), bootstyle=style).pack(anchor="w", padx=6, pady=(6, 0))
        tb.Label(card, text=str(value), font=("Helvetica", 18, "bold")).pack(anchor="w", padx=6, pady=(2, 8))

    # --- MAIN NAVIGATION (buttons) ---
    nav_frame = tb.Frame(main_frame)
    nav_frame.pack(fill="x", padx=30, pady=(0, 12))

    # --- MAIN TABS ---
    notebook = ttk.Notebook(main_frame)
    notebook.pack(expand=True, fill="both", padx=30, pady=0)

    # Hide tabs visually
    style = ttk.Style()
    style.layout('TNotebook.Tab', [])

    def switch_tab(idx):
        notebook.select(idx)

    tb.Button(nav_frame, text="New appointment", bootstyle="success-outline", width=16, command=lambda: switch_tab(0)).pack(side="left", padx=8)
    tb.Button(nav_frame, text="View appointments", bootstyle="info-outline", width=16, command=lambda: switch_tab(1)).pack(side="left", padx=8)
    tb.Button(nav_frame, text="Cancel by client", bootstyle="danger-outline", width=20, command=lambda: switch_tab(2)).pack(side="left", padx=8)
    tb.Button(nav_frame, text="AI Assistant", bootstyle="warning-outline", width=16, command=lambda: switch_tab(3)).pack(side="left", padx=8)

    # TAB 0 – SCHEDULE
    tab_schedule = tb.Frame(notebook)
    notebook.add(tab_schedule, text="📅 New appointment")

    tb.Label(tab_schedule, text="Client name:", bootstyle="info").grid(row=0, column=0, padx=15, pady=15, sticky="e")
    name_entry = tb.Entry(tab_schedule, width=35, bootstyle="light")
    name_entry.grid(row=0, column=1, padx=15, pady=15)

    tb.Label(tab_schedule, text="Employee:", bootstyle="info").grid(row=1, column=0, padx=15, pady=15, sticky="e")
    employee_combo = ttk.Combobox(tab_schedule, values=[], state="readonly", width=32)
    employee_combo.grid(row=1, column=1, padx=15, pady=15)

    tb.Label(tab_schedule, text="Date:", bootstyle="info").grid(row=2, column=0, padx=15, pady=15, sticky="e")
    date_picker = DateEntry(tab_schedule, firstweekday=0, dateformat="%d/%m/%Y", bootstyle="light")
    date_picker.grid(row=2, column=1, padx=15, pady=15)

    tb.Label(tab_schedule, text="Time:", bootstyle="info").grid(row=3, column=0, padx=15, pady=15, sticky="e")
    time_values = [f"{h:02d}:{m:02d}" for h in range(8, 21) for m in (0, 30)]
    time_combo = ttk.Combobox(tab_schedule, values=time_values, state="readonly", width=32)
    time_combo.grid(row=3, column=1, padx=15, pady=15)

    # Populate employee list
    employee_options = {}
    def load_employees():
        employee_options.clear()
        labels = []
        for emp in get_employees():
            label = f"{emp.name} ({emp.email})"
            employee_options[label] = emp.email
            labels.append(label)
        employee_combo["values"] = labels
    # Demo employees if DB is empty
    if not get_employee_by_email("laura@example.com"):
        add_employee(Employee("Laura Sanchez", "laura@example.com", "3011234567", "Dentist", ["Monday", "Tuesday"]))
    if not get_employee_by_email("carlos@example.com"):
        add_employee(Employee("Carlos Gomez", "carlos@example.com", "3027654321", "Therapist", ["Wednesday", "Thursday"]))
    if not get_employee_by_email("ana@example.com"):
        add_employee(Employee("Ana Torres", "ana@example.com", "3039876543", "Nutritionist", ["Friday"]))
    load_employees()

    tb.Button(
        tab_schedule,
        text="Schedule appointment",
        bootstyle="success",
        width=20,
        command=lambda: schedule_appointment(name_entry, employee_options, employee_combo, date_picker, time_combo)
    ).grid(row=4, columnspan=2, pady=25)

    # TAB 1 – VIEW APPOINTMENTS
    tab_view = tb.Frame(notebook)
    notebook.add(tab_view, text="👁 View appointments")

    global tree
    tree = ttk.Treeview(tab_view, columns=("Client", "Employee", "Start", "End", "Status"), show="headings")
    for col, w in zip(("Client", "Employee", "Start", "End", "Status"), (140, 140, 140, 140, 100)):
        tree.heading(col, text=col)
        tree.column(col, width=w)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    btn_frame = tb.Frame(tab_view)
    btn_frame.pack(pady=10)
    tb.Button(btn_frame, text="🔄 Refresh", bootstyle="info", command=refresh_tree).grid(row=0, column=0, padx=10)
    tb.Button(btn_frame, text="✔️ Complete", bootstyle="success", command=lambda: mark_selected(STATUS_COMPLETED)).grid(row=0, column=1, padx=10)
    tb.Button(btn_frame, text="❌ Cancel", bootstyle="danger", command=lambda: mark_selected(STATUS_CANCELLED)).grid(row=0, column=2, padx=10)
    refresh_tree()

    # TAB 2 – CANCEL BY CLIENT
    tab_cancel = tb.Frame(notebook)
    notebook.add(tab_cancel, text="❌ Cancel by client")

    tb.Label(tab_cancel, text="Client name:", bootstyle="info").grid(row=0, column=0, padx=15, pady=15, sticky="e")
    name_cancel_entry = tb.Entry(tab_cancel, width=35, bootstyle="light")
    name_cancel_entry.grid(row=0, column=1, padx=15, pady=15)
    tb.Button(
        tab_cancel,
        text="Cancel appointments",
        bootstyle="danger",
        command=lambda: cancel_by_client(name_cancel_entry)
    ).grid(row=1, columnspan=2, pady=10)

    # TAB 3 – AI ASSISTANT
    from smartscheduler.views.tab_ai_assistant import AIAssistantTab
    ai_tab = AIAssistantTab(notebook)
    notebook.add(ai_tab, text="🤖 AI Assistant")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    launch_dashboard()
    root.mainloop()