from enum import Enum


class StepSubType(Enum):
    """
    Enum representing different subtypes of steps in a process.

    Attributes
    ----------
    NONE : str
        Represents no specific subtype.
    GO : str
        Represents a go step.
    FACE : str
        Represents a face step.
    GOTO : str
        Represents a goto step.
    GOTO_BACK : str
        Represents a goto back step.
    GOTO_CHAIN : str
        Represents a goto chain step.
    GOTO_ASTAR : str
        Represents a goto astar step.
    SET_SPEED : str
        Represents a set speed step.
    DELETE_ZONE : str
        Represents a forbidden zone suppression step.
    ADD_ZONE : str
        Represents an forbidden zone addition step.
    WAIT_CHRONO : str
        Represents a wait chrono step.
    WAIT : str
        Represents a wait step.
    """
    NONE = 'NONE'
    GO = 'GO'
    FACE = 'FACE'
    GOTO = 'GOTO'
    GOTO_BACK = 'GOTO_BACK'
    GOTO_CHAIN = 'GOTO_CHAIN'
    GOTO_ASTAR = 'GOTO_ASTAR'
    SET_SPEED = 'SET_SPEED'
    DELETE_ZONE = 'DELETE_ZONE'
    ADD_ZONE = 'ADD_ZONE'
    WAIT_CHRONO = 'WAIT_CHRONO'
    WAIT = 'WAIT'