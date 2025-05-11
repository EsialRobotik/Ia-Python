import math

from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.enum.sub_type import SubType
from strategy.enum.type import Type
from strategy.task.abstract_task import AbstractTask


class GoToBack(AbstractTask):
    def __init__(self, desc, position_x, position_y, mirror= Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            position_x=position_x,
            position_y=position_y,
            task_type=Type.DEPLACEMENT,
            subtype=SubType.GOTO_BACK,
            mirror=mirror
        )

    def execute(self, start_point: Position):
        self.end_point = Position(
            self.position_x,
            self.position_y,
            (self.calculate_theta(start_point, self.position_x, self.position_y) - math.pi) % (2 * math.pi)
        )
        return {
            "task": self.desc,
            "command": f"goto-back#{self.position_x};{self.position_y}",
            "position": self.end_point.to_dict()
        }