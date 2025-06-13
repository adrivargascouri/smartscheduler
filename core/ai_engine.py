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
    add_appointment,
    STATUS_SCHEDULED,
)
def normalize(text):
    """Quita acentos y convierte a minúsculas para comparar nombres correctamente."""
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# Memoria conversacional simple (para un usuario)
conversation_state = {
    "employee": None,
    "date": None,
    "time": None,
    "client_name": None,
    "last_step": None,  # Para saber qué le falta pedir al usuario
}

def reset_state():
    global conversation_state
    conversation_state = {
        "employee": None,
        "date": None,
        "time": None,
        "client_name": None,
        "last_step": None,
    }

def parse_date_time(text):
    """Extract date and time from text"""
    text_lower = text.lower()
    target_date = None
    target_time = None

    # Palabras clave para fechas relativas
    patterns = {
        'day after tomorrow': datetime.now() + timedelta(days=2),
        'tomorrow': datetime.now() + timedelta(days=1),
        'today': datetime.now(),
        'next week': datetime.now() + timedelta(days=7),
        # Agrega más reglas si lo deseas
    }
    for word, date_obj in patterns.items():
        if word in text_lower:
            target_date = date_obj.date()
            break

    # Fechas explícitas tipo "friday 20", "15/06", "junio 15"
    date_patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',   # 15/06/2025
        r'(\d{1,2})/(\d{1,2})',           # 15/06
        r'friday (\d{1,2})',              # friday 20
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
                        # Día de la semana y número
                        day = int(match.group(1))
                        month = now.month
                        target_date = datetime(now.year, month, day).date()
                except Exception:
                    continue
                break

    # Busca hora en formatos comunes
    time_patterns = [
        r'(\d{1,2}):(\d{2})',     # 14:30
        r'(\d{1,2}) ?pm',         # 2pm
        r'(\d{1,2}) ?am',         # 10am
        r'at (\d{1,2})',          # at 2
        r'(\d{1,2}) o\'clock',    # 2 o'clock
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
                    # Asume PM para horas laborales típicas
                    if 8 <= hour <= 12:
                        target_time = f"{hour:02d}:00"
                    elif 1 <= hour <= 8:
                        target_time = f"{hour + 12:02d}:00"
                break
            except Exception:
                continue

    return target_date, target_time

def extract_client_name(text):
    """Extrae el nombre del cliente del texto"""
    # Busca patrones comunes
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
            return match.group(1).title()  # Normaliza mayúsculas

    # Si el usuario solo escribe dos palabras, tómalo como nombre
    words = text.strip().split()
    if len(words) == 2 and all(word.isalpha() for word in words):
        return text.title()

    return None

def find_employee_in_text(text):
    text_norm = normalize(text)
    for emp in get_employees():
        emp_norm = normalize(emp.name)
        if emp_norm in text_norm or text_norm in emp_norm:
            return emp
    return None

def check_availability(employee, date, time):
    try:
        date_obj = date if isinstance(date, datetime) else datetime.strptime(str(date), "%Y-%m-%d").date()
        time_obj = datetime.strptime(time, "%H:%M").time()
        start_time = datetime.combine(date_obj, time_obj)
        end_time = start_time + timedelta(hours=1)
        return is_employee_available(employee.id, start_time, end_time)
    except Exception:
        return False

def create_appointment(client_name, employee, date, time):
    try:
        client = Client(name=client_name)
        add_client(client)
        date_obj = date if isinstance(date, datetime) else datetime.strptime(str(date), "%Y-%m-%d").date()
        time_obj = datetime.strptime(time, "%H:%M").time()
        start_time = datetime.combine(date_obj, time_obj)
        end_time = start_time + timedelta(hours=1)
        appointment = Appointment(client, employee, start_time, end_time, STATUS_SCHEDULED)
        add_appointment(appointment)
        return True, f"Appointment scheduled for {client_name} with {employee.name} on {start_time.strftime('%d/%m/%Y at %H:%M')}"
    except Exception as e:
        return False, f"Error creating appointment: {str(e)}"

def get_employees_info():
    employees = get_employees()
    return [f"{emp.name} ({emp.role})" for emp in employees]

def process_conversation(user_message):
    global conversation_state

    # Reset si usuario saluda o pide reiniciar
    if any(x in user_message.lower() for x in ["start", "restart", "reset", "nuevo", "empezar de nuevo"]):
        reset_state()
        return welcome_message()
    
    # Paso 1: Intentar extraer datos del mensaje
    emp = find_employee_in_text(user_message)
    if emp:
        conversation_state["employee"] = emp
    date, time = parse_date_time(user_message)
    if date:
        conversation_state["date"] = date
    if time:
        conversation_state["time"] = time

    # --- BLOQUE CLAVE: Solo acepta el nombre de cliente si no es igual al del empleado seleccionado ---
    name = extract_client_name(user_message)
    if name:
        # No permitas que el nombre del empleado se use como cliente (ignorando acentos y mayúsculas)
        if conversation_state.get("employee") and normalize(name) == normalize(conversation_state["employee"].name):
            pass  # No lo uses como cliente
        else:
            conversation_state["client_name"] = name

    # Paso 2: Preguntar solo lo que falta
    if not conversation_state["employee"]:
        conversation_state["last_step"] = "employee"
        emp_list = ", ".join(get_employees_info())
        return f"Which employee would you like to book with? Available employees are: {emp_list}"
    if not conversation_state["date"]:
        conversation_state["last_step"] = "date"
        return f"What date would you prefer for the appointment with {conversation_state['employee'].name}? (e.g., 'tomorrow', 'June 15', '15/06')"
    if not conversation_state["time"]:
        conversation_state["last_step"] = "time"
        date_str = conversation_state['date'].strftime('%d/%m/%Y')
        return f"What time would you like on {date_str} with {conversation_state['employee'].name}? (e.g., '14:00', '2pm')"
    if not conversation_state["client_name"]:
        conversation_state["last_step"] = "client_name"
        return "What's the client's name for the appointment?"

    # Paso 3: Verificar disponibilidad y agendar
    available = check_availability(
        conversation_state['employee'],
        conversation_state['date'],
        conversation_state['time'],
    )
    if not available:
        date_str = conversation_state['date'].strftime('%d/%m/%Y')
        return f"Sorry, {conversation_state['employee'].name} is not available on {date_str} at {conversation_state['time']}. Would you like to try another time?"

    success, msg = create_appointment(
        conversation_state["client_name"],
        conversation_state["employee"],
        conversation_state["date"],
        conversation_state["time"],
    )
    reset_state()
    if success:
        return f"✅ {msg} The appointment has been confirmed!"
    else:
        return f"❌ {msg}"
def welcome_message():
    emp_list = ", ".join(get_employees_info())
    return (
        "Hello! I'm your scheduling assistant. "
        "I can help you book appointments. "
        f"Our employees are: {emp_list}. "
        "Who would you like to schedule an appointment with?"
    )

def chat_completion(history):
    if not history or not history[-1][1].strip():
        reset_state()
        return welcome_message()
    user_message = history[-1][1]
    # Si el usuario solo saluda, responde con bienvenida + empleados
    if any(word in user_message.lower() for word in ["hello", "hi", "hey", "hola"]):
        reset_state()
        return welcome_message()
    return process_conversation(user_message)