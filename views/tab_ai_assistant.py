# views/tab_ai_assistant.py

# ui/ai_tab.py
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime, timedelta
from smartscheduler.data.database import get_client_by_name, cancel_appointments_by_client_id, cancel_appointment_by_id, get_active_appointments_by_client_id
from smartscheduler.core.ai_engine import chat_completion
from smartscheduler.core.scheduler_utils import schedule_appointment_with_validation

class AIAssistantTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.history = []
        self.pending_cancellation = None
        self.awaiting_cancellation_client = False

        self.awaiting_cancellation_which = False
        self.citas_a_cancelar = []

        self.chat_display = tk.Text(self, wrap="word", state="disabled", height=25)
        self.chat_display.pack(padx=10, pady=10, fill="both", expand=True)

        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill="x", padx=10, pady=5)

        self.entry = ttk.Entry(entry_frame)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.send_message)

        send_button = ttk.Button(entry_frame, text="Enviar", command=self.send_message)
        send_button.pack(side="right", padx=5)

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        
        self.entry.delete(0, tk.END)
        self.append_to_chat("You", user_input)
        self.history.append(("user", user_input))

         # --- PASO 1: Si estamos esperando que el usuario elija cuál cita cancelar ---
        if self.awaiting_cancellation_which:
            try:
                idx = int(user_input.strip()) - 1
                cita = self.citas_a_cancelar[idx]
                affected = cancel_appointment_by_id(cita[0])  # cita[0] es el id
                if affected:
                    reply = f"Appointment cancelled: {cita[1]} a {cita[2]} with employee ID {cita[3]}"
                else:
                    reply = "Could not cancel the appointment, perhaps is already cancelled before ."
            except Exception:
                reply = "Invalid selection. Please, insert the number of the appointment to be cancelled."
                self.history.append(("assistant", reply))
                self.append_to_chat("AI", reply)
                return
            self.awaiting_cancellation_which = False
            self.citas_a_cancelar = []
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

        # --- PASO 2: Si el usuario pide cancelar cita ---
        if "cancel" in user_input.lower() and "appointment" in user_input.lower():
            lowered = user_input.lower()
            # Extrae el nombre del cliente después de la palabra "for"
            if "for" in lowered:
                idx = lowered.find("for") + 4
                client_name = user_input[idx:].strip()
            else:
                client_name = ""
            if not client_name:
                reply = "Which client do you want to cancel an appointment for? Write the name."
                self.awaiting_cancellation_client = True
                self.history.append(("assistant", reply))
                self.append_to_chat("AI", reply)
                return

            client = get_client_by_name(client_name)
            if not client:
                reply = f"Client not found '{client_name}'."
                self.history.append(("assistant", reply))
                self.append_to_chat("AI", reply)
                return

            citas = get_active_appointments_by_client_id(client.id)
            if not citas:
                reply = f"{client_name} does not have appointments to cancel."
            elif len(citas) == 1:
                affected = cancel_appointment_by_id(citas[0][0])
                if affected:
                    reply = f"appointment cancelled: {citas[0][1]} a {citas[0][2]} with employee ID {citas[0][3]}"
                else:
                    reply = "Your appointment could not be cancelled, perhaps it was already cancelled before."
            else:
                listado = "\n".join(
                    [f"{i+1}. {c[1]} a {c[2]} with employee ID {c[3]}" for i, c in enumerate(citas)]
                )
                reply = (
                    f"{client_name} has several active appointments:\n{listado}\n"
                    "Please, insert the number of the appointment you want to cancel."
                )
                self.awaiting_cancellation_which = True
                self.citas_a_cancelar = citas
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

        # --- PASO 3: Si está esperando que el usuario escriba el cliente ---
        if self.awaiting_cancellation_client:
            client_name = user_input
            client = get_client_by_name(client_name)
            if not client:
                reply = f"Client was not found '{client_name}'."
                self.awaiting_cancellation_client = False
                self.history.append(("assistant", reply))
                self.append_to_chat("AI", reply)
                return
            citas = get_active_appointments_by_client_id(client.id)
            if not citas:
                reply = f"{client_name} have no appointments to cancel."
                self.awaiting_cancellation_client = False
            elif len(citas) == 1:
                affected = cancel_appointment_by_id(citas[0][0])
                if affected:
                    reply = f"Appointment cancelled: {citas[0][1]} a {citas[0][2]} with employee ID {citas[0][3]}"
                else:
                    reply = "Your appointment could not be cancelled, perhaps it was already cancelled previously."
                self.awaiting_cancellation_client = False
            else:
                listado = "\n".join(
                    [f"{i+1}. {c[1]} a {c[2]} with employee ID {c[3]}" for i, c in enumerate(citas)]
                )
                reply = (
                    f"{client_name} have several active appointments:\n{listado}\n"
                    "Please, insert the number of the appointment you want to cancel"
                )
                self.awaiting_cancellation_which = True
                self.citas_a_cancelar = citas
                self.awaiting_cancellation_client = False
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

        # --- AGENDADOR ORIGINAL ---
        schedule_reply = self.try_schedule_from_input(user_input)
        if schedule_reply:
            self.history.append(("assistant", schedule_reply))
            self.append_to_chat("AI", schedule_reply)
            return

        # --- CANCELACIÓN MASIVA (MANTENIDA POR SI QUIERES EL FLUJO ANTIGUO) ---
        if self.pending_cancellation:
            if user_input.lower() in ("si", "yes", "confirm", "ok"):
                client_name = self.pending_cancellation
                client = get_client_by_name(client_name)
                if client:
                    cancel_appointments_by_client_id(client.id)
                    reply = f"All appointments for {client.name} have been cancelled."
                else:
                    reply = f"No client found with the name '{client_name}'."
                self.pending_cancellation = None
            else:
                reply = "Appointment Cancellation aborted"
                self.pending_cancellation = None
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

        # --- FLUJO MASIVO OBSOLETO (PUEDES ELIMINAR SI YA NO QUIERES LA OPCIÓN) ---
        if "cancel all" in user_input.lower() and "appointments" in user_input.lower():
            lowered = user_input.lower()
            if "for" in lowered:
                idx = lowered.find("for") + 4
                client_name = user_input[idx:].strip()
            else:
                client_name = ""

            if client_name:
                reply = f"Are you sure you want to cancel all appointments for {client_name}? (Reply 'yes' to confirm)"
                self.pending_cancellation = client_name
            else:
                reply = "Which client would you like to cancel all appointments for? Please specify the name"
                self.awaiting_cancellation_client = True
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

        # --- CONTINÚA FLUJO NORMAL DEL ASSISTANT ---
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, "AI typing...\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

        self.update_idletasks()

        try:
            reply = chat_completion(self.history)
        except Exception as e:
            reply = f"[Error]: {e}"

        self.history.append(("assistant", reply))
        self.append_to_chat("AI", reply)

    def append_to_chat(self, speaker, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{speaker}: {text}\n\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def try_schedule_from_input(self, user_input):
        """
        Detecta y agenda citas a partir de mensajes tipo:
        'Schedule appointment with Laura Sanchez on 27/06/2025 at 16:00 for Adriana Vargas'
        """
        m = re.search(
            r"(?:appointment|cita)\s+with\s+([\w\s]+)\s+on\s+(\d{1,2}/\d{1,2}/\d{4})\s+at\s+(\d{1,2}(?::\d{2})?)\s*(am|pm)?(?:\s+for\s+([\w\s]+))?",
            user_input, re.IGNORECASE)
        if m:
            employee_name = m.group(1).strip()
            date_str = m.group(2).strip()
            time_str = m.group(3).strip()
            am_pm = m.group(4)
            client_name = m.group(5).strip() if m.group(5) else "Unknown Client"
            # Procesar fecha y hora
            try:
                start_date = datetime.strptime(date_str, "%d/%m/%Y")
                if am_pm:
                    start_time = datetime.strptime(time_str + " " + am_pm, "%I:%M %p" if ":" in time_str else "%I %p")
                else:
                    start_time = datetime.strptime(time_str, "%H:%M" if ":" in time_str else "%H")
                start = start_date.replace(hour=start_time.hour, minute=start_time.minute)
                end = start + timedelta(hours=1)
            except Exception as e:
                return f"Could not parse date/time: {e}"

            ok, msg = schedule_appointment_with_validation(client_name, employee_name, start, end)
            return msg

        return None