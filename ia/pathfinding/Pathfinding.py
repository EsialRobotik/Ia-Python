import heapq
import logging
import time
from typing import Dict, List, Tuple

import numpy as np
from shapely.geometry import Polygon, Point

from ia.utils import Position


class Pathfinding:
    """
    A class to represent the pathfinding logic for a robot on a table.

    Attributes
    ----------
    computation_finished: bool
        Whether the pathfinding computation has finished.
    config : dict
        Configuration data for the table.
    resolution : int
        Size of a grid cell in mm.
    size_x : int
        Number of columns in the grid.
    size_y : int
        Number of rows in the grid.
    marge : int
        Margin to be considered around obstacles.
    active_color : str
        The active color for the pathfinding ('color0' or 'color3000').
    grid : np.ndarray
        The grid representing the table with obstacles and dynamic zones.

    Methods
    -------
    __init__(table_config: Dict, active_color: str) -> None:
        Initializes the Pathfinding object with the given configuration and active color.
    set_obstacles() -> None:
        Adds forbidden zones to the grid based on the active color.
    set_dynamic_zones() -> None:
        Adds dynamic zones to the grid.
    update_dynamic_zone(zone_id: str, active: bool) -> None:
        Updates the state of a dynamic zone.
    mark_zone(points: List[Dict[str, int]], marge: int, active: bool = True) -> None:
        Marks or clears a polygonal zone on the grid.
    mark_circle(center: Dict[str, int], radius: int, active: bool = True) -> None:
        Marks or clears a circular zone on the grid.
    set_grid(x: int, y: int, value: int) -> None:
        Marks or clears a cell in the grid.
    heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        Heuristic based on Manhattan distance for A* algorithm.
    get_neighbors(node: Tuple[int, int]) -> List[Tuple[int, int]]:
        Returns accessible neighbors, including diagonals.
    a_star(start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Position]]:
        Optimized implementation of the A* algorithm.
    simplify_path(path: List[Tuple[int, int]]) -> List[Position]:
        Simplifies the path by keeping integer x, y positions.
    """

    def __init__(self, table_config: Dict, active_color: str) -> None:
        """
        Initializes the Pathfinding object with the given configuration and active color.

        Parameters
        ----------
        table_config : dict
            Configuration data for the table.
        active_color : str
            The active color for the pathfinding ('color0' or 'color3000').
        """

        self.computation_finished = True
        self.config = table_config
        self.resolution = 10  # Taille d'une case en mm
        self.size_x = self.config["sizeX"] // self.resolution
        self.size_y = self.config["sizeY"] // self.resolution
        self.marge = self.config["marge"]
        self.active_color = active_color  # Color0 ou Color3000
        self.grid = np.zeros((self.size_y, self.size_x), dtype=np.uint8)

        self.set_obstacles()
        self.set_dynamic_zones()
        self.path = []
        self.logger = logging.getLogger(__name__)

    def set_obstacles(self) -> None:
        """
        Adds forbidden zones to the grid based on the active color.

        This method iterates through the forbidden zones defined in the configuration
        and marks them on the grid. It considers the active color to determine which
        zones should be marked as obstacles.

        Returns
        -------
        None
        """

        for zone in self.config["forbiddenZones"]:
            if zone["type"] != self.active_color:
                if zone["forme"] == "polygone":
                    self.mark_zone(zone["points"], self.marge)
                elif zone["forme"] == "cercle":
                    self.mark_circle(zone["centre"], zone["rayon"] + self.marge)
        for zone in self.config["forbiddenZones"]:
            if zone["type"] != self.active_color:
                if zone["forme"] == "polygone":
                    self.mark_zone(zone["points"], self.marge)
                elif zone["forme"] == "cercle":
                    self.mark_circle(zone["centre"], zone["rayon"] + self.marge)

    def set_dynamic_zones(self) -> None:
        """
        Adds dynamic zones to the grid.

        This method iterates through the dynamic zones defined in the configuration
        and marks them on the grid. It considers the active state of each zone to
        determine whether it should be marked as an obstacle.

        Returns
        -------
        None
        """

        for zone in self.config["dynamicZones"]:
            if zone["forme"] == "polygone":
                self.mark_zone(zone["points"], self.marge, active=zone["active"])
            elif zone["forme"] == "cercle":
                self.mark_circle(zone["centre"], zone["rayon"] + self.marge, active=zone["active"])

    def update_dynamic_zone(self, zone_id: str, active: bool) -> None:
        """
        Updates the state of a dynamic zone.

        This method iterates through the dynamic zones defined in the configuration
        and updates the active state of the zone with the given ID.

        Parameters
        ----------
        zone_id : str
            The ID of the dynamic zone to update.
        active : bool
            The new active state of the zone.

        Returns
        -------
        None
        """

        for zone in self.config["dynamicZones"]:
            if zone["id"] == zone_id:
                zone["active"] = active

    def mark_zone(self, points: List[Dict[str, int]], marge: int, active: bool = True) -> None:
        """
        Marks or clears a polygonal zone on the grid.

        This method takes a list of points defining a polygon and marks or clears the area
        on the grid based on the given margin and active state.

        Parameters
        ----------
        points : list of dict
            A list of points defining the polygon.
        marge : int
            The margin to be considered around the polygon.
        active : bool, optional
            Whether to mark (True) or clear (False) the zone. Defaults to True.

        Returns
        -------
        None
        """

        poly = Polygon([(p["x"], p["y"]) for p in points]).buffer(marge)
        minx, miny, maxx, maxy = map(int, poly.bounds)
        value = 1 if active else 0

        for x in range(minx, maxx, self.resolution):
            for y in range(miny, maxy, self.resolution):
                if poly.contains(Point(x, y)):
                    self.set_grid(x, y, value)

    def mark_circle(self, center: Dict[str, int], radius: int, active: bool = True) -> None:
        """
        Marks or clears a circular zone on the grid.

        This method takes the center and radius of a circle and marks or clears the area
        on the grid based on the given active state.

        Parameters
        ----------
        center : dict
            A dictionary with 'x' and 'y' keys representing the center of the circle.
        radius : int
            The radius of the circle.
        active : bool, optional
            Whether to mark (True) or clear (False) the zone. Defaults to True.

        Returns
        -------
        None
        """

        cx, cy = center["x"], center["y"]
        r_sq = radius ** 2
        value = 1 if active else 0

        for x in range(cx - radius, cx + radius, self.resolution):
            for y in range(cy - radius, cy + radius, self.resolution):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                    self.set_grid(x, y, value)

    def set_grid(self, x: int, y: int, value: int) -> None:
        """
        Marks or clears a cell in the grid.

        This method takes the x and y coordinates of a cell and sets its value in the grid.
        The value can be used to mark the cell as an obstacle or clear it.

        Parameters
        ----------
        x : int
            The x-coordinate of the cell.
        y : int
            The y-coordinate of the cell.
        value : int
            The value to set in the cell (e.g., 1 for obstacle, 0 for clear).

        Returns
        -------
        None
        """

        row, col = y // self.resolution, x // self.resolution
        if 0 <= row < self.size_y and 0 <= col < self.size_x:
            self.grid[row, col] = value

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """
        Heuristic function based on Manhattan distance for the A* algorithm.

        This function calculates the Manhattan distance between two points, which is
        the sum of the absolute differences of their Cartesian coordinates. It is used
        to estimate the cost of the cheapest path from the current node to the goal.

        Parameters
        ----------
        a : tuple of int
            The coordinates of the first point (x, y).
        b : tuple of int
            The coordinates of the second point (x, y).

        Returns
        -------
        int
            The Manhattan distance between the two points.
        """

        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Returns accessible neighbors, including diagonals.

        This method takes a node's coordinates and returns a list of accessible neighboring nodes.
        It considers both orthogonal and diagonal movements and ensures that the neighbors are within
        the grid boundaries and not marked as obstacles.

        Parameters
        ----------
        node : tuple of int
            The coordinates of the current node (x, y).

        Returns
        -------
        list of tuple of int
            A list of accessible neighboring nodes' coordinates.
        """

        x, y = node
        neighbors = [(x + dx, y + dy) for dx, dy in [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]]
        return [(nx, ny) for nx, ny in neighbors
                if 0 <= nx < self.size_x and 0 <= ny < self.size_y and self.grid[ny, nx] == 0]

    def a_star(self, start: Position, goal: Position) -> None:
        """
        Optimized implementation of the A* algorithm.

        This method performs the A* search algorithm to find the shortest path from the start
        position to the goal position on the grid. It uses a priority queue to explore nodes
        based on their estimated cost to reach the goal, considering both the actual cost
        from the start and the heuristic estimate to the goal.

        During execution, computation_finished is set to False and the path is stored in the path attribute.

        Parameters
        ----------
        start : tuple of int
            The starting coordinates (x, y) in millimeters.
        goal : tuple of int
            The goal coordinates (x, y) in millimeters.

        Returns
        -------
        None
        """

        start_time = time.time_ns()
        self.computation_finished = False
        self.path = []
        start = (start.x // self.resolution, start.y // self.resolution)
        goal = (goal.x // self.resolution, goal.y // self.resolution)
        self.logger.info(f"A* Compute path from {start} to {goal}")

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        heapq.heapify(open_set)

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                self.logger.info(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms")
                self.computation_finished = True
                self.path = self.simplify_path([(x * self.resolution, y * self.resolution) for x, y in path[::-1]])
                return

            for neighbor in self.get_neighbors(current):
                move_cost = 1 if abs(neighbor[0] - current[0]) + abs(neighbor[1] - current[1]) == 1 else 1.4
                tentative_g_score = g_score[current] + move_cost
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        self.logger.info(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms without path")
        self.computation_finished = True
        return  # Pas de chemin trouvé

    def simplify_path(self, path: List[Tuple[int, int]]) -> List[Position]:
        """
        Simplifies the path by keeping integer x, y positions.

        This method takes a list of path coordinates and simplifies it by removing unnecessary points
        that lie on the same straight line. It returns a list of Position objects representing the simplified path.

        Parameters
        ----------
        path : list of tuple of int
            A list of coordinates (x, y) representing the path.

        Returns
        -------
        list of Position
            A list of Position objects representing the simplified path.
        """

        if len(path) < 2:
            simplified_path = path
        else:
            simplified_path = [path[0]]
            for i in range(1, len(path) - 1):
                if (path[i + 1][0] - path[i][0]) * (path[i][1] - path[i - 1][1]) != (path[i + 1][1] - path[i][1]) * (path[i][0] - path[i - 1][0]):
                    simplified_path.append(path[i])
            simplified_path.append(path[-1])
        final_path = []
        for p in simplified_path:
            final_path.append(Position(p[0], p[1]))
        return final_path