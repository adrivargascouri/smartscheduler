from dataclasses import dataclass, field

@dataclass
class Person:
    name: str
    email: str
    phone: str
    id: int = field(default=None, init=False)  

    
@dataclass
class Client(Person):
  pass

@dataclass
class Employee(Person):
    role: str
    availability: list

    def is_available(self,time_slot):
        return time_slot in self.availability
    
