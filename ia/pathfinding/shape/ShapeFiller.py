class ShapeFiller:
    """
    A class used to fill the interior of a shape on a board.

    Attributes:
        board (list[list[bool]]): The board where the shape is drawn.
    """

    def __init__(self, board: list[list[bool]]) -> None:
        """
        Initializes the ShapeFiller with the given board.

        Args:
            board (list[list[bool]]): The board where the shape is drawn.
        """
        self.board = board

    def fill_board(self) -> None:
        """
        Fills the interior of the shape on the board.
        """
        buffer = [[False] * len(self.board[0]) for _ in range(len(self.board))]

        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j]:
                    continue
                if self.is_inside_y_axis_projection(i, j) and self.is_inside_x_axis_projection(i, j):
                    buffer[i][j] = True

        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if buffer[i][j]:
                    self.board[i][j] = True

    def is_inside_x_axis_projection(self, x: int, y: int) -> bool:
        """
        Checks if a point is inside the shape based on the x-axis projection.

        Args:
            x (int): The x-coordinate of the point.
            y (int): The y-coordinate of the point.

        Returns:
            bool: True if the point is inside the shape, False otherwise.
        """
        before = 0
        after = 0
        in_border = False

        for i in range(len(self.board)):
            temp = self.board[i][y]
            if temp:
                if not in_border:
                    if i < x:
                        before += 1
                    else:
                        after += 1
                in_border = True
            else:
                in_border = False

        return (after % 2) != 0 and (before % 2) != 0

    def is_inside_y_axis_projection(self, x: int, y: int) -> bool:
        """
        Checks if a point is inside the shape based on the y-axis projection.

        Args:
            x (int): The x-coordinate of the point.
            y (int): The y-coordinate of the point.

        Returns:
            bool: True if the point is inside the shape, False otherwise.
        """
        before = 0
        after = 0
        in_border = False

        for i in range(len(self.board[0])):
            temp = self.board[x][i]
            if temp:
                if not in_border:
                    if i < y:
                        before += 1
                    else:
                        after += 1
                in_border = True
            else:
                in_border = False

        return (after % 2) != 0 and (before % 2) != 0