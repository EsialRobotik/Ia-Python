import logging
import time
from typing import List, Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction


@action_type("list_join")
class ActionListJoin(ThreadedAction):
    """Lance toutes les actions de la liste en parallèle et attend qu'elles soient toutes terminées."""

    def __init__(self, action_repository, action_list: List[str], flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.action_list = action_list
        self.action_repository = action_repository

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionListJoin':
        if "list" not in payload:
            raise ValueError("'list' not found in list_join action config payload")
        return cls(deps["action_repository"], payload["list"])

    def reset(self) -> None:
        super().reset()
        logger = logging.getLogger(__name__)
        for action_id in self.action_list:
            if self.action_repository.has_action(action_id):
                self.action_repository.get_action(action_id).reset()
            else:
                logger.error(f"no action with id {action_id} found in action list_join")

    def check_action_list_for_missing(self):
        missing_ids = [a for a in self.action_list if not self.action_repository.has_action(a)]
        if missing_ids:
            raise ValueError(f"Actions missing from repository: {', '.join(missing_ids)}")

    def _run(self) -> None:
        logger = logging.getLogger(__name__)
        actions = []
        for action_id in self.action_list:
            if not self.action_repository.has_action(action_id):
                logger.error(f"no action with id {action_id} found in action list_join")
                continue
            actions.append(self.action_repository.get_action(action_id))

        for action in actions:
            action.execute()

        while not all(action.finished() for action in actions):
            if self._stop_requested:
                for action in actions:
                    action.stop()
                break
            time.sleep(0.01)

        self._finished = True