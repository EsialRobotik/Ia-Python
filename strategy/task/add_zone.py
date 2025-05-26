from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class AddZone(AbstractTask):

    def __init__(self, desc: str, item_id: str, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            task_type=StepType.ELEMENT,
            subtype=StepSubType.ADD_ZONE,
            mirror=mirror,
            item_id=item_id
        )

    def execute(self, start_point: Position):
        self.end_point = start_point
        self.path_finding.update_dynamic_zone(self.item_id, True)
        return {
            "task": self.desc,
            "command": f"add-zone#{self.item_id}",
            "position": self.end_point.to_dict()
        }