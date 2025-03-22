from enum import Enum


class StepType(Enum):
    """
    Enum representing different types of steps in a process.

    Attributes
    ----------
    MOVEMENT : str
        Represents a movement strategy.
    MANIPULATION : str
        Represents a manipulation strategy.
    ELEMENT : str
        Represents an element strategy.
    """
    MOVEMENT = 'MOVEMENT'
    MANIPULATION = 'MANIPULATION'
    ELEMENT = 'ELEMENT'