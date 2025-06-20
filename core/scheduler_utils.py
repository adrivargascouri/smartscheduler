from datetime import datetime
from smartscheduler.data.database import (
    get_employee_by_name,
    get_client_by_name,
    is_employee_available,
    add_appointment,
)
from smartscheduler.models.appointment import Appointment

def is_time_in_employee_availability(employee, start_time, end_time):
    """
    Verifica si la cita propuesta está DENTRO de algún intervalo de disponibilidad del empleado.
    """
    availability = employee.availability or {}
    day_of_week = start_time.strftime("%A")
    intervals = availability.get(day_of_week, [])
    for interval in intervals:
        start_str, end_str = interval.split("-")
        avail_start = datetime.strptime(start_str, "%H:%M").time()
        avail_end = datetime.strptime(end_str, "%H:%M").time()
        if avail_start <= start_time.time() and end_time.time() <= avail_end:
            return True
    return False

def schedule_appointment_with_validation(client_name, employee_name, start_time, end_time):
    """
    Intenta agendar una cita para el cliente y empleado dados, validando:
    - Que el empleado existe
    - Que el cliente existe
    - Que la cita está dentro del horario laboral del empleado
    - Que no hay solapamientos
    """
    # 1. Verify the existent of an employee or client 
    client = get_client_by_name(client_name)
    if not client:
        return False, f"No client found with name '{client_name}'."

    employee = get_employee_by_name(employee_name)
    if not employee:
        return False, f"No employee found with name '{employee_name}'."

    # 2. Check availability (date and time)
    if not is_time_in_employee_availability(employee, start_time, end_time):
        day_of_week = start_time.strftime("%A")
        intervals = employee.availability.get(day_of_week, [])
        if intervals:
            pretty_intervals = ", ".join(intervals)
            return (False, f"{employee.name} only works on {day_of_week}s at: {pretty_intervals}. Please select a time within those ranges.")
        else:
            return (False, f"{employee.name} does not work on {day_of_week}s. Please select another day.")

    # 3. Check overlaps
    if not is_employee_available(employee.id, start_time, end_time):
        return False, f"{employee.name} already has another appointment at that time."

    # 4. If everything good, schedule appointment
    appointment = Appointment(
        client=client,
        employee=employee,
        start_time=start_time,
        end_time=end_time,
        status="Scheduled"
    )
    add_appointment(appointment)
    return True, f"Appointment scheduled for {client_name} with {employee_name} on {start_time.strftime('%A %d/%m/%Y at %H:%M')}."