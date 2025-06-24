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
    Check if the proposed appointment is WITHIN any of the employee's available intervals.
    Returns True if available, False otherwise.
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
    Try to schedule an appointment for the given client and employee, validating:
    - That the employee exists
    - That the client exists
    - That the appointment is within the employee's working hours
    - That there are no overlaps
    Returns (success: bool, message: str)
    """
    # 1. Verify the existence of the client and employee
    client = get_client_by_name(client_name)
    if not client:
        return False, f"No client found with name '{client_name}'."

    employee = get_employee_by_name(employee_name)
    if not employee:
        return False, f"No employee found with name '{employee_name}'."

    # 2. Check if the appointment is within the employee's availability
    if not is_time_in_employee_availability(employee, start_time, end_time):
        day_of_week = start_time.strftime("%A")
        intervals = employee.availability.get(day_of_week, [])
        if intervals:
            pretty_intervals = ", ".join(intervals)
            return (
                False,
                f"{employee.name} only works on {day_of_week}s at: {pretty_intervals}. "
                "Please select a time within those ranges."
            )
        else:
            return (
                False,
                f"{employee.name} does not work on {day_of_week}s. Please select another day."
            )

    # 3. Check for overlapping appointments
    if not is_employee_available(employee.id, start_time, end_time):
        return False, f"{employee.name} already has another appointment at that time."

    # 4. If all checks pass, schedule the appointment
    appointment = Appointment(
        client=client,
        employee=employee,
        start_time=start_time,
        end_time=end_time,
        status="Scheduled"
    )
    add_appointment(appointment)
    return (
        True,
        f"Appointment scheduled for {client_name} with {employee_name} on "
        f"{start_time.strftime('%A %d/%m/%Y at %H:%M')}."
    )