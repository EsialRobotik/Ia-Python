from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask

class SetSpeed(AbstractTask):

    def __init__(self, desc: str, speed: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            dist=speed,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.SET_SPEED,
            mirror=mirror,
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"speed#{self.dist}",
            "position": self.end_point.to_dict()
        }