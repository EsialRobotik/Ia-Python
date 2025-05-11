import copy
from typing import List, Optional

from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class Objective:
    def __init__(self, desc: str = "", id: int = 0, points: int = 0, priority: int = 0, tasks: Optional[List[AbstractTask]] = None, skip_flag: Optional[str] = None):
        self.desc = desc
        self.id = id
        self.points = points
        self.priority = priority
        self.tasks = tasks if tasks is not None else []
        self.skip_flag = skip_flag

    def generate_mirror(self, mirror_tasks: List[AbstractTask], specific_tasks: Optional[List[AbstractTask]] = None, mirror_size: int = 3000) -> None:
        specific_tasks = specific_tasks if specific_tasks is not None else []
        self.tasks = []

        for task in mirror_tasks:
            if task.mirror == Mirror.NONE:
                self.tasks.append(task)
            elif task.mirror == Mirror.MIRRORY:
                mirrored_task = copy.deepcopy(task)
                mirrored_task.position_y = mirror_size - mirrored_task.position_y
                if mirrored_task.item_id is not None:
                    mirrored_task.item_id = mirrored_task.item_id.replace("0_", f"{mirror_size}_")
                self.tasks.append(mirrored_task)

        self.tasks.extend(specific_tasks)

        if len(self.tasks) != len(mirror_tasks):
            tasks = "\t\t".join([str(obj) for obj in self.tasks])
            print(f"tasks : {tasks}")
            tasks = "\t\t".join([str(obj) for obj in mirror_tasks])
            print(f"mirror_tasks : {tasks}")
            raise Exception("Il manque des objectifs non ?")

    def to_dict(self) -> dict:
            return {
                "desc": self.desc,
                "id": self.id,
                "points": self.points,
                "priority": self.priority,
                "tasks": [task.to_dict() for task in self.tasks],
                "skip_flag": self.skip_flag
            }

    def __str__(self) -> str:
        tasks = "\t\t".join([str(obj) for obj in self.tasks])
        return (
            f"\n\t\tObjective{{"
            f"\n\t\t\tdesc='{self.desc}',"
            f"\n\t\t\tid={self.id},"
            f"\n\t\t\tpoints={self.points},"
            f"\n\t\t\tpriority={self.priority},"
            f"\n\t\t\ttasks=[{tasks}\n\t\t\t],"
            f"\n\t\t\tskip_flag={self.skip_flag}"
            f"\n\t\t}}"
        )