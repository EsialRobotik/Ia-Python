from enum import Enum


class StepType(Enum):
    """
    Enum representing different types of steps in a process.

    Attributes
    ----------
    MOVEMENT : str
        Represents a movement step.
    MANIPULATION : str
        Represents a manipulation step.
    ELEMENT : str
        Represents an element step.
    """
    MOVEMENT = 'MOVEMENT'
    MANIPULATION = 'MANIPULATION'
    ELEMENT = 'ELEMENT'