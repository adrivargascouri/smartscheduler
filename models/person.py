from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Person:
    name: str
    email: str
    phone: str

    def __str__(self):
        return f"{self.name} ({self.email})"
    
@dataclass
class Client(Person):
    email: str = ""
    phone: str = ""

@dataclass
class Employee(Person):
    role : str
    availability: Dict[str, List[str]] = field(default_factory=dict)
    id: int = field(default=None, init=False)

    def __str__(self):
        return f"{self.name} - {self.role} ({self.email})"
