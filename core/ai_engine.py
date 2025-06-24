import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import unicodedata

from smartscheduler.models.person import Client, Employee
from smartscheduler.models.appointment import Appointment
from smartscheduler.data.database import (
    get_employees,
    is_employee_available,
    add_client,
    STATUS_SCHEDULED,
)
from smartscheduler.core.scheduler_utils import schedule_appointment_with_validation

def normalize(text):
    """
    Remove accents and convert to lowercase for name comparison.
    """
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# ---------------------------------------------------------------------------
# Simple conversational memory (for a single user)
# ---------------------------------------------------------------------------
conversation_state = {
    "employee": None,
    "date": None,
    "time": None,
    "client_name": None,
    "last_step": None,  # To know what info is missing from the user
}

def reset_state():
    """
    Reset the conversation state to initial values.
    """
    global conversation_state
    conversation_state = {
        "employee": None,
        "date": None,
        "time": None,
        "client_name": None,
        "last_step": None,
    }

def parse_date_time(text):
    """
    Extract date and time from text using regex and keywords.
    Returns (date, time) as (datetime.date, str) or (None, None).
    """
    text_lower = text.lower()
    target_date = None
    target_time = None

    # Relative date keywords
    patterns = {
        'day after tomorrow': datetime.now() + timedelta(days=2),
        'tomorrow': datetime.now() + timedelta(days=1),
        'today': datetime.now(),
        'next week': datetime.now() + timedelta(days=7),
    }
    for word, date_obj in patterns.items():
        if word in text_lower:
            target_date = date_obj.date()
            break

    # Explicit date patterns (e.g., "15/06/2025", "june 15")
    date_patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',   # 15/06/2025
        r'(\d{1,2})/(\d{1,2})',           # 15/06
        r'friday (\d{1,2})',
        r'saturday (\d{1,2})',
        r'sunday (\d{1,2})',
        r'monday (\d{1,2})',
        r'tuesday (\d{1,2})',
        r'wednesday (\d{1,2})',
        r'thursday (\d{1,2})',
        r'june (\d{1,2})',
        r'july (\d{1,2})',
    ]
    if not target_date:
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    now = datetime.now()
                    if '/' in pattern and len(match.groups()) == 3:
                        day, month, year = match.groups()
                        target_date = datetime(int(year), int(month), int(day)).date()
                    elif '/' in pattern and len(match.groups()) == 2:
                        day, month = match.groups()
                        target_date = datetime(now.year, int(month), int(day)).date()
                    elif 'june' in pattern:
                        day = match.group(1)
                        target_date = datetime(now.year, 6, int(day)).date()
                    elif 'july' in pattern:
                        day = match.group(1)
                        target_date = datetime(now.year, 7, int(day)).date()
                    else:
                        # Day of week and number
                        day = int(match.group(1))
                        month = now.month
                        target_date = datetime(now.year, month, day).date()
                except Exception:
                    continue
                break

    # Time patterns (e.g., "2pm", "14:30")
    time_patterns = [
        r'\b(\d{1,2})\s*pm\b',      # 2pm, 2 pm
        r'\b(\d{1,2})\s*am\b',      # 10am, 10 am
        r'(\d{1,2}):(\d{2})',       # 14:30
        r'at (\d{1,2})',            # at 2
        r'(\d{1,2}) o\'clock',      # 2 o'clock
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                if 'pm' in pattern:
                    hour = int(match.group(1))
                    if hour != 12:
                        hour += 12
                    target_time = f"{hour:02d}:00"
                elif 'am' in pattern:
                    hour = int(match.group(1))
                    if hour == 12:
                        hour = 0
                    target_time = f"{hour:02d}:00"
                elif ':' in pattern:
                    target_time = f"{int(match.group(1)):02d}:{match.group(2)}"
                else:
                    hour = int(match.group(1))
                    # Assume PM for typical working hours
                    if 8 <= hour <= 12:
                        target_time = f"{hour:02d}:00"
                    elif 1 <= hour <= 8:
                        target_time = f"{hour + 12:02d}:00"
                break
            except Exception:
                continue

    return target_date, target_time

def extract_client_name(text):
    """
    Extract the client's name from the text using common patterns.
    Returns the name as a string or None.
    """
    patterns = [
        r'for ([A-Za-záéíóúñÁÉÍÓÚÑ]+ [A-Za-záéíóúñÁÉÍÓÚÑ]+)',     # for John Smith
        r'client ([A-Za-záéíóúñÁÉÍÓÚÑ]+ [A-Za-záéíóúñÁÉÍÓÚÑ]+)',  # client John Smith
        r'name is ([A-Za-záéíóúñÁÉÍÓÚÑ]+ [A-Za-záéíóúñÁÉÍÓÚÑ]+)', # name is John Smith
        r'I am ([A-Za-záéíóúñÁÉÍÓÚÑ]+ [A-Za-záéíóúñÁÉÍÓÚÑ]+)',    # I am John Smith
        r'my name is ([A-Za-záéíóúñÁÉÍÓÚÑ]+ [A-Za-záéíóúñÁÉÍÓÚÑ]+)', # my name is John Smith
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).title()  # Normalize capitalization

    # If user writes only two words, treat as name
    words = text.strip().split()
    if len(words) == 2 and all(word.isalpha() for word in words):
        return text.title()

    return None

def find_employee_in_text(text):
    """
    Find an employee mentioned in the text by name (accent/case-insensitive).
    Returns an Employee object or None.
    """
    text_norm = normalize(text)
    for emp in get_employees():
        emp_norm = normalize(emp.name)
        if emp_norm in text_norm or text_norm in emp_norm:
            return emp
    return None

def check_availability(employee, date, time):
    """
    Check if the employee is available at the given date and time.
    Returns True if available, False otherwise.
    """
    try:
        date_obj = date if isinstance(date, datetime) else datetime.strptime(str(date), "%Y-%m-%d").date()
        time_obj = datetime.strptime(time, "%H:%M").time()
        start_time = datetime.combine(date_obj, time_obj)
        end_time = start_time + timedelta(hours=1)
        return is_employee_available(employee.id, start_time, end_time)
    except Exception:
        return False

def create_appointment(client_name, employee, date, time):
    """
    Create an appointment for the client with the employee at the given date and time.
    Returns (success: bool, message: str).
    """
    try:
        # Ensure client exists
        client = Client(name=client_name)
        add_client(client)
        date_obj = date if isinstance(date, datetime) else datetime.strptime(str(date), "%Y-%m-%d").date()
        time_obj = datetime.strptime(time, "%H:%M").time()
        start_time = datetime.combine(date_obj, time_obj)
        end_time = start_time + timedelta(hours=1)
        # Use full validation
        success, msg = schedule_appointment_with_validation(
            client_name, employee.name, start_time, end_time
        )
        return success, msg
    except Exception as e:
        return False, f"Error creating appointment: {str(e)}"

def get_employees_info():
    """
    Return a list of employee names and roles for display.
    """
    employees = get_employees()
    return [f"{emp.name} ({emp.role})" for emp in employees]

def process_conversation(user_message):
    """
    Main conversational logic for the AI assistant.
    Updates conversation_state and returns the next response.
    """
    global conversation_state

    # Reset if user greets or asks to restart
    if any(x in user_message.lower() for x in ["start", "restart", "reset", "nuevo", "empezar de nuevo"]):
        reset_state()
        return welcome_message()
    
    # Step 1: Try to extract data from the message
    emp = find_employee_in_text(user_message)
    if emp:
        conversation_state["employee"] = emp
    date, time = parse_date_time(user_message)
    if date:
        conversation_state["date"] = date
    if time:
        conversation_state["time"] = time

    # Only accept client name if not equal to selected employee (ignoring accents/case)
    name = extract_client_name(user_message)
    if name:
        if conversation_state.get("employee") and normalize(name) == normalize(conversation_state["employee"].name):
            pass  # Don't use as client name
        else:
            conversation_state["client_name"] = name

    # Step 2: Ask only for missing info
    if not conversation_state["employee"]:
        conversation_state["last_step"] = "employee"
        emp_list = ", ".join(get_employees_info())
        return f"Which employee would you like to book with? Available employees are: {emp_list}"
    if not conversation_state["date"]:
        conversation_state["last_step"] = "date"
        return (
            f"What date would you prefer for the appointment with "
            f"{conversation_state['employee'].name}? (e.g., 'tomorrow', 'June 15', '15/06')"
        )
    if not conversation_state["time"]:
        conversation_state["last_step"] = "time"
        date_str = conversation_state['date'].strftime('%d/%m/%Y')
        return (
            f"What time would you like on {date_str} with "
            f"{conversation_state['employee'].name}? (e.g., '14:00', '2pm')"
        )
    if not conversation_state["client_name"]:
        conversation_state["last_step"] = "client_name"
        return "What's the client's name for the appointment?"

    # Step 3: Check availability and schedule
    available = check_availability(
        conversation_state['employee'],
        conversation_state['date'],
        conversation_state['time'],
    )
    if not available:
        date_str = conversation_state['date'].strftime('%d/%m/%Y')
        # Only clear the time, not the date, so user can pick another time
        conversation_state["time"] = None
        return (
            f"❌ {conversation_state['employee'].name} is not available on "
            f"{date_str} at {conversation_state['time']}. Please select another time."
        )

    success, msg = create_appointment(
        conversation_state["client_name"],
        conversation_state["employee"],
        conversation_state["date"],
        conversation_state["time"],
    )
    if not success:
        # If error is only about time, don't clear date
        if "does not work on" in msg or "only works on" in msg:
            conversation_state["time"] = None
        elif "already has another appointment" in msg:
            conversation_state["time"] = None
        else:
            # If error is about date, clear both date and time
            conversation_state["date"] = None
            conversation_state["time"] = None
        return f"❌ {msg}"

    # Reset all if successfully scheduled
    reset_state()
    return f"✅ {msg} The appointment has been confirmed!"

def welcome_message():
    """
    Return a welcome message with available employees.
    """
    emp_list = ", ".join(get_employees_info())
    return (
        "Hello! I'm your scheduling assistant. "
        "I can help you book appointments. "
        f"Our employees are: {emp_list}. "
        "Who would you like to schedule an appointment with?"
    )

def chat_completion(history):
    """
    Main entry point for chat UI. Returns the assistant's response.
    """
    if not history or not history[-1][1].strip():
        reset_state()
        return welcome_message()
    user_message = history[-1][1]
    # If user greets, respond with welcome + employees
    if any(word in user_message.lower() for word in ["hello", "hi", "hey", "hola"]):
        reset_state()
        return welcome_message()
    return process_conversation(user_message)