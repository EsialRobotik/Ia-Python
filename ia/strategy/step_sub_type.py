from enum import Enum


class StepSubType(Enum):
    """
    Enum representing different subtypes of steps in a process.

    Attributes
    ----------
    NONE : str
        Represents no specific subtype.
    GO : str
        Represents a go strategy.
    FACE : str
        Represents a face strategy.
    GOTO : str
        Represents a goto strategy.
    GOTO_BACK : str
        Represents a goto back strategy.
    GOTO_CHAIN : str
        Represents a goto chain strategy.
    GOTO_ASTAR : str
        Represents a goto astar strategy.
    SET_SPEED : str
        Represents a set speed strategy.
    DELETE_ZONE : str
        Represents a forbidden zone suppression strategy.
    ADD_ZONE : str
        Represents an forbidden zone addition strategy.
    WAIT_CHRONO : str
        Represents a wait chrono strategy.
    WAIT : str
        Represents a wait strategy.
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