import ttkbootstrap as tb
from tkinter import ttk
from datetime import datetime, timedelta, time
from smartscheduler.data.database import get_appointments, get_employees

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_BLOCKS = [f"{h:02d}:00" for h in range(8, 21)]  # 08:00 a 20:00

def parse_block(block: str):
    """Devuelve tuplas (hora_inicio, hora_fin) de un string '09:00-12:00'."""
    try:
        start, end = block.split("-")
        return datetime.strptime(start, "%H:%M").time(), datetime.strptime(end, "%H:%M").time()
    except Exception:
        return None, None

def block_is_occupied(block_start, block_end, citas):
    """True si hay una cita que se solapa con este bloque."""
    for cita_start, cita_end in citas:
        if (cita_start < block_end and cita_end > block_start):
            return True
    return False

def show_employee_calendar_window(root):
    # Ventana principal
    win = tb.Toplevel(root)
    win.title("Calendario de empleados")
    win.geometry("950x600")

    # Selección de empleado
    employees = get_employees()
    emp_names = [f"{e.name} ({e.email})" for e in employees]
    sel_emp = tb.StringVar(value=emp_names[0] if emp_names else "")
    sel_week = tb.StringVar()

    # Semana actual (lunes)
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sel_week.set(monday.strftime("%Y-%m-%d"))

    def get_selected_employee():
        name = sel_emp.get()
        for e in employees:
            if f"{e.name} ({e.email})" == name:
                return e
        return None

    def refresh_calendar():
        for widget in frame_calendar.winfo_children():
            widget.destroy()
        employee = get_selected_employee()
        print("Empleado:", employee.name)
        print("Availability", employee.availability)
        if not employee:
            return
        week_start = datetime.strptime(sel_week.get(), "%Y-%m-%d").date()
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        # Título días
        for i, day in enumerate(DAYS):
            date_str = week_days[i].strftime("%d/%m")
            l = ttk.Label(frame_calendar, text=f"{day}\n{date_str}", anchor="center")
            l.grid(row=0, column=i+1, padx=2, pady=2)
        # Horas
        for j, hour in enumerate(HOUR_BLOCKS):
            l = ttk.Label(frame_calendar, text=hour, anchor="center")
            l.grid(row=j+1, column=0, padx=2, pady=2)
        # Celdas: disponibilidad
        # Consigue citas de ese empleado esa semana
        citas = []
        for ap in get_appointments():
            # ap: (id, client_name, employee_name, start, end, status)
            emp_name = ap[2]
            if emp_name == employee.name:
                start_dt = datetime.strptime(ap[3], "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(ap[4], "%Y-%m-%d %H:%M:%S")
                if week_start <= start_dt.date() <= week_start + timedelta(days=6):
                    citas.append((start_dt, end_dt))
        for i, day in enumerate(DAYS):
            this_date = week_days[i]
            blocks = employee.availability.get(day, [])
            # Lista de intervalos reales de disponibilidad para ese día
            available_intervals = []
            for block in blocks:
                h_ini, h_fin = parse_block(block)
                if h_ini is not None:
                    available_intervals.append((h_ini, h_fin))
            for j, hour in enumerate(HOUR_BLOCKS):
                block_time = datetime.combine(this_date, datetime.strptime(hour, "%H:%M").time())
                siguiente = block_time + timedelta(hours=1)
                block_start_time = block_time.time()
                block_end_time = siguiente.time()
                # ¿Está este bloque dentro de la disponibilidad?
                disp = False
                for h_ini, h_fin in available_intervals:
                    # El bloque debe estar completamente contenido en el intervalo de disponibilidad
                    if h_ini <= block_start_time < h_fin and block_end_time <= h_fin:
                        disp = True
                        break
                ocupado = block_is_occupied(block_time, siguiente, citas)
                #print(f"{day} {hour} - disp: {disp}, ocupado: {ocupado}")
                if ocupado:
                    color = "danger"
                    text= ""
                    state = "disabled"
                elif disp:
                    color = "success"
                    text = ""
                    state = "normal"
                else:
                    color = "secondary"
                    text = "-"
                    state = "disabled"

                btn = tb.Button(
                    frame_calendar,
                    text=text,
                    width=4,
                    bootstyle=color,
                    state=state
                )
                btn.grid(row=j+1, column=i+1, padx=1, pady=1)

    # Selector empleado
    frame_top = tb.Frame(win)
    frame_top.pack(pady=10)
    ttk.Label(frame_top, text="Empleado:").pack(side="left", padx=5)
    emp_cb = ttk.Combobox(frame_top, textvariable=sel_emp, values=emp_names, state="readonly", width=32)
    emp_cb.pack(side="left", padx=5)
    ttk.Label(frame_top, text="Semana:").pack(side="left", padx=5)
    week_entry = ttk.Entry(frame_top, textvariable=sel_week, width=12)
    week_entry.pack(side="left", padx=5)
    def prev_week():
        wk = datetime.strptime(sel_week.get(), "%Y-%m-%d").date()
        new_wk = wk - timedelta(days=7)
        sel_week.set(new_wk.strftime("%Y-%m-%d"))
        refresh_calendar()
    def next_week():
        wk = datetime.strptime(sel_week.get(), "%Y-%m-%d").date()
        new_wk = wk + timedelta(days=7)
        sel_week.set(new_wk.strftime("%Y-%m-%d"))
        refresh_calendar()
    tb.Button(frame_top, text="⏪", bootstyle="secondary", command=prev_week).pack(side="left", padx=5)
    tb.Button(frame_top, text="⏩", bootstyle="secondary", command=next_week).pack(side="left", padx=5)
    tb.Button(frame_top, text="Mostrar", bootstyle="primary", command=refresh_calendar).pack(side="left", padx=10)

    # Calendario
    frame_calendar = tb.Frame(win)
    frame_calendar.pack(padx=10, pady=10, fill="both", expand=True)

    # Inicial
    emp_cb.bind("<<ComboboxSelected>>", lambda e: refresh_calendar())
    refresh_calendar()