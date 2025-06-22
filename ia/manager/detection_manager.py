import logging
import math
from typing import Dict, List

import numpy as np
from shapely.geometry import Polygon

from ia.api.detection.lidar.lidar_rpa2 import LidarRpA2
from ia.api.detection.ultrasound.srf import Srf
from ia.asservissement.asserv import Asserv
from ia.asservissement.movement_direction import MovementDirection
from ia.utils.position import Position


class DetectionManager:
    def __init__(self, sensors: list[Srf], lidar: LidarRpA2, asserv: Asserv, table_config: Dict) -> None:
        """
        Initializes the DetectionManager with a list of SRF sensors, a Lidar, an Asserv and a Pathfinding.

        Args:
            sensors (list[srf]): A list of SRF sensors, the last one is backward, the others are in the front of
            the robot.
            lidar (lidar_rpa2): An instance of the Lidar class.
            asserv (asserv): An instance of the Asserv class.
            table_config (Dict): The configuration of the table.
        """

        self.logger = logging.getLogger(__name__)
        self.sensors = sensors
        self.lidar = lidar
        self.asserv = asserv
        self.table_config = table_config
        self.ignore_detection_grid = np.zeros(
            shape=(self.table_config.get("sizeX"), self.table_config.get("sizeY")),
            dtype=np.uint8
        )
        self.set_ignore_detection_grid()

    def set_ignore_detection_grid(self) -> None:
        """
        Adds dynamic zones to the grid.

        This method iterates through the dynamic zones defined in the configuration
        and marks them on the grid. It considers the active state of each zone to
        determine whether it should be marked as an obstacle.

        Returns
        -------
        None
        """

        for zone in self.table_config["detectionIgnoreZone"]:
            if zone["forme"] == "polygone":
                self.mark_zone(zone["points"])
            elif zone["forme"] == "cercle":
                self.mark_circle(zone["centre"], zone["rayon"])

    def mark_zone(self, points: List[Dict[str, int]]) -> None:
        poly = Polygon([(p["x"], p["y"]) for p in points])
        minx, miny, maxx, maxy = map(int, poly.bounds)

        for x in range(minx, maxx):
            for y in range(miny, maxy):
                #if poly.contains(Point(x, y)):
                self.ignore_detection_grid[x, y] = True

    def mark_circle(self, center: Dict[str, int], radius: int) -> None:
        cx, cy = center["x"], center["y"]
        r_sq = radius ** 2

        for x in range(cx - radius, cx + radius):
            for y in range(cy - radius, cy + radius):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                    self.ignore_detection_grid[x, y] = True

    def get_obstacle_position(self, sensor: Srf, distance: int) -> Position:
        """
        Returns the position of the detected obstacle.

        Args:
            sensor (srf): The sensor that detected the obstacle.
            distance (int): The distance to the obstacle.

        Returns:
            position: The position of the detected obstacle.
        """

        self.logger.debug(f"Sensor {sensor.desc} detected an obstacle at distance {distance}")

        # Position relative au robot
        x_obstacle_relative_to_robot = sensor.get_position().x + distance * math.cos(sensor.get_position().theta)
        y_obstacle_relative_to_robot = sensor.get_position().y + distance * math.sin(sensor.get_position().theta)

        # Position du robot sur la table
        robot_position = self.asserv.position

        # Changement de repère (robot -> table)
        x_obstacle_relative_to_table = int(
            robot_position.x +
            x_obstacle_relative_to_robot * math.cos(robot_position.theta) -
            y_obstacle_relative_to_robot * math.sin(robot_position.theta)
        )
        y_obstacle_relative_to_table = int(
            robot_position.y +
            x_obstacle_relative_to_robot * math.sin(robot_position.theta) +
            y_obstacle_relative_to_robot * math.cos(robot_position.theta)
        )

        return Position(x_obstacle_relative_to_table, y_obstacle_relative_to_table)

    def is_emergency_detection_front(self, ignore_direction: bool = False) -> bool:
        """
        Check if an emergency detection is triggered by the front sensors.

        Returns:
            bool: True if an emergency detection is triggered, False otherwise.
        """

        if not ignore_direction and self.asserv.direction != MovementDirection.FORWARD:
            return False

        for sensor in self.sensors[:-1]:
            if sensor.get_distance() <= sensor.threshold:
                return self.must_stop(self.get_obstacle_position(sensor, sensor.get_distance()))
        return False

    def is_emergency_detection_back(self, ignore_direction: bool = False) -> bool:
        """
        Check if an emergency detection is triggered by the back sensor.

        Returns:
            bool: True if an emergency detection is triggered, False otherwise.
        """

        if not ignore_direction and self.asserv.direction != MovementDirection.BACKWARD:
            return False

        sensor = self.sensors[-1]
        if sensor.get_distance() <= sensor.threshold:
            return self.must_stop(self.get_obstacle_position(sensor, sensor.get_distance()))
        return False

    def must_stop(self, position: Position) -> bool:
        """
        Determines if the robot must stop based on the position of the object detected

        Args:
            position (position): The current position of the robot.

        Returns:
            bool: True if the robot must stop, False otherwise.
        """
        must_stop = (50 < position.x < (self.table_config.get("sizeX") - 50) and
                50 < position.y < (self.table_config.get("sizeY") - 50) and
                not self.ignore_detection_grid[position.x][position.y])
        if must_stop:
            self.logger.info(f"Emergency stop, enemy detected at {position}")
        return must_stop

    def is_trajectory_blocked(self, goto_queue: list[Position]) -> bool:
        """
        Checks if the trajectory is blocked by any detected points.

        Parameters
        ----------
        goto_queue : list[Position] Trajectory to check.

        Returns
        -------
        bool
            True if the trajectory is blocked, False otherwise.
        """
        if not goto_queue:
            return False

        current_position = self.asserv.position
        if goto_queue:
            goto_queue.insert(0, Position(current_position.x, current_position.y))

        for i in range(len(goto_queue) - 1):
            start = goto_queue[i]
            end = goto_queue[i + 1]
            for center in self.lidar.detected_points:
                if self.is_segment_intersecting_circle(start, end, center, 150):
                    self.logger.info(f"Trajectory blocked by {center}")
                    return True
        return False

    def is_segment_intersecting_circle(self, start: Position, end: Position, center: Position, radius: int) -> bool:
        """
        Checks if a line segment intersects with a circle.

        Parameters
        ----------
        start : position
            The starting point of the segment.
        end : position
            The ending point of the segment.
        center : position
            The center of the circle.
        radius : int
            The radius of the circle.

        Returns
        -------
        bool
            True if the segment intersects the circle, False otherwise.
        """
        dx = end.x - start.x
        dy = end.y - start.y
        fx = start.x - center.x
        fy = start.y - center.y

        a = dx * dx + dy * dy

        if a == 0:
            return False

        b = 2 * (fx * dx + fy * dy)
        c = (fx * fx + fy * fy) - radius * radius

        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return False

        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)

        return 0 <= t1 <= 1 or 0 <= t2 <= 1