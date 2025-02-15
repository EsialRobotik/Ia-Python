from ia.pathfinding.shape.Shape import Shape
from ia.pathfinding.shape.ShapeFiller import ShapeFiller
from ia.utils.Position import Position


class Polygon(Shape):
    """
    A class representing a polygon, inheriting from Shape.

    Attributes:
        vertex_list (list[Position]): The list of vertices of the polygon.
    """

    def __init__(self, json_object: dict) -> None:
        """
        Initializes a Polygon object from a JSON object.

        Args:
            json_object (dict): A dictionary containing the polygon's properties.
        """
        self.vertex_list = [Position(vertex["x"], vertex["y"]) for vertex in json_object["points"]]
        if json_object:
            super().__init__(id=json_object.get("id", ""), active=json_object.get("active", False))
        else:
            super().__init__(id="", active=False)

    def get_vertex_list(self) -> list[Position]:
        """
        Gets the list of vertices of the polygon.

        Returns:
            list[Position]: The list of vertices of the polygon.
        """
        return self.vertex_list

    def draw_shape_edges(self, length: int, width: int, fill: bool = True) -> list[list[bool]]:
        """
        Draws the edges of the polygon on a board.

        Args:
            length (int): The length of the board.
            width (int): The width of the board.
            fill (bool): Whether to fill the shape or not.

        Returns:
            list[list[bool]]: A 2D list representing the board with the polygon edges drawn.
        """
        board = self.get_empty_board(length * 3, width * 3)

        # Draw the shape edges segment by segment
        for i in range(len(self.vertex_list) - 1):
            self.draw_segment(board, self.vertex_list[i], self.vertex_list[i + 1], length, width)

        # Draw the last segment
        self.draw_segment(board, self.vertex_list[0], self.vertex_list[-1], length, width)

        if fill:
            shape_filler = ShapeFiller(board)
            shape_filler.fill_board()

        return board

    def draw_segment(self, board: list[list[bool]], a: Position, b: Position, length: int, width: int) -> None:
        """
        Draws a segment between two points on the board.

        Args:
            board (list[list[bool]]): The board to draw on.
            a (Position): The starting point of the segment.
            b (Position): The ending point of the segment.
            length (int): The length of the board.
            width (int): The width of the board.
        """
        board[a.x // 10 + length][a.y // 10 + width] = True
        board[b.x // 10 + length][b.y // 10 + width] = True

        # Divide the segment into 1000 points
        delta_x = (b.x - a.x) / 10000
        delta_y = (b.y - a.y) / 10000

        x = a.x / 10 + length
        y = a.y / 10 + width

        for _ in range(1000):
            board[int(x)][int(y)] = True
            x += delta_x
            y += delta_y