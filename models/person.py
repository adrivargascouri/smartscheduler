from dataclasses import dataclass

@dataclass
class Person:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def __str__(self):
        return f"{self.name} ({self.email})"

class Client(Person):
    def __init__(self, name, email="", phone=""):
        super().__init__(name, email, phone)

class Employee(Person):
    def __init__(self, name, email, phone, role, availability):
        super().__init__(name, email, phone)
        self.role = role
        self.availability = availability  # List of available days (e.g., ["Monday", "Tuesday"])

    def __str__(self):
        return f"{self.name} - {self.role} ({self.email})"
