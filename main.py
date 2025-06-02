import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
from data.database import (
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
    add_user,
    validate_user,
    get_user_by_username,
    STATUS_SCHEDULED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
)
from models.appointment import Appointment
from models.person import Client, Employee

# ---------------------------------------------------------------------------
# Bootstrap DB
# ---------------------------------------------------------------------------
create_tables()

CURRENT_THEME = "minty"
root = tb.Window(themename=CURRENT_THEME)
root.withdraw()  # hidden until login success

tree = None
user_role = None  # admin / employee / etc.


# ---------------------------------------------------------------------------
# Helper callbacks
# ---------------------------------------------------------------------------
def schedule_appointment(
    name_entry,
    employee_opts,
    employee_combo,
    date_picker,
    time_combo,
):
    """Validate inputs, check availability and persist."""
    client_name = name_entry.get().strip()
    employee_label = employee_combo.get()
    employee_email = employee_opts.get(employee_label, "")

    # ---- Fecha y hora elegidas ----
    date_str = date_picker.entry.get().strip()          # dd/mm/yyyy
    time_str = time_combo.get().strip()                 # HH:MM

    if not all((client_name, employee_email, date_str, time_str)):
        messagebox.showerror("Error", "Please fill in all the fields.")
        return

    # Parseo fecha y hora
    try:
        date_selected = datetime.strptime(date_str, "%d/%m/%Y").date()
        time_selected = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        messagebox.showerror("Error", "Invalid date or time format.")
        return

    start_time = datetime.combine(date_selected, time_selected)
    end_time = start_time + timedelta(hours=1)

    # ---- Disponibilidad ----
    employee = get_employee_by_email(employee_email)
    if not employee:
        messagebox.showerror("Error", "Employee not found.")
        return

    if not is_employee_available(employee.id, start_time, end_time):
        messagebox.showerror(
            "Error",
            "The employee already has an appointment at that time."
        )
        return

    # ---- Persistencia ----
    client = Client(name=client_name)
    add_client(client)

    appt = Appointment(client, employee, start_time, end_time, STATUS_SCHEDULED)
    add_appointment(appt)

    messagebox.showinfo(
        "Scheduled",
        f"Appointment booked for {client_name} on {start_time:%d/%m/%Y %H:%M}."
    )

    # Reset inputs
    name_entry.delete(0, "end")
    employee_combo.set("")
    date_picker.entry.delete(0, "end")
    date_picker.entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
    time_combo.set("")


def refresh_tree():
    """Reload all appointments into the Treeview."""
    tree.delete(*tree.get_children())
    for ap in get_appointments():
        ap_id, client_name, employee_name, start, end, status = ap
        tag = {"Scheduled": "scheduled",
               "Completed": "completed",
               "Cancelled": "cancelled"}.get(status, "")
        tree.insert(
            "",
            "end",
            iid=ap_id,
            values=(client_name, employee_name, start, end, status),
            tags=(tag,)
        )

    tree.tag_configure("scheduled", background="#e0f7fa")
    tree.tag_configure("completed", background="#d0f8ce")
    tree.tag_configure("cancelled", background="#ffcdd2")


def mark_selected(new_status: str):
    selected_iid = tree.focus()
    if not selected_iid:
        messagebox.showerror("Error", "Please select an appointment.")
        return

    update_appointment_status(int(selected_iid), new_status)
    refresh_tree()
    messagebox.showinfo("Success", f"Appointment marked as {new_status}.")


def cancel_by_client(name_entry):
    from data.database import get_client_by_name

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
# Login dialog
# ---------------------------------------------------------------------------
def login_dialog():
    login = tb.Toplevel()
    login.title("Login")
    login.geometry("320x210")
    login.resizable(False, False)

    tb.Label(login, text="Username:", bootstyle="info").pack(pady=(15, 5))
    username_entry = tb.Entry(login, width=24)
    username_entry.pack(pady=5)
    username_entry.focus()

    tb.Label(login, text="Password:", bootstyle="info").pack(pady=5)
    password_entry = tb.Entry(login, show="*", width=24)
    password_entry.pack(pady=5)

    def attempt(event=None):
        global user_role
        user = username_entry.get()
        pwd = password_entry.get()
        role = validate_user(user, pwd)
        if role:
            user_role = role
            login.destroy()
            launch_main_app()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    # Bind <Return> key
    username_entry.bind("<Return>", attempt)
    password_entry.bind("<Return>", attempt)

    tb.Button(
        login,
        text="Acceder",
        bootstyle="primary",
        width=18,
        command=attempt
    ).pack(pady=15)

    login.grab_set()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
