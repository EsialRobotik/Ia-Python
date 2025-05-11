from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.enum.sub_type import SubType
from strategy.enum.type import Type
from strategy.task.abstract_task import AbstractTask

class Face(AbstractTask):

    def __init__(self, desc: str, position_x: int, position_y: int, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            position_x=position_x,
            position_y=position_y,
            task_type=Type.DEPLACEMENT,
            subtype=SubType.FACE,
            mirror=mirror
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        self.end_point.theta = self.calculate_theta(start_point, self.position_x, self.position_y)
        return {
            "task": self.desc,
            "command": f"face#{self.position_x};{self.position_y}",
            "position": self.end_point.to_dict()
        }