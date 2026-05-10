import logging

from ia.actions.abstract_action import AbstractAction


class ActionRepository:

    def __init__(self) -> None:
        self._actions: dict[str, AbstractAction] = {}
        # Snapshot of strategy flags valid for the action currently being executed.
        # Updated by ActionManager.execute_command; consulted by ActionList/ActionListJoin
        # to skip sub-actions whose needed_flag is missing.
        self.active_flags: list[str] = []
        self.logger = logging.getLogger(__name__)

    def has_action(self, action_id: str) -> bool:
        return action_id.upper() in self._actions

    def get_action(self, action_id: str) -> AbstractAction | None:
        key = action_id.upper()
        if key not in self._actions:
            self.logger.warning(f"Action id '{action_id}' not found in action collection")
            return None
        return self._actions[key]

    def register_action(self, action_id: str, action: AbstractAction) -> None:
        self._actions[action_id.upper()] = action