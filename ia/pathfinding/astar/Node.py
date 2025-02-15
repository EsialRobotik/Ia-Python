from typing import Optional

from ia.utils.Direction import Direction


class Node:
    """
    Class representing a node in a pathfinding algorithm.
    """

    def __init__(self, x: int, y: int) -> None:
        """
        Constructor for the Node class.

        Args:
            x (int): x position of the node.
            y (int): y position of the node.
        """
        self.x = x
        self.y = y
        self.cost = 0
        self.cost_heuristic = 0
        self.heuristic = 0
        self.parent: Optional[Node] = None
        self.parent_direction: Optional[Direction] = None
        self.closed = False
        self.accessible = True
        self.neighbor_n: Optional[Node] = None
        self.neighbor_s: Optional[Node] = None
        self.neighbor_e: Optional[Node] = None
        self.neighbor_w: Optional[Node] = None
        self.neighbor_ne: Optional[Node] = None
        self.neighbor_nw: Optional[Node] = None
        self.neighbor_se: Optional[Node] = None
        self.neighbor_sw: Optional[Node] = None

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: 'Node') -> bool:
        return self.cost_heuristic < other.cost_heuristic

    def __le__(self, other: 'Node') -> bool:
        return self.cost_heuristic <= other.cost_heuristic

    def __gt__(self, other: 'Node') -> bool:
        return self.cost_heuristic > other.cost_heuristic

    def __ge__(self, other: 'Node') -> bool:
        return self.cost_heuristic >= other.cost_heuristic