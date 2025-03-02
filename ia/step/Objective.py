import logging
from typing import Dict, Optional, List

from ia.step import Step


class Objective:
    """
    Represents an objective with various attributes and configurations.

    Attributes
    ----------
    step_index : int
        Index of the current step in the step list.
    description : str
        Description of the objective.
    id : int
        Identifier of the objective.
    points : list
        List of points associated with the objective.
    priority : int
        Priority of the objective.
    step_list : list
        List of steps associated with the objective.
    skip_flag : str, optional
        Flag indicating if the objective should be skipped, default is None.
    needed_flag : str, optional
        Flag needed to execute the objective, default is None.
    action_flag : str, optional
        Flag raised when step is finished, default is None.
    logger : logging.Logger
        Logger for the objective.
    """

    def __init__(self, objective_config: Dict):
        """
        Initialize an Objective with its configuration.

        Parameters
        ----------
        objective_config : Dict
            Dictionary containing the configuration for the objective.
        """
        self.step_index = -1
        self.description = objective_config.get('description')
        self.id = objective_config.get('id')
        self.points = objective_config.get('points')
        self.priority = objective_config.get('priority')
        self.step_list = []
        for step_config in objective_config.get('tasks'):
            self.step_list.append(Step(step_config))
        self.skip_flag = objective_config.get('skipFlag', None)
        self.needed_flag = objective_config.get('neededFlag', None)
        self.action_flag = objective_config.get('actionFlag', None)
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

    def get_next_step(self, flags: List[str]) -> Optional[Step]:
        """
        Get the next step in the step list, considering skip and needed flags and increment cursor.

        Returns:
            Step: The next step if available, otherwise None.
        """
        self.step_index += 1
        step = self.step_list[self.step_index]

        if step.skip_flag is None and step.needed_flag is None:
            return step

        while ((step.skip_flag is not None and step.skip_flag in flags)
            or (step.needed_flag is not None and step.needed_flag not in flags)):
            self.logger.info(f'Skip step {step.step_id}')
            self.step_index += 1
            if not self.has_next_step():
                return None
            step = self.step_list[self.step_index]

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