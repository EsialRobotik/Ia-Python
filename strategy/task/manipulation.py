from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask

class Manipulation(AbstractTask):
    def __init__(self, desc: str, action_id: str, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            task_type=StepType.MANIPULATION,
            subtype=StepSubType.NONE,
            mirror=mirror,
            action_id=action_id
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"action#{self.action_id}",
            "position": self.end_point.to_dict()
        }