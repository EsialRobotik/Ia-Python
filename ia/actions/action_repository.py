from ia.actions.abstract_action import AbstractAction


class ActionRepository:

    def __init__(self) -> None:
        self._actions: dict[str, AbstractAction] = {}

    def has_action(self, action_id: str) -> bool:
        return action_id.upper() in self._actions

    def get_action(self, action_id: str) -> AbstractAction:
        key = action_id.upper()
        if key not in self._actions:
            raise KeyError(f"Action id '{action_id}' not found in action collection")
        return self._actions[key]

    def register_action(self, action_id: str, action: AbstractAction) -> None:
        self._actions[action_id.upper()] = action