def launch_main_app():
    global tree, CURRENT_THEME

    root.deiconify()
    root.title("SmartScheduler")
    root.geometry("720x560")

    tb.Label(root, text="SmartScheduler", font=("Helvetica", 24, "bold"),
             bootstyle="primary").pack(pady=20)

    # Theme toggle
    def toggle_theme():
        global CURRENT_THEME
        CURRENT_THEME = "darkly" if CURRENT_THEME == "minty" else "minty"
        root.style.theme_use(CURRENT_THEME)

    tb.Button(root, text="🌓 Change Theme", bootstyle="secondary",
              command=toggle_theme).pack(pady=10)

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=20, pady=20)

    # ========================================================================
    # TAB 1 – Schedule
    # ========================================================================
    tab_schedule = tb.Frame(notebook)
    notebook.add(tab_schedule, text="📅 Schedule")

    # Client name
    tb.Label(tab_schedule, text="Client Name:", bootstyle="info")\
        .grid(row=0, column=0, padx=15, pady=15, sticky="e")
    name_entry = tb.Entry(tab_schedule, width=35, bootstyle="light")
    name_entry.grid(row=0, column=1, padx=15, pady=15)

    # Employee
    tb.Label(tab_schedule, text="Employee:", bootstyle="info")\
        .grid(row=1, column=0, padx=15, pady=15, sticky="e")
    employee_combo = ttk.Combobox(tab_schedule, values=[],
                                  state="readonly", width=32)
    employee_combo.grid(row=1, column=1, padx=15, pady=15)

    # Date
    tb.Label(tab_schedule, text="Date:", bootstyle="info")\
        .grid(row=2, column=0, padx=15, pady=15, sticky="e")
    date_picker = DateEntry(tab_schedule, firstweekday=0,
                            dateformat="%d/%m/%Y", bootstyle="light")
    date_picker.grid(row=2, column=1, padx=15, pady=15)

    # Time
    tb.Label(tab_schedule, text="Time:", bootstyle="info")\
        .grid(row=3, column=0, padx=15, pady=15, sticky="e")
    time_values = [f"{h:02d}:{m:02d}" for h in range(8, 21) for m in (0, 30)]
    time_combo = ttk.Combobox(tab_schedule, values=time_values,
                              state="readonly", width=32)
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

    # Demo employees if DB empty
    if not get_employee_by_email("laura@example.com"):
        add_employee(Employee("Laura Sánchez", "laura@example.com",
                              "3011234567", "Dentist", ["Monday", "Tuesday"]))
    if not get_employee_by_email("carlos@example.com"):
        add_employee(Employee("Carlos Gómez", "carlos@example.com",
                              "3027654321", "Therapist", ["Wednesday", "Thursday"]))
    if not get_employee_by_email("ana@example.com"):
        add_employee(Employee("Ana Torres", "ana@example.com",
                              "3039876543", "Nutritionist", ["Friday"]))

    load_employees()

    # Schedule button
    tb.Button(
        tab_schedule,
        text="Schedule Appointment",
        bootstyle="success",
        command=lambda: schedule_appointment(
            name_entry, employee_options, employee_combo,
            date_picker, time_combo
        )
    ).grid(row=4, columnspan=2, pady=25)

    # ========================================================================
    # TAB 2 – View appointments
    # ========================================================================
    tab_view = tb.Frame(notebook)
    notebook.add(tab_view, text="👁 View")

    tree = ttk.Treeview(tab_view, columns=("Client", "Employee", "Start",
                                           "End", "Status"), show="headings")
    for col, w in zip(("Client", "Employee", "Start", "End", "Status"),
                      (150, 150, 150, 150, 100)):
        tree.heading(col, text=col)
        tree.column(col, width=w)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    btn_frame = tb.Frame(tab_view)
    btn_frame.pack(pady=10)
    tb.Button(btn_frame, text="🔄 Refresh", bootstyle="info",
              command=refresh_tree).grid(row=0, column=0, padx=10)
    tb.Button(btn_frame, text="✔️ Complete", bootstyle="success",
              command=lambda: mark_selected(STATUS_COMPLETED))\
        .grid(row=0, column=1, padx=10)
    tb.Button(btn_frame, text="❌ Cancel", bootstyle="danger",
              command=lambda: mark_selected(STATUS_CANCELLED))\
        .grid(row=0, column=2, padx=10)

    refresh_tree()

    # ========================================================================
    # TAB 3 – Cancel by client
    # ========================================================================
    if user_role != "employee":
        tab_cancel = tb.Frame(notebook)
        notebook.add(tab_cancel, text="❌ Cancel by Client")

        tb.Label(tab_cancel, text="Client name:", bootstyle="info")\
            .grid(row=0, column=0, padx=15, pady=15, sticky="e")
        name_cancel_entry = tb.Entry(tab_cancel, width=35, bootstyle="light")
        name_cancel_entry.grid(row=0, column=1, padx=15, pady=15)

        tb.Button(
            tab_cancel,
            text="Cancel appointments",
            bootstyle="danger",
            command=lambda: cancel_by_client(name_cancel_entry)
        ).grid(row=1, columnspan=2, pady=10)

    if user_role == "employee":
        notebook.hide(tab_schedule)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not get_user_by_username("admin"):
        add_user("admin", "admin", "admin")

    login_dialog()
    root.mainloop()
