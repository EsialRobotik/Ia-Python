from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class HaltAsserv(AbstractTask):

    def __init__(self, desc: str, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.HALT_ASSERV,
            mirror=mirror,
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": "halt-asserv",
            "position": self.end_point.to_dict()
        }