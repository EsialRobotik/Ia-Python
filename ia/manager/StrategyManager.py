import json

from ia.step import Objective


class StrategyManager:
    """
    Manages the strategy configuration and objectives for a given year.

    Attributes:
        current_index (int): The current index of the objective being processed.
        year (int): The year of the strategy configuration.
        objectives (list): A list of objectives to be performed.
        action_flags (list): A list of action flags.
        action_finished (dict): A dictionary to track the completion status of actions.
    """

    def __init__(self, year: int) -> None:
        """
        Initialize the StrategyManager.

        Args:
            year (int): The year of the strategy configuration.
        """
        self.current_index = 0
        self.year = year
        self.objectives = []
        self.action_flags = []
        self.action_finished = {}

    def prepare_objectives(self, is_color0: bool) -> None:
        """
        Prepare objectives based on the strategy configuration file.

        Args:
            is_color0 (bool): Determines which color strategy to load.
        """
        with open(f'config/{self.year}/strategy.json') as strategy_file:
            strategy = json.load(strategy_file).get('color0' if is_color0 else 'color3000')
            strategy_file.close()
            for objective_config in strategy:
                self.objectives.append(Objective(objective_config))
                self.action_finished[objective_config.get('id')] = False

    def __str__(self) -> str:
        return (f'StrategyManager(year={self.year}, '
            f'current_index={self.current_index}, '
            f'objectives={self.objectives}, '
            f'action_flags={self.action_flags}, '
            f'action_finished={self.action_finished})')

    def add_action_flag(self, flag: str) -> None:
        """
        Add an action flag to the action_flags list.

        Args:
            flag (str): The action flag to be added.
        """
        self.action_flags.append(flag)

    def get_next_objective(self) -> Objective | None:
        """
        Get the next objective to perform.

        Returns:
            Objective | None: The next objective to perform or None if all objectives are finished.
        """
        # TODO: Devenir intelligent avec gestion des flags, des priorités, etc.

        if self.current_index >= len(self.objectives):
            return None

        next_objective = self.objectives[self.current_index]
        self.current_index += 1

        return next_objective