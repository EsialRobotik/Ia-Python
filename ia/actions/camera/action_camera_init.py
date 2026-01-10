import logging
import threading
from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.api.camera import Camera

class ActionCameraInit(AbstractAction):
    """
    Class to represent an initialization action for the camera.

    This action sets up the camera for subsequent operations, it must 
    be executed before any other camera-related actions, otherwise you will wait indefinitely.
    """

    def __init__(self, camera: Camera, flags: Optional[str] = None) -> None:
        """
        Initialize the ActionCameraInit with optional flags.

        :param flags: Optional flags to help in the decision process.
        """
        self.logger = logging.getLogger(__name__)
        self.flags = flags
        self.camera_thread = None
        self.is_finished = False

    def execute(self) -> None:
        """
        Execute the cmera initialization action by starting the camera thread,
        and initializing the camera.
        """
        if self.camera_thread is None:
            self.is_finished = False
            self.camera_thread = threading.Thread(target=self.__init_camera)
            self.camera_thread.start()

    def __init_camera(self) -> None:
        """
        Internal method to initialize the camera.
        """
        self.logger.info(f"start camera initialization")
        self.camera.initialize()
        self.is_finished = True
        self.logger.info(f"camera initialization finished")
        

    def finished(self) -> bool:
        """
        Check if the camera init action has finished executing.

        :return: True if the camera init action has finished executing, False otherwise.
        """
        return self.is_finished

    def stop(self) -> None:
        """
        Stop the camera init action if it is currently running.
        """
        if not self.camera_thread is None and self.camera_thread.is_alive:
            self.camera_thread.cancel()

    def reset(self) -> None:
        """
        Reset the camera init action so it can be re-executed with execute().
        """
        if self.camera_thread is None:
            return
        if self.camera_thread.is_alive:
            self.camera_thread.cancel()
        self.camera_thread = None

    def get_flag(self) -> Optional[str]:
        """
        Retrieve the flag associated with the wait action.

        :return: The flag associated with the wait action, or None if no flag is set.
        """
        return self.flags
    