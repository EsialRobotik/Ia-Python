import logging
import time
from typing import List, Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction


@action_type("list")
class ActionList(ThreadedAction):
    """Execute une liste d'actions sequentiellement."""

    def __init__(self, action_repository, action_list: List[str], flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.action_list = action_list
        self.action_repository = action_repository

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionList':
        if "list" not in payload:
            raise ValueError("'list' not found in list action config payload")
        return cls(deps["action_repository"], payload["list"])

    def reset(self) -> None:
        super().reset()
        logger = logging.getLogger(__name__)
        for action_id in self.action_list:
            if self.action_repository.has_action(action_id):
                self.action_repository.get_action(action_id).reset()
            else:
                logger.error(f"no action with id {action_id} found in action list")

    def check_action_list_for_missing(self):
        missing_ids = [a for a in self.action_list if not self.action_repository.has_action(a)]
        if missing_ids:
            raise ValueError(f"Actions missing from repository: {', '.join(missing_ids)}")

    def _run(self) -> None:
        logger = logging.getLogger(__name__)
        for action_id in self.action_list:
            if self._stop_requested:
                break
            if not self.action_repository.has_action(action_id):
                logger.error(f"no action with id {action_id} found in action list")
                continue
            action = self.action_repository.get_action(action_id)

            try:
                action.reset()
                action.execute()
                logger.info(f"action with id {action_id} started")
                while not action.finished() and not self._stop_requested:
                    time.sleep(0.01)
                if self._stop_requested:
                    action.stop()
            except Exception as e:
                logger.error(f"Exception error {e}")
            logger.info(f"action with id {action_id} finished")
        self._finished = True