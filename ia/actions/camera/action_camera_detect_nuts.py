import logging
import threading
from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.api.camera import Camera

class ActionCameraDetectNuts(AbstractAction):
    """
    Class to represent a detection action for nuts using the camera.

    This action captures an image and processes it to detect the nuts. 
    It raises flags depending on which nut crates must be rotated.

    IMPORTANT: This action requires the camera to be initialized beforehand.
    """

    def __init__(self, camera: Camera, flags: Optional[str] = None) -> None:
        """
        Initialize the ActionCameraInit with optional flags.

        :param flags: Optional flags to help in the decision process.
        """
        self.logger = logging.getLogger(__name__)
        self.flags = flags
        self.camera = camera
        self.is_finished = False

    def execute(self) -> None:
        """
        Execute the cmera initialization action by starting the camera thread,
        and initializing the camera.
        """
        # TODO: implement nut detection logic here

    def finished(self) -> bool:
        """
        Check if the action has finished executing.

        :return: True if the action has finished executing, False otherwise.
        """
        return self.is_finished

    def stop(self) -> None:
        """
        Stop the action if it is currently running.
        """
        # TODO: for now, you just cannot stop this action
        pass

    def reset(self) -> None:
        """
        Reset the action so it can be re-executed with execute().
        """
        self.is_finished = False

    def get_flag(self) -> Optional[str]:
        """
        Retrieve the flag associated with the wait action.

        :return: The flag associated with the wait action, or None if no flag is set.
        """
        return self.flags
    