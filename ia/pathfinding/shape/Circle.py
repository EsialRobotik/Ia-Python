import math

from ia.pathfinding.shape.Shape import Shape
from ia.pathfinding.shape.ShapeFiller import ShapeFiller
from ia.utils.Position import Position


class Circle(Shape):
    """
    A class representing a circle, inheriting from Shape.

    Attributes:
        center (Position): The center point of the circle.
        radius (int): The radius of the circle.
        epsilon (float): A small value used for floating-point comparison.
    """

    epsilon = 0.00001

    def __init__(self, x: int =None, y: int =None, radius: int =None, json_object: dict =None) -> None:
        """
        Initializes a Circle object from a JSON object.

        Args:
            json_object (dict): A dictionary containing the circle's properties.
        """
        if json_object:
            self.center = Position(json_object["centre"]["x"], json_object["centre"]["y"])
            self.radius = json_object["rayon"]
        else:
            self.center = Position(x, y)
            self.radius = radius
        if json_object:
            super().__init__(id=json_object.get("id", ""), active=json_object.get("active", False))
        else:
            super().__init__(id="", active=False)

    def get_radius(self) -> int:
        """
        Gets the radius of the circle.

        Returns:
            int: The radius of the circle.
        """
        return self.radius

    def get_center(self) -> Position:
        """
        Gets the center point of the circle.

        Returns:
            Position: The center point of the circle.
        """
        return self.center

    def draw_shape_edges(self, length: int, width: int, fill: bool = True) -> list[list[bool]]:
        """
        Draws the edges of the circle on a board.

        Args:
            length (int): The length of the board.
            width (int): The width of the board.
            fill (bool): Whether to fill the shape or not.

        Returns:
            list[list[bool]]: A 2D list representing the board with the circle edges drawn.
        """
        board = self.get_empty_board(length * 3, width * 3)

        # We divide the circle into 1000 parts and compute points each time.
        # We work with the original millimetric table and will convert to cm when drawing.
        rad_split = math.pi / 1000
        current_value = 0
        shifted_x_center = self.center.x + length * 10
        shifted_y_center = self.center.y + width * 10
        while current_value < (math.pi * 2):
            x_float = (shifted_x_center + self.radius * math.cos(current_value)) / 10
            y_float = (shifted_y_center + self.radius * math.sin(current_value)) / 10

            x = int(x_float)
            y = int(y_float)
            if (x_float - x) > self.epsilon and (y_float - y) > self.epsilon:
                board[x][y] = True
            current_value += rad_split

        if fill:
            shape_filler = ShapeFiller(board)
            shape_filler.fill_board()

        return board