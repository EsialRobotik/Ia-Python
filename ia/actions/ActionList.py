import threading
import time
from typing import List
from typing import Optional

from ia.actions.AbstractAction import AbstractAction
from ia.actions.ActionRepository import ActionRepository


class ActionList(AbstractAction):
    """
    Class to manage and execute a list of actions sequentially.
    """

    def __init__(self, action_repository: ActionRepository, action_list: List[str], flags: Optional[str]) -> None:
        """
        Initialize the ActionList with a repository of actions, a list of action IDs, and optional flags.

        :param action_repository: The repository containing available actions.
        :param action_list: A list of action IDs to be executed in sequence.
        :param flags: Optional flags to help in the decision process.
        """
        self.action_list = action_list
        self.action_repository = action_repository
        self.flags = flags
        self.thread = None
        self.is_finished = False
        self.request_stop = False
    
    def check_action_list_for_missing(self):
        """
        Check that each action of the actionList exists in the action repository
        """
        missing_ids = []
        for a in self.action_list:
            if not self.action_repository.has_action(a):
                missing_ids.append(a)
        if len(missing_ids) > 0:
            missing_action_ids_str = ", ".join(missing_ids)
            raise Exception(f"A least on action from the action list is missing form the action repository : {missing_action_ids_str}")

    def execute(self) -> None:
        """
        Start the execution of the action list in a separate thread.
        """
        if self.thread is None:
            self.thread = threading.Thread(target=self.thread_function)
            self.thread.daemon = True
            self.thread.start()

    def finished(self) -> bool:
        """
        Check if the action list has finished executing.

        :return: True if the action list has finished executing, False otherwise.
        """
        if self.thread is None:
            return False
        return self.is_finished

    def stop(self) -> None:
        """
        Request to stop the execution of the action list.
        """
        self.request_stop = True

    def reset(self) -> None:
        """
        Reset the action list so it can be re-executed with execute().
        """
        if self.thread is None:
            return
        if self.thread.is_alive:
            self.stop()
            self.thread.join()
        for actionId in self.action_list:
            self.action_repository.get_action(actionId).reset()
        self.thread = None

    def get_flag(self) -> Optional[str]:
        """
        Return potential existing flag of the action list to help AI in its decision process.

        :return: The flag associated with the action list, or None if no flag is set.
        """
        return self.flags

    def thread_function(self):
        """
        Function executed in a separate thread to run the actions in the action list sequentially.
        It sets the `is_finished` flag to False at the start and to True at the end.
        It iterates over each action ID in the action list, retrieves the corresponding action from the repository,
        and executes it. It waits for each action to finish before moving to the next one.
        If a stop request is made, it stops the current action and exits the loop.
        """
        self.is_finished = False
        self.request_stop = False
        for actionId in self.action_list:
            if not self.request_stop:
                action = self.action_repository.get_action(actionId)
                action.execute()
                while not action.finished() and self.request_stop == False:
                    time.sleep(0.01)
                if self.request_stop:
                    action.stop()
        self.is_finished = True