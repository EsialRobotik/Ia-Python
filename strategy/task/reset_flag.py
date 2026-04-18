from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class ResetFlag(AbstractTask):
    def __init__(self, desc: str, flags: list[str], mirror: Mirror = Mirror.NONE):
        super().__init__(
            desc=desc,
            task_type=StepType.ELEMENT,
            subtype=StepSubType.RESET_FLAG,
            mirror=mirror,
            reset_flags=flags
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"reset-flag#{','.join(self.reset_flags)}",
            "position": self.end_point.to_dict()
        }