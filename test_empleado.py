from smartscheduler.models.person import Employee
from smartscheduler.data.database import add_employee, get_employee_by_email

# Disponibilidad de ejemplo (puedes cambiar los rangos y días)
availability = {
    "Monday": ["08:00-12:00", "14:00-17:00"],
    "Tuesday": ["09:00-12:00"],
    "Wednesday": [],
    "Thursday": ["08:00-12:00", "15:00-18:00"],
    "Friday": ["08:00-12:00"],
    "Saturday": [],
    "Sunday": []
}

emp = Employee(
    name="Mario Test",
    email="mario@test.com",
    phone="3210001111",
    role="Therapist",
    availability=availability
)

add_employee(emp)

# Para verificar:
emp_db = get_employee_by_email("mario@test.com")
print(emp_db.name)
print(emp_db.availability)