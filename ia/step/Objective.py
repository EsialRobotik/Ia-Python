import logging
from typing import Dict, Optional

from ia.step import Step


class Objective:
    def __init__(self, objective_config: Dict):
        self.step_index = -1
        self.description = objective_config.get('description')
        self.id = objective_config.get('id')
        self.points = objective_config.get('points')
        self.priority = objective_config.get('priority')
        self.step_list = []
        for step_config in objective_config.get('tasks'):
            self.step_list.append(Step(step_config))
        self.skip_flag = objective_config.get('skipFlag')
        self.needed_flag = objective_config.get('neededFlag')
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        return (f"Objective(description={self.description}, objective_id={self.id}, "
            f"points={self.points}, priority={self.priority}, skip_flag={self.skip_flag}, "
            f"needed_flag={self.needed_flag})")

    def has_next_step(self) -> bool:
        """
        Check if there is a next step in the step list.

        Returns:
            bool: True if there is a next step, False otherwise.
        """
        return self.step_index < len(self.step_list) - 1

    def get_next_step(self) -> Optional[Step]:
        """
        Get the next step in the step list, considering skip and needed flags and increment cursor.

        Returns:
            Step: The next step if available, otherwise None.
        """
        self.step_index += 1
        step = self.step_list[self.step_index]

        # todo gérer les flags skip et needed

        return step

    def get_next_step_real(self) -> Optional[Step]:
        """
        Get the next step in the step list.

        Returns:
            Step: The next step if available, otherwise None.
        """
        if self.step_index + 1 < len(self.step_list):
            return self.step_list[self.step_index + 1]
        else:
            return None