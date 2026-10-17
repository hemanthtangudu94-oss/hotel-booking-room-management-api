from enum import Enum

class RoleName(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    USER = "USER"
    # Backward-compatible role names for existing databases.
    RECEPTIONIST = "RECEPTIONIST"
    CUSTOMER = "CUSTOMER"
