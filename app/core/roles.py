from enum import Enum

class RoleName(str, Enum):
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    CUSTOMER = "CUSTOMER"
    