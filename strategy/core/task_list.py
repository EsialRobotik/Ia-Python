from typing import List, Optional

from strategy.core.objective import Objective
from strategy.task.abstract_task import AbstractTask


class TaskList:
    def __init__(self, mirror_size: int = 0, with_mirror: bool = True):
        self.tasks: List[AbstractTask] = []
        self.mirror_task_list: Optional[TaskList] = TaskList(0, False) if with_mirror else None
        self.mirror_size = mirror_size

    def get_mirror_task_list(self) -> Optional['TaskList']:
        return self.mirror_task_list

    def set_mirror_task_list(self, mirror_task_list: 'TaskList') -> None:
        self.mirror_task_list = mirror_task_list

    def add(self, task: AbstractTask, mirror_task: Optional[AbstractTask] = None) -> bool:
        self.tasks.append(task)

        if mirror_task and self.mirror_task_list:
            self.mirror_task_list.add(mirror_task)
        return True

    def generate_objective(self, name: str, id: int, score: int, priority: int, skip_flag: Optional[str] = None) -> Objective:
        return Objective(name, id, score, priority, self.tasks, skip_flag)

    def generate_mirror_objective(self, name: str, id: int, score: int, priority: int, skip_flag: Optional[str] = None) -> Objective:
        objective = Objective(name, id, score, priority, None, skip_flag)
        try:
            mirror_tasks = self.mirror_task_list.tasks if self.mirror_task_list else []
            mirror_size = self.mirror_size if self.mirror_size > 0 else 3000
            objective.generate_mirror(self.tasks, mirror_tasks, mirror_size)
        except Exception as e:
            print(f"Error generating mirror objective: {e}")
        return objective