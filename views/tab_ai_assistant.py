# views/tab_ai_assistant.py

# ui/ai_tab.py
import tkinter as tk
from tkinter import ttk
from smartscheduler.core.ai_engine import chat_completion

class AIAssistantTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.history = []

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

