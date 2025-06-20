import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from tkinter import ttk, messagebox, PhotoImage
from datetime import datetime, timedelta
import tkinter as tk
from smartscheduler.views.employee_calendar import show_employee_calendar_window
from ics import Calendar, Event
from tkinter import filedialog

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

from smartscheduler.core.scheduler_utils import schedule_appointment_with_validation

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

def seed_employees():
    from smartscheduler.models.person import Employee
    from smartscheduler.data.database import add_employee, get_employees

    if get_employees():
        return  # Ya hay empleados, no hagas nada

    default_availability = {
        "Monday": ["09:00-13:00", "15:00-18:00"],
        "Tuesday": ["09:00-13:00", "15:00-18:00"],
        "Wednesday": ["09:00-13:00", "15:00-18:00"],
        "Thursday": ["09:00-13:00", "15:00-18:00"],
        "Friday": ["09:00-13:00", "15:00-18:00"]
    }

    employees = [
        Employee(name="Laura Sanchez", email="laura@clinic.com", phone="123456789", role="Doctor", availability=default_availability),
        Employee(name="Carlos Perez", email="carlos@clinic.com", phone="987654321", role="Therapist", availability=default_availability),
    ]

    for emp in employees:
        add_employee(emp)

# Después de create_tables()
create_tables()
seed_employees()

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

    # Aquí llamamos la función centralizada
    ok, msg = schedule_appointment_with_validation(client_name, employee_label, start_time, end_time)
    if not ok:
        messagebox.showerror("No disponible", msg)
        return

    messagebox.showinfo("Scheduled", msg)

    # Limpiar campos
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

from ics import Calendar, Event
from datetime import datetime, timezone

def export_appoint_selected():
    seleccionadas = tree.selection()
    if not seleccionadas:
        messagebox.showwarning("No selection", "Select at least an appointment to export.")
        return

    calendar = Calendar()
    for item_id in seleccionadas:
        cita = tree.item(item_id, "values")
        cliente = cita[0]
        empleado = cita[1]
        inicio_str = cita[2]  # formato: 'YYYY-MM-DD HH:MM:SS'
        fin_str = cita[3]
        estado = cita[4]

        if estado.lower() == "cancelled":
            continue

        try:
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            fin = datetime.strptime(fin_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            continue

        event = Event()
        event.name = f"Cita: {cliente} con {empleado}"
        event.begin = inicio
        event.end = fin
        event.description = f"Estado: {estado}\nCliente: {cliente}\nEmpleado: {empleado}"
        event.created = datetime.utcnow().replace(tzinfo=timezone.utc)  # Esto agrega DTSTAMP
        # event.location = "Consultorio 123"  # Si tienes ubicación

        calendar.events.add(event)

    if not calendar.events:
        messagebox.showinfo("No events", "No appointments selected to export.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".ics",
        filetypes=[("iCalendar files", "*.ics")],
        title="Save appointments as..."
    )
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(calendar.serialize())
        messagebox.showinfo("Successful export", f"Appointments exported to {filepath}")

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
        style = ttk.Style()
        style.layout('TNotebook.Tab', [])
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

    tb.Button(nav_frame, text="View appointments", bootstyle="info-outline", width=16, command=lambda: switch_tab(0)).pack(side="left", padx=8)
    tb.Button(nav_frame, text="AI Assistant", bootstyle="warning-outline", width=16, command=lambda: switch_tab(1)).pack(side="left", padx=8)
    
    # TAB 0 – VIEW APPOINTMENTS
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
    tb.Button(btn_frame, text="📤 Export Selected", bootstyle="primary", command=export_appoint_selected).grid(row=0, column=3, padx=10)
    refresh_tree()

    # TAB 1 – AI ASSISTANT
    from smartscheduler.views.tab_ai_assistant import AIAssistantTab
    ai_tab = AIAssistantTab(notebook)
    notebook.add(ai_tab, text="🤖 AI Assistant")
    
    #TAB 2 - EMPLOYEE CALENDAR 
    tb.Button(
    nav_frame,  
    text="Employees calendar",
    bootstyle="info-outline",
    width=24,
    command=lambda: show_employee_calendar_window(root)
).pack(side="left", padx=8)
    
def show_welcome():
    root.configure(bg="#e7f0fd")  

    welcome_frame = tb.Frame(root, bootstyle="light")
    welcome_frame.pack(expand=True, fill="both")

    container = tb.Frame(welcome_frame, bootstyle="light")
    container.place(relx=0.5, rely=0.5, anchor="center")

    # Logo o ilustración (opcional)
    try:
        img = PhotoImage(file="calendar.png")
        tk.Label(container, image=img, bg="#e7f0fd").pack(pady=(0, 18))
        container.image = img 
    except Exception:
        pass

    # ANIMATED TITLE
    title_text = "¡Welcome to Smartscheduler!"
    title_label = tb.Label(
        container,
        text="",
        font=("Segoe UI Bold", 28),
        foreground="#2776b5",
        background="#e7f0fd"
    )
    title_label.pack(pady=(0, 8))

    # EFECT TYPEWRITER
    def type_text(text, label, idx=0):
        if idx <= len(text):
            label.config(text=text[:idx])
            container.after(40, lambda: type_text(text, label, idx+1))

    subtitle_label = tb.Label(
        container,
        text="Manage your appointments easily and quickly",
        font=("Segoe UI", 14),
        foreground="#555",
        background="#e7f0fd"
    )

    def enter():
        welcome_frame.destroy()
        launch_dashboard()

    btn_entrar = tb.Button(
        container,
        text="🚀 Enter",
        bootstyle="success",
        width=22,
        padding=10,
        command=enter
    )

    # FADE-IN ANIMATION
    def show_subtitle():
        subtitle_label.pack(pady=(0, 25))
        container.after(300, show_button)

    def show_button():
        btn_entrar.pack()
        container.after(200, show_phrase)

    # motivational frase
    phrase_label = tb.Label(
        container,
        text="Ready to boost your productivity? 🎉",
        font=("Segoe UI Italic", 11),
        foreground="#888",
        background="#e7f0fd"
    )
    def show_phrase():
        phrase_label.pack(pady=(20, 0))

    # Start animation
    container.after(300, lambda: type_text(title_text, title_label))
    container.after(1300, show_subtitle)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    show_welcome()
    root.mainloop()