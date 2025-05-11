from enum import Enum

class AsservStatus(Enum):
    STATUS_IDLE = 0
    STATUS_RUNNING = 1
    STATUS_HALTED = 2
    STATUS_BLOCKED = 3