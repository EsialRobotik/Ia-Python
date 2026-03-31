import math

from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class GoToBack(AbstractTask):
    def __init__(self, desc, position_x, position_y, mirror= Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            position_x=position_x,
            position_y=position_y,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.GOTO_BACK,
            mirror=mirror
        )

    def calculate_theta(self, current_position, final_x, final_y):
        angle = math.atan2(final_y - current_position.y, final_x - current_position.x) + math.pi
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle <= -math.pi:
            angle += 2 * math.pi
        return angle

    def execute(self, start_point: Position):
        self.end_point = Position(
            self.position_x,
            self.position_y,
            self.calculate_theta(start_point, self.position_x, self.position_y)
        )
        return {
            "task": self.desc,
            "command": f"goto-back#{self.position_x};{self.position_y}",
            "position": self.end_point.to_dict()
        }