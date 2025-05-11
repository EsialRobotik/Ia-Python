from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.enum.sub_type import SubType
from strategy.enum.type import Type
from strategy.task.abstract_task import AbstractTask

class SetSpeed(AbstractTask):

    def __init__(self, desc: str, speed: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            dist=speed,
            task_type=Type.DEPLACEMENT,
            subtype=SubType.SET_SPEED,
            mirror=mirror,
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"speed#{self.dist}",
            "position": self.end_point.to_dict()
        }