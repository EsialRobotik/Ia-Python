class Position:
    """
    A class to represent a position in a 2D space with an optional orientation.
    Attributes:
    ----------
    x : float
        The x-coordinate of the position.
    y : float
        The y-coordinate of the position.
    theta : float, optional
        The orientation angle in radians (default is 0).
    Methods:
    -------
    __str__():
        Returns a string representation of the position.
    """

    def __init__(self, x: int, y: int, theta: float = 0) -> None:
        """
        Initialize a new Position instance.
        Args:
            x (float): The x-coordinate of the position.
            y (float): The y-coordinate of the position.
            theta (float, optional): The orientation angle in radians. Defaults to 0.
        """

        self.x = x
        self.y = y
        self.theta = theta

    def __str__(self) -> str:
        """
        Returns a string representation of the Position object.
        The string representation includes the x, y coordinates and the theta angle.
        Returns:
            str: A string in the format "Position(x=<x>, y=<y>, theta=<theta>)".
        """

        return f"Position(x={self.x}, y={self.y}, theta={self.theta})"