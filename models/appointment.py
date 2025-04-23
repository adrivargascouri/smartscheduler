from dataclasses import dataclass
from datetime import datetime
from models.person import Client,Employee

@dataclass
class Appointment:
    id: int
    client: Client
    employee: Employee
    start_time: datetime
    end_time: datetime
    status: str

    def duration(self):
        return (self.end_time - self.start_time).total_seconds() / 60
    
    def __str__(self):
        return f"Appointment {self.id}: {self.client.name} with {self.employee.name} from {self.start_time} to {self.end_time} ({self.status})"
    