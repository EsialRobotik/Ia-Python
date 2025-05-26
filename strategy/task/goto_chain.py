from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask

class GoToChain(AbstractTask):

    def __init__(self, desc: str, position_x: int, position_y: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            position_x=position_x,
            position_y=position_y,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.GOTO_CHAIN,
            mirror=mirror
        )

    def execute(self, start_point: Position):
        self.end_point = Position(
            self.position_x,
            self.position_y,
            self.calculate_theta(start_point, self.position_x, self.position_y)
        )
        return {
            "task": self.desc,
            "command": f"goto-chain#{self.position_x};{self.position_y}",
            "position": self.end_point.to_dict()
        }