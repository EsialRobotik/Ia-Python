from abc import ABC, abstractmethod

class Shape(ABC):
    """
    Abstract base class representing a shape.

    Attributes:
        id (str): The identifier of the shape.
        active (bool): The active state of the shape.
    """

    def __init__(self, id: str, active: bool) -> None:
        self.id = id
        self.active = active

    @abstractmethod
    def draw_shape_edges(self, length: int, width: int, fill: bool =True) -> list[list[bool]]:
        """
        Draws the edges of the shape on a board.

        Args:
            length (int): The length of the board.
            width (int): The width of the board.
            fill (bool): Whether to fill the shape or not.

        Returns:
            list[list[bool]]: A 2D list representing the board with the shape edges drawn.
        """
        pass

    def get_empty_board(self, length: int, width: int) -> list[list[bool]]:
        """
        Creates an empty board.

        Args:
            length (int): The length of the board.
            width (int): The width of the board.

        Returns:
            list[list[bool]]: A 2D list representing the empty board.
        """
        return [[False for _ in range(width)] for _ in range(length)]

    def get_id(self) -> str:
        """
        Gets the identifier of the shape.

        Returns:
            str: The identifier of the shape.
        """
        return self.id

    def is_active(self) -> bool:
        """
        Checks if the shape is active.

        Returns:
            bool: True if the shape is active, False otherwise.
        """
        return self.active

    def set_active(self, active: bool) -> None:
        """
        Sets the active state of the shape.

        Args:
            active (bool): The new active state of the shape.
        """
        self.active = active