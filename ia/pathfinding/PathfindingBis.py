import heapq
import json
import time

import numpy as np
from shapely.geometry import Polygon, Point

from ia.utils import Position


class PathfindingBis:
    def __init__(self, config_file, active_color):
        with open(config_file, 'r') as f:
            self.config = json.load(f)["table"]

        self.resolution = 10  # Taille d'une case en mm
        self.cols = self.config["sizeX"] // self.resolution
        self.rows = self.config["sizeY"] // self.resolution
        self.marge = self.config["marge"]
        self.active_color = active_color  # Color0 ou Color3000
        self.grid = np.zeros((self.rows, self.cols), dtype=np.uint8)

        self.set_obstacles()
        self.set_dynamic_zones()

    def set_obstacles(self):
        """Ajoute les zones interdites en fonction de la couleur active."""
        for zone in self.config["forbiddenZones"]:
            if zone["type"] != self.active_color:
                if zone["forme"] == "polygone":
                    self.mark_zone(zone["points"], self.marge)
                elif zone["forme"] == "cercle":
                    self.mark_circle(zone["centre"], zone["rayon"] + self.marge)

    def set_dynamic_zones(self):
        for zone in self.config["dynamicZones"]:
            if zone["forme"] == "polygone":
                self.mark_zone(zone["points"], self.marge, active=zone["active"])
            elif zone["forme"] == "cercle":
                self.mark_circle(zone["centre"], zone["rayon"] + self.marge, active=zone["active"])

    def update_dynamic_zone(self, zone_id, active):
        """Met à jour l'état d'une zone dynamique."""
        for zone in self.config["dynamicZones"]:
            if zone["id"] == zone_id:
                zone["active"] = active

    def mark_zone(self, points, marge, active=True):
        """Marque ou libère une zone polygonale sur la grille."""
        poly = Polygon([(p["x"], p["y"]) for p in points]).buffer(marge)
        minx, miny, maxx, maxy = map(int, poly.bounds)
        value = 1 if active else 0

        for x in range(minx, maxx, self.resolution):
            for y in range(miny, maxy, self.resolution):
                if poly.contains(Point(x, y)):
                    self.set_grid(x, y, value)

    def mark_circle(self, center, radius, active=True):
        """Marque ou libère une zone circulaire sur la grille."""
        cx, cy = center["x"], center["y"]
        r_sq = radius ** 2
        value = 1 if active else 0

        for x in range(cx - radius, cx + radius, self.resolution):
            for y in range(cy - radius, cy + radius, self.resolution):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                    self.set_grid(x, y, value)

    def set_grid(self, x, y, value):
        """Marque ou libère une cellule de la grille."""
        row, col = y // self.resolution, x // self.resolution
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row, col] = value

    def heuristic(self, a, b):
        """Heuristique basée sur la distance de Manhattan pour accélérer A*."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, node):
        """Retourne les voisins accessibles, y compris les diagonales."""
        x, y = node
        neighbors = [(x + dx, y + dy) for dx, dy in [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]]
        return [(nx, ny) for nx, ny in neighbors
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny, nx] == 0]

    def a_star(self, start, goal):
        """Implémentation optimisée de l'algorithme A*."""
        start = (start[0] // self.resolution, start[1] // self.resolution)
        goal = (goal[0] // self.resolution, goal[1] // self.resolution)

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
                return self.simplify_path([(x * self.resolution, y * self.resolution) for x, y in path[::-1]])

            for neighbor in self.get_neighbors(current):
                move_cost = 1 if abs(neighbor[0] - current[0]) + abs(neighbor[1] - current[1]) == 1 else 1.4
                tentative_g_score = g_score[current] + move_cost
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # Pas de chemin trouvé

    def simplify_path(self, path):
        """Simplifie le chemin en conservant les positions x, y en entier."""
        if len(path) < 2:
            return path
        simplified_path = [path[0]]
        for i in range(1, len(path) - 1):
            if (path[i + 1][0] - path[i][0]) * (path[i][1] - path[i - 1][1]) != (path[i + 1][1] - path[i][1]) * (path[i][0] - path[i - 1][0]):
                simplified_path.append(path[i])
        simplified_path.append(path[-1])
        final_path = []
        for p in simplified_path:
            final_path.append(Position(p[0], p[1]))
        return final_path

if __name__ == "__main__":
    # Exécution
    total_time = time.time_ns()
    table = PathfindingBis("config/2025/config.json", "color0")  # Utilisation de la configuration JSON
    start = (1000, 700)
    goal = (1700, 2000)
    start_time = time.time_ns()
    path = table.a_star(start, goal)
    print(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms")
    if path is not None:
        for position in path:
            print(position)
    else:
        print("Aucun chemin trouvé")
    print(f"Total computation in {(time.time_ns() - total_time) / 1000000:.2f} ms")

    total_time = time.time_ns()
    print("Changement zones interdites")
    table.update_dynamic_zone("Plants_N", False)
    table.update_dynamic_zone("Plants_S", False)
    table.set_dynamic_zones()
    start_time = time.time_ns()
    path = table.a_star(start, goal)
    print(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms")
    if path is not None:
        for position in path:
            print(position)
    else:
        print("Aucun chemin trouvé")
    print(f"Total computation in {(time.time_ns() - total_time) / 1000000:.2f} ms")
