import threading
from typing import List, Optional

from ia.pathfinding.astar import Astar, LineSimplificator
from ia.utils.Position import Position


class Pathfinding:
    """
    PathFinding is a class that handles pathfinding operations using the A* algorithm.
    Attributes:
        astar (Astar): An instance of the Astar class used for pathfinding.
        computation_ended (bool): A flag indicating if the path computation has ended.
        computation_start (bool): A flag indicating if the path computation has started.
        detected_points (List[Position]): A list of detected points.
    Methods:
        compute_path(start: Position, end: Position) -> None:
            Starts a new thread to compute the path from start to end.
        computation_thread(start: Position, end: Position) -> None:
            The thread method that computes the path.
        is_computation_start() -> bool:
            Returns whether the computation has started.
        is_computation_ended() -> bool:
            Returns whether the computation has ended.
        get_last_computed_path() -> Optional[List[Position]]:
            Returns the last computed path.
        set_computed_path(path: List[Position]) -> None:
            Sets the computed path.
        liberate_element_by_id(element_id: str) -> None:
            Makes the element with the given ID accessible.
        lock_element_by_id(element_id: str) -> None:
            Makes the element with the given ID inaccessible.
        get_detected_points() -> List[Position]:
            Returns the list of detected points.
        set_detected_points(detected_points: List[Position]) -> None:
            Sets the list of detected points.
        liberate_detected_points() -> None:
            Makes all detected points accessible.
        lock_detected_points() -> None:
            Makes all detected points inaccessible.
        get_points_from_shape(shape) -> List[Position]:
            Returns the points from the given shape.
        add_points_to_detection_ignore_quadrilaterium(points: List[Position]) -> None:
            Adds points to the detection ignore quadrilaterium.
    """

    def __init__(self, astar: Astar) -> None:
        self.astar = astar
        self.computation_ended = True
        self.computation_start = False
        self.detected_points: List[Position] = []
        self.computed_path = None

        for shape in self.astar.get_table().get_elements_list().keys():
            if shape.is_active():
                for p in self.astar.get_table().get_elements_list()[shape]:
                    self.astar.set_temporary_accessible(p.x, p.y, False)

    def compute_path(self, start: Position, end: Position) -> None:
        t = threading.Thread(target=self.computation_thread, args=(start, end))
        self.computation_start = True
        self.computation_ended = False
        self.computed_path = None
        t.start()

    def computation_thread(self, start: Position, end: Position) -> None:
        rectified_start = Position(start.x // 10, start.y // 10)
        rectified_end = Position(end.x // 10, end.y // 10)
        path = self.astar.get_path(start=rectified_start, end=rectified_end)
        self.computed_path = []
        if path is None:
            self.computation_ended = True
            self.computation_start = False
            return

        simple_path = LineSimplificator.get_simple_lines(path)
        simple_path.reverse()
        for p in simple_path:
            self.computed_path.append(Position(p.x * 10, p.y * 10))
        if self.computed_path:
            self.computed_path[-1] = end
        self.computation_ended = True
        self.computation_start = False

    def is_computation_start(self) -> bool:
        return self.computation_start

    def is_computation_ended(self) -> bool:
        return self.computation_ended

    def get_last_computed_path(self) -> Optional[List[Position]]:
        return self.computed_path

    def set_computed_path(self, path: List[Position]) -> None:
        self.computed_path = path

    def liberate_element_by_id(self, element_id: str) -> None:
        for p in self.astar.get_table().find_element_by_id(element_id):
            self.astar.set_temporary_accessible(p.x, p.y, True)

    def lock_element_by_id(self, element_id: str) -> None:
        for p in self.astar.get_table().find_element_by_id(element_id):
            self.astar.set_temporary_accessible(p.x, p.y, False)

    def get_detected_points(self) -> List[Position]:
        return self.detected_points

    def set_detected_points(self, detected_points: List[Position]) -> None:
        self.detected_points = detected_points

    def liberate_detected_points(self) -> None:
        for p in self.detected_points:
            self.astar.set_temporary_accessible(p.x, p.y, True)

    def lock_detected_points(self) -> None:
        for p in self.detected_points:
            self.astar.set_temporary_accessible(p.x, p.y, False)

    def get_points_from_shape(self, shape) -> List[Position]:
        return self.astar.get_table().get_points_from_shape(shape)

    def add_points_to_detection_ignore_quadrilaterium(self, points: List[Position]) -> None:
        self.astar.get_table().add_points_to_detection_ignore_quadrilaterium(points)