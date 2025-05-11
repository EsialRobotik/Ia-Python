from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.enum.sub_type import SubType
from strategy.enum.type import Type
from strategy.task.abstract_task import AbstractTask

class Wait(AbstractTask):

    def __init__(self, desc: str, ms_count: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            timeout=ms_count,
            task_type=Type.DEPLACEMENT,
            subtype=SubType.WAIT,
            mirror=mirror,
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        return {
            "task": self.desc,
            "command": f"wait#{self.timeout}",
            "position": self.end_point.to_dict()
        }