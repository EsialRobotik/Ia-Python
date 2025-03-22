from enum import Enum

class AsservStatus(Enum):
    STATUS_IDLE = 1
    STATUS_RUNNING = 2
    STATUS_HALTED = 3
    STATUS_BLOCKED = 4