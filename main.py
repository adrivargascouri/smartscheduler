import data.database as db
from models.person import Client, Employee
from models.appointment import Appointment
from datetime import datetime, timedelta

db.reset_database()

db.create_tables()

cliente = Client(name="Carlos Perez", email="carlos@correo.com", phone="1233449")
db.add_client(cliente)

empleado = Employee(name="Maria Lopez", email="maria@empresa.com", phone="12367890", role="Doctor", availability=["10:00", "11:00", "12:00"])
db.add_employee(empleado)

start = datetime(2025, 4, 24, 10, 0)
end = start + timedelta(hours=1)
cita = Appointment(client=cliente, employee=empleado, start_time=start, end_time=end)
db.add_appointment(cita)

print("\nClients:")
for c in db.get_clients():
    print(f"ID: {c[0]}, Name: {c[1]}, Email: {c[2]}, Phone: {c[3]}")

print("\nEmployees:")
for e in db.get_employees():
    print(f"ID: {e[0]}, Name: {e[1]}, Email: {e[2]}, Phone: {e[3]}, Role: {e[4]}, Availability: {e[5]}")

print("\nAppointments:")
for a in db.get_appointments():
    print(f"ID: {a[0]}, Client ID: {a[1]}, Employee ID: {a[2]}, Start: {a[3]}, End: {a[4]}, Status: {a[5]}")
