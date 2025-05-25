import logging
import threading
from typing import Optional

from ia.actions.abstract_action import AbstractAction


class ActionWait(AbstractAction):
    """
    Class to represent a wait action that pauses execution for a specified duration.
    """

    def __init__(self, duration_seconds: float, flags: Optional[str]) -> None:
        """
        Initialize the ActionWait with a duration and optional flags.

        :param duration_seconds: The duration to wait in seconds.
        :param flags: Optional flags to help in the decision process.
        """
        self.logger = logging.getLogger(__name__)
        self.duration_seconds = duration_seconds
        self.flags = flags
        self.timer_thread = None
        self.is_finished = False

    def execute(self) -> None:
        """
        Execute the wait action by starting a timer thread.
        """
        if self.timer_thread is None:
            self.logger.info(f"start waiting of {self.duration_seconds} second(s)")
            self.is_finished = False
            self.timer_thread = threading.Timer(self.duration_seconds, self.timer_end)
            self.timer_thread.start()

    def finished(self) -> bool:
        """
        Check if the wait action has finished executing.

        :return: True if the wait action has finished executing, False otherwise.
        """
        return self.is_finished

    def stop(self) -> None:
        """
        Stop the wait action if it is currently running.
        """
        if not self.timer_thread is None and self.timer_thread.is_alive:
            self.timer_thread.cancel()

    def reset(self) -> None:
        """
        Reset the wait action so it can be re-executed with execute().
        """
        if self.timer_thread is None:
            return
        if self.timer_thread.is_alive:
            self.timer_thread.cancel()
        self.timer_thread = None

    def get_flag(self) -> Optional[str]:
        """
        Retrieve the flag associated with the wait action.

        :return: The flag associated with the wait action, or None if no flag is set.
        """
        return self.flags

    def timer_end(self):
        """
        Callback function called when the timer ends.
        It sets the `is_finished` flag to True and logs the completion of the wait action.
        """
        self.logger.info(f"waiting finished")
        self.is_finished = True
    