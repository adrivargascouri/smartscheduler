from dataclasses import dataclass

@dataclass
class Person:
    id: int
    name: str
    email: str
    phone: str

    def __str__(self):
        return f"{self.name}({self.email})"
    
@dataclass
class Client(Person):
    pass

@dataclass
class Employee(Person):
    role: str
    availability: list

    def is_available(self,time_slot):
        return time_slot in self.availability
    

#Person es una clase generica para personas,con
#datos comunes.
#Client hereda de Person sin agregar nada extra 
#Employee tambien hereda,pero agrega campos como role
#y availability
#Usamos @dataclass para evitar escribir constructores
#(__init__) manualmente