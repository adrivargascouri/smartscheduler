# views/tab_ai_assistant.py

# ui/ai_tab.py
import tkinter as tk
from tkinter import ttk
from smartscheduler.data.database import get_client_by_name, cancel_appointments_by_client_id
from smartscheduler.core.ai_engine import chat_completion

class AIAssistantTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.history = []
        self.pending_cancellation = None
        self.awaiting_cancellation_client = False

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

        if self.awaiting_cancellation_client:
            client_name = user_input
            reply = f"Are you sure you want to cancel all appointments for {client_name}? (Reply 'yes' to confirm)"
            self.pending_cancellation = client_name
            self.awaiting_cancellation_client = False
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return
        
    # --- Nuevo bloque para cancelar citas ---
        if self.pending_cancellation:
            if user_input.lower()in ("si","yes","confirm","ok"):
                client_name = self.pending_cancellation
                client = get_client_by_name(client_name)
                if client:
                    cancel_appointments_by_client_id(client.id)
                    reply = f"All appointments for {client.name} have been cancelled."
                else:
                    reply = f"No client found with the name '{client_name}'."
                self.pending_cancellation = None
            else:
                reply = "Appointment Cancelation aborted"
                self.pending_cancellation = None
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return
    
        if "cancel" in user_input.lower() and "appointment" in user_input.lower():
            lowered = user_input.lower()
            if "for" in lowered:
                idx = lowered.find("for") + 4
                client_name = user_input[idx:].strip()
            else:
                client_name = ""
        
            if client_name:
                reply = f"Are you sure you want to cancel all appointments for {client_name}? (Reply 'yes) to confrim"
                self.pending_cancellation = client_name
            else:
                reply = "Which client would you like to cancel all appointments for? Please specify the name"
                self.awaiting_cancellation_client = True
            self.history.append(("assistant", reply))
            self.append_to_chat("AI", reply)
            return

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

