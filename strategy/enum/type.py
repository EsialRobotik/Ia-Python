from enum import Enum

class Type(Enum):
    DEPLACEMENT = "deplacement"
    MANIPULATION = "manipulation"
    ELEMENT = "element"

    def __str__(self):
        return self.value