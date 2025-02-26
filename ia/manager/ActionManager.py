import logging
import threading
import time
from typing import Dict

from ia.actions import ActionRepository, AbstractAction
from ia.api.ax12 import AX12LinkSerial


class ActionManager:
    """
    Manages the execution of actions using a repository and AX12 actuators.
    """

    def __init__(self, action_repository: ActionRepository, ax12_link: AX12LinkSerial, actions_config: Dict) -> None:
        """
        Initializes the ActionManager with the given action repository, AX12 link, and actions configuration.

        Parameters
        ----------
        action_repository : ActionRepository
            The repository containing available actions.
        ax12_link : AX12LinkSerial
            The serial link to the AX12 actuators.
        actions_config : Dict
            The configuration dictionary for actions.
        """
        self.action_flag = None
        self.current_action = None
        self.actions_config = actions_config
        self.action_repository = action_repository
        self.ax12_link = ax12_link
        self.logger = logging.getLogger(__name__)

    def get_action(self, action_id: str) -> AbstractAction:
        """
        Executes the command with the given action ID.

        Parameters
        ----------
        action_id : str
            The ID of the action to execute.
        """
        return self.action_repository.get_action(action_id)

    def execute_command(self, action_id: str) -> None:
        """
        Executes the command with the given action ID.

        Parameters
        ----------
        action_id : int
            The ID of the action to execute.
        """
        self.logger.info(f"Execute action {action_id}")
        self.action_flag = None
        self.current_action = self.action_repository.get_action(action_id)
        self.current_action.reset()
        thread = threading.Thread(target=self.current_action.execute())
        thread.start()

    def stop_actions(self) -> None:
        """
        Stops the current action.
        """
        self.ax12_link.enable_dtr(False)
        self.ax12_link.enable_rts(False)
        self.ax12_link.disable_ax12_and_shutdown_link()

    def is_last_execution_finished(self) -> bool:
        """
        Checks if the last execution is finished.

        Returns
        -------
        bool
            True if the last execution is finished, False otherwise.
        """
        if self.current_action.finished():
            self.action_flag = self.current_action.get_action_flag()
            return True
        return False

    def init(self) -> None:
        """
        Initialize actuators by executing initial actions.
        """
        self.logger.info("Init actuators")
        for action_id in self.actions_config['init']:
            self.logger.info(f"Init action: {action_id}")
            self.execute_command(action_id)
            while not self.is_last_execution_finished():
                try:
                    time.sleep(0.005)
                except InterruptedError as e:
                    self.logger.error(e)