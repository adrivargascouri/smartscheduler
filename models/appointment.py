from dataclasses import dataclass, field
from models.person import Client, Employee
from datetime import datetime

@dataclass
class Appointment:
    client: Client
    employee: Employee
    start_time: datetime
    end_time: datetime
    status: str = "pending"
    id: int = field(default=None, init=False) 