import math

from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class Go(AbstractTask):

    def __init__(self, desc: str, dist: int, mirror: Mirror = Mirror.MIRRORY, timeout: int = -1):
        super().__init__(
            desc=desc,
            dist=dist,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.GO,
            mirror=mirror,
            timeout=timeout
        )

    def execute(self, start_point: Position):
        new_x = start_point.x + int(self.dist * math.cos(start_point.theta))
        new_y = start_point.y + int(self.dist * math.sin(start_point.theta))
        self.end_point = Position(new_x, new_y, start_point.theta)
        return {
            "task": self.desc,
            "command": f"go#{self.dist}",
            "position": self.end_point.to_dict()
        }