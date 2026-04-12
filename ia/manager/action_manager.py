import logging
import time
from typing import Callable, Dict, List, Optional

from ia.actions.abstract_action import AbstractAction
from ia.actions.action_repository import ActionRepository


class ActionManager:

    def __init__(
        self,
        action_repository: ActionRepository,
        actions_config: Dict,
        stop_hooks: Optional[List[Callable]] = None
    ) -> None:
        self.action_flag = None
        self.current_action: Optional[AbstractAction] = None
        self.actions_config = actions_config
        self.action_repository = action_repository
        self.stop_hooks = stop_hooks or []
        self.logger = logging.getLogger(__name__)

    def get_action(self, action_id: str) -> AbstractAction:
        return self.action_repository.get_action(action_id)

    def execute_command(self, action_id: str) -> None:
        self.logger.info(f"Execute action {action_id}")
        self.action_flag = None
        self.current_action = self.action_repository.get_action(action_id)
        self.current_action.reset()
        self.current_action.execute()

    def stop_actions(self) -> None:
        if self.current_action is not None:
            self.current_action.stop()
        for hook in self.stop_hooks:
            try:
                hook()
            except Exception as e:
                self.logger.error(f"Error in stop hook: {e}")

    def is_last_execution_finished(self) -> bool:
        if self.current_action.finished():
            self.action_flag = self.current_action.get_flag()
            self.logger.info("Action finished")
            return True
        return False

    def init(self) -> None:
        self.logger.info("Init actuators")
        for action_id in self.actions_config['init']:
            self.logger.info(f"Init action: {action_id}")
            self.execute_command(action_id)
            while not self.is_last_execution_finished():
                try:
                    time.sleep(0.005)
                except InterruptedError as e:
                    self.logger.error(e)