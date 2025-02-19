import heapq
import logging
import time
from typing import List, Optional

from ia.pathfinding import Table
from ia.pathfinding.astar import Node
from ia.utils.Position import Position, Direction


class Astar:
    """
    A class to calculate paths using the A* algorithm.
    """

    # Distance constants
    DIST_DIAGONALE = 18
    DIST_H_V = 10

    def __init__(self, table: Table) -> None:
        """
        Initializes the A* pathfinding algorithm.

        Args:
            table (Table): The table to navigate.
        """
        self.logger = logging.getLogger(__name__)
        self.table = table

        # Grid dimensions
        self.dim_x = self.table.get_rectified_x_size() + 1
        self.dim_y = self.table.get_rectified_y_size() + 1
        self.logger.info(f"Initialize the algorithm with a dimension: {self.dim_x} x {self.dim_y}")

        # Grid initialization
        self.grid = [[] for _ in range(self.dim_x)]
        for x in range(self.dim_x):
            self.grid[x] = [None] * self.dim_y
            for y in range(self.dim_y):
                if (self.table.is_area_forbidden(x, y) or
                    self.table.is_area_forbidden(x - 1, y) or
                    self.table.is_area_forbidden(x - 1, y - 1) or
                    self.table.is_area_forbidden(x, y - 1)):
                    self.grid[x][y] = None
                else:
                    self.grid[x][y] = Node(x, y)

        self.opened = []
        self.update_neighbor_info()

    def get_table(self) -> Table:
        return self.table

    def set_definitively_accessible(self, x: int, y: int, accessible: bool) -> None:
        """
        Sets the accessibility of a grid cell definitively.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            accessible (bool): Whether the cell is accessible.
        """
        if accessible and self.grid[x][y] is None:
            self.grid[x][y] = Node(x, y)
        elif not accessible:
            self.grid[x][y] = None

    def set_temporary_accessible(self, x: int, y: int, accessible: bool) -> None:
        """
        Sets the accessibility of a node temporarily.

        Args:
            x (int): The x coordinate.
            y (int): The y coordinate.
            accessible (bool): Whether the node is accessible.
        """
        node = self.get_node(x, y)
        if node is not None:
            node.accessible = accessible

    def reset_temporary_accessible(self) -> None:
        """
        Resets all temporarily inaccessible zones to accessible.
        """
        for x in range(self.dim_x):
            for y in range(self.dim_y):
                if self.grid[x][y] is not None:
                    self.grid[x][y].accessible = True

    def get_node(self, x: int, y: int) -> Optional[Node]:
        if 0 <= x < self.dim_x and 0 <= y < self.dim_y:
            return self.grid[x][y]
        return None

    def update_neighbor_info(self) -> None:
        """
        Updates the neighborhood information for all nodes.
        """
        for x in range(self.dim_x):
            for y in range(self.dim_y):
                node = self.grid[x][y]
                if node is None:
                    continue

                node.neighbor_n = self.get_node(x - 1, y)
                node.neighbor_s = self.get_node(x + 1, y)
                node.neighbor_e = self.get_node(x, y - 1)
                node.neighbor_w = self.get_node(x, y + 1)
                node.neighbor_ne = self.get_node(x - 1, y - 1)
                node.neighbor_nw = self.get_node(x - 1, y + 1)
                node.neighbor_se = self.get_node(x + 1, y - 1)
                node.neighbor_sw = self.get_node(x + 1, y + 1)

    def update_cost(self, current: Node, next: Node, cost: int, direction: Direction) -> None:
        if next is None or next.closed or not next.accessible:
            return

        direction_overhead = 0 if current.parent_direction == direction else 500000000
        new_cost = next.heuristic + cost + direction_overhead

        if new_cost < next.cost_heuristic:
            next.cost = cost
            next.cost_heuristic = new_cost
            next.parent_direction = direction
            heapq.heappush(self.opened, next)
            next.parent = current

    def compute_path(self, start_x: int, start_y: int, objectif_x: int, objectif_y: int) -> None:
        if self.grid[objectif_x][objectif_y] is None:
            self.logger.error("Objective is in forbidden area.")
            return

        if self.grid[start_x][start_y] is None:
            self.logger.error("Start is in forbidden area.")
            return

        for x in range(self.dim_x):
            dist_x = abs(objectif_x - x)
            for y in range(self.dim_y):
                temp = self.grid[x][y]
                if temp is not None:
                    temp.cost = float('inf')
                    temp.cost_heuristic = float('inf')
                    temp.parent = None
                    temp.closed = False
                    temp.heuristic = (dist_x + abs(objectif_y - y)) * self.DIST_H_V

        self.opened.clear()
        start = self.grid[start_x][start_y]
        start.cost = 0
        start.cost_heuristic = start.heuristic
        start.parent_direction = Direction.NULL
        heapq.heappush(self.opened, start)

        while self.opened:
            current = heapq.heappop(self.opened)
            if current.closed:
                continue

            current.closed = True
            if current.x == objectif_x and current.y == objectif_y:
                return

            cost_h_v = current.cost + self.DIST_H_V
            cost_diag = current.cost + self.DIST_DIAGONALE

            self.update_cost(current, current.neighbor_n, cost_h_v, Direction.N)
            self.update_cost(current, current.neighbor_s, cost_h_v, Direction.S)
            self.update_cost(current, current.neighbor_e, cost_h_v, Direction.E)
            self.update_cost(current, current.neighbor_w, cost_h_v, Direction.W)
            self.update_cost(current, current.neighbor_ne, cost_diag, Direction.NE)
            self.update_cost(current, current.neighbor_nw, cost_diag, Direction.NW)
            self.update_cost(current, current.neighbor_se, cost_diag, Direction.SE)
            self.update_cost(current, current.neighbor_sw, cost_diag, Direction.SW)

    def get_path(self, start: Position, end: Position) -> Optional[List[Position]]:
        self.logger.info(f"Start A* to compute path between {start} and {end}")
        start_time = time.time_ns()

        if start == end:
            return [start]

        if (start.x < 0 or start.x >= self.dim_x or start.y < 0 or start.y >= self.dim_y or
            end.x < 0 or end.x >= self.dim_x or end.y < 0 or end.y >= self.dim_y):
            self.logger.error("Point out of bounds!")
            return None

        if self.grid[start.x][start.y] is None:
            self.logger.error("Start in forbidden area")
            return None

        if self.grid[end.x][end.y] is None:
            self.logger.error("Objective in forbidden area")
            return None

        self.compute_path(start.x, start.y, end.x, end.y)
        path = []
        current = self.grid[end.x][end.y]

        if current is None or current.parent is None:
            self.logger.error("No path found!")
            return None

        while current is not None:
            path.append(Position(current.x, current.y))
            current = current.parent

        self.logger.info(f"A* end computation in {(time.time_ns() - start_time)/1000000:.2f} ms")
        return path