from enum import Enum

class SubType(Enum):
    GO = "go"
    GOTO = "goto"
    GOTO_CHAIN = "goto_chain"
    FACE = "face"
    GOTO_BACK = "goto_back"
    GOTO_ASTAR = "goto_astar"
    SET_SPEED = "set_speed"
    SUPPRESSION = "suppression"
    AJOUT = "ajout"
    WAIT_CHRONO = "wait_chrono"
    WAIT = "wait"
    NONE = "none"

    def __str__(self):
        return self.value