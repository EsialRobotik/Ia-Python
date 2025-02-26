from ia.actions.AbstractAction import AbstractAction

class ActionRepository:
    """
    Class to manage a repository of actions.
    """

    def __init__(self, action_list: dict[str, AbstractAction]):
        """
        Initialize the ActionRepository with a dictionary of actions.

        :param action_list: A dictionary where the keys are action IDs and the values are AbstractAction instances.
        """
        self.actions_list = action_list
    
    def has_action(self, action_id: str) -> bool:
        """
        Check if the action repository contains an action with the given ID.

        :param action_id: The ID of the action to check.
        :return: True if the action exists in the repository, False otherwise.
        """
        return action_id in self.actions_list

    def get_action(self, action_id: str) -> AbstractAction:
        """
        Retrieve an action from the repository by its ID.

        :param action_id: The ID of the action to retrieve.
        :return: The AbstractAction instance associated with the given ID.
        :raises KeyError: If the action ID is not found in the repository.
        """
        if action_id in self.actions_list:
            return self.actions_list[action_id]
        else:
            raise f'Action id {action_id} not found in action collection'

    def register_action(self, action_id: str, action: AbstractAction) -> None:
        """
        Register a new action in the repository.

        :param action_id: The ID of the action to register.
        :param action: The AbstractAction instance to register.
        """
        self.actions_list[action_id] = action