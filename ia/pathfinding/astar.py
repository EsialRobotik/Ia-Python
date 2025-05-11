import logging
import math
import time
from typing import Dict, List, Tuple

import networkx as nx
from shapely.geometry import Polygon, Point

from ia.utils.position import Position


class AStar:
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
        self.graph = nx.grid_2d_graph(self.size_x, self.size_y)

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
                if zone["forme"] == "polygone":
                    self.mark_zone(zone["points"], self.marge, active=active)
                elif zone["forme"] == "cercle":
                    self.mark_circle(zone["centre"], zone["rayon"] + self.marge, active=active)

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

        poly = Polygon([(p["x"] // self.resolution, p["y"] // self.resolution) for p in points]).buffer(marge // self.resolution)
        minx, miny, maxx, maxy = map(int, poly.bounds)

        for x in range(max(0, minx), min(maxx, self.size_x)):
            for y in range(max(0, miny), min(maxy, self.size_y)):
                if poly.contains(Point(x, y)):
                    if active and self.graph.has_node((x, y)):
                        self.graph.remove_node((x, y))
                    elif not active and not self.graph.has_node((x, y)):
                        self.graph.add_node((x, y))
                        # Reconnecter le noeud aux voisins
                        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
                        for nx, ny in neighbors:
                            if 0 <= nx < self.size_x and 0 <= ny < self.size_y and self.graph.has_node((nx, ny)):
                                self.graph.add_edge((x, y), (nx, ny))

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

        cx, cy = center["x"] // self.resolution, center["y"] // self.resolution
        r_sq = (radius ** 2) // self.resolution

        for x in range(max(0, cx - radius), min(cx + radius, self.size_x)):
            for y in range(max(0, cy - radius), min(cy + radius, self.size_y)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                    if active and self.graph.has_node((x, y)):
                        self.graph.remove_node((x, y))
                    elif not active and not self.graph.has_node((x, y)):
                        self.graph.add_node((x, y))
                        # Reconnecter le noeud aux voisins
                        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
                        for nx, ny in neighbors:
                            if 0 <= nx < self.size_x and 0 <= ny < self.size_y and self.graph.has_node((nx, ny)):
                                self.graph.add_edge((x, y), (nx, ny))

    def heuristic(self, a, b, previous_direction=None) -> int:
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

        #(x1, y1) = a
        #(x2, y2) = b
        #return abs(x1 - x2) + abs(y1 - y2)
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])

        if previous_direction is None:
            return dx + dy

        direction = (a[0] - previous_direction[0], a[1] - previous_direction[1])
        next_direction = (b[0] - a[0], b[1] - a[1])

        if direction == (0, 0):
            return dx + dy

        # Calcul de l'angle entre les deux directions
        dot_product = direction[0] * next_direction[0] + direction[1] * next_direction[1]
        magnitude_a = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
        magnitude_b = math.sqrt(next_direction[0] ** 2 + next_direction[1] ** 2)
        cos_theta = dot_product / (magnitude_a * magnitude_b)

        angle_penalty = 10 * (1 - cos_theta)  # Plus l'angle est grand, plus la pénalité est forte
        return dx + dy + angle_penalty

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

        try:
            path = nx.astar_path(self.graph, start, goal, heuristic=self.heuristic)
            self.logger.info(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms")
            self.path = self.simplify_path([(x * self.resolution, y * self.resolution) for x, y in path])
            self.computation_finished = True
            self.logger.info(f"A* path simplified in {(time.time_ns() - start_time) / 1000000:.2f} ms")
        except nx.NetworkXNoPath:
            self.logger.info("Aucun chemin trouvé avec les obstacles placés.")

        self.computation_finished = True
        return

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