import logging
from typing import Dict, Optional, List

from ia.strategy.step import Step


class Objective:
    """
    Represents an objective with various attributes and configurations.

    Attributes
    ----------
    step_index : int
        Index of the current strategy in the strategy list.
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
    needed_flag : str, optional
        Flag needed to execute the objective, default is None.
    action_flag : str, optional
        Flag raised when objective is finished, default is None.
    clear_flags : list[str], optional
        Flags removed from the active flags when objective is finished, default is None.
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
        self.needed_flag = objective_config.get('needed_flag', None)
        self.action_flag = objective_config.get('action_flag', None)
        self.clear_flags = objective_config.get('clear_flags', None)
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        return (f"Objective(description={self.description}, objective_id={self.id}, "
            f"points={self.points}, priority={self.priority}, needed_flag={self.needed_flag}, "
            f"action_flag={self.action_flag}, clear_flags={self.clear_flags})")

    def has_next_step(self) -> bool:
        """
        Check if there is a next strategy in the strategy list.

        Returns:
            bool: True if there is a next strategy, False otherwise.
        """
        return self.step_index < len(self.step_list) - 1

    def get_next_step(self, flags: List[str]) -> Optional[Step]:
        """
        Get the next step in the step list, skipping those whose needed_flag is missing from the active flags.

        Returns:
            step: The next step if available, otherwise None.
        """
        self.step_index += 1
        step = self.step_list[self.step_index]

        while step.needed_flag is not None and step.needed_flag not in flags:
            self.logger.info(f'Skip step {step.description} (missing flag {step.needed_flag})')
            if not self.has_next_step():
                return None
            self.step_index += 1
            step = self.step_list[self.step_index]

        return step

    def get_next_step_real(self) -> Optional[Step]:
        """
        Get the next strategy in the strategy list.

        Returns:
            step: The next strategy if available, otherwise None.
        """
        if self.step_index + 1 < len(self.step_list):
            return self.step_list[self.step_index + 1]
        else:
            return None