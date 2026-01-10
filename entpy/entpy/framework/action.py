from enum import Enum


class Action(Enum):
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    HARD_DELETE = "HARD_DELETE"
    SOFT_DELETE = "SOFT_DELETE"
