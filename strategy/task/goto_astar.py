import time

from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class GoToAstar(AbstractTask):

    def __init__(self, desc: str, position_x: int, position_y: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            position_x=position_x,
            position_y=position_y,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.GOTO_ASTAR,
            mirror=mirror
        )
        self.path_finding = None

    def execute(self, start_point: Position):
        total_time = time.time_ns()
        print(f"Compute pathfinding from {start_point} to ({self.position_x},{self.position_y})")
        self.path_finding.a_star(
            Position(start_point.x, start_point.y),
            Position(self.position_x, self.position_y)
        )
        while not self.path_finding.computation_finished:
            time.sleep(0.05)
        print(f"Total computation in {(time.time_ns() - total_time) / 1000000:.2f} ms")

        result = []
        self.end_point = start_point
        path = self.path_finding.path
        if not path:
            print("Erreur de pathfinding")
            return ""

        for p in path:
            if self.end_point.x != p.x or self.end_point.y != p.y:
                self.end_point = Position(p.x, p.y, self.calculate_theta(self.end_point, p.x, p.y))
            result.append(
                {
                    "task": self.desc,
                    "command": f"goto-astar#{p.x};{p.y}",
                    "position": self.end_point.to_dict()
                }
            )
        return result