import logging
import threading
from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.actions.actuators.abstract_actuator_link import AbstractActuatorLink
from ia.actions.actuators.actuator_command import ActuatorCommand


class ActionActuator(AbstractAction):
    """
    Class to represent a wait action that pauses execution for a specified duration.
    """

    def __init__(self, actuator_link: AbstractActuatorLink, actuator_commands: list[ActuatorCommand], flags: Optional[str]) -> None:
        """
        Initialize the ActionWait with a duration and optional flags.

        :param duration_seconds: The duration to wait in seconds.
        :param flags: Optional flags to help in the decision process.
        """
        self.logger = logging.getLogger(__name__)
        self.actuator_link = actuator_link
        self.actuator_commands = actuator_commands
        self.flags = flags
        self.thread = None
        self.is_finished = False

    def execute(self) -> None:
        """
        Start the execution of the actuator action in a separate thread.
        """
        if self.thread is None:
            self.thread = threading.Thread(target=self.thread_function)
            self.thread.daemon = True
            self.thread.start()

    def finished(self) -> bool:
        """
        Check if the actuator action has finished executing.

        :return: True if the actuator action has finished executing, False otherwise.
        """
        if self.thread is None:
            return False
        return self.is_finished

    def stop(self) -> None:
        """
        Request to stop the execution of the actuator action.
        """
        self.request_stop = True

    def reset(self) -> None:
        """
        Reset the actuator action so it can be re-executed with execute().
        """
        if self.thread is None:
            return
        if self.thread.is_alive:
            self.stop()
            self.thread.join()
        self.thread = None

    def get_flag(self) -> Optional[str]:
        """
        Return potential existing flag of the actuator action to help AI in its decision process.

        :return: The flag associated with the actuator action, or None if no flag is set.
        """
        return self.flags

    def thread_function(self):
        """
        Function executed in a separate thread to run the actions in the actuator action sequentially.
        It sets the `is_finished` flag to False at the start and to True at the end.
        It iterates over each commnd to send to the actuator and sends it. Waits for each command return if it is requested
        by the command.
        If a stop request is made, it stops sending the commands and exits the loop.
        """
        self.is_finished = False
        self.request_stop = False
        for command in self.actuator_commands:
            if not self.request_stop:
                b = bytearray()
                b.extend(map(ord, command.command))
                command_response = self.actuator_link.send_command(b, not command.isasync, command.timeout)
                if (not command.isasync):
                    if not command_response == 'ok':
                        if len(command_response) == 0:
                            self.logger.warning(f'Command "{command.command}" returned an unexpected empty response')
                        else :
                            self.logger.warning(f'Command "{command.command}" returned an unexpected string : "{command_response}"')
        self.is_finished = True