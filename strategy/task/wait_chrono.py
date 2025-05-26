from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask

class WaitChrono(AbstractTask):

    def __init__(self, desc: str, chrono: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            timeout=chrono,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.WAIT_CHRONO,
            mirror=mirror,
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"wait-chrono#{self.timeout}",
            "position": self.end_point.to_dict()
        }