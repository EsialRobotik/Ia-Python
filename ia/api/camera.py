import logging
logger = logging.getLogger(__name__)
from picamera2 import Picamera2

class Camera:
    """
    A class used to represent the Camera. It provides methods to interact with the camera hardware.
    """

    def __init__(self) -> None:
        """
        Initialize the Camera object.
        """
        self.is_initialized = False
        self.picam = None

    def initialize(self) -> None:
        """
        Initialize the camera hardware.
        """
        if not self.is_initialized:
            logger.info("Initializing the camera.")
            self.picam = Picamera2()
            self.picam.start(show_preview = False)
            self.is_initialized = True
            logger.info("Camera initialized successfully.")

    def capture_image(self): # TODO: type hint
        """
        Capture an image from the camera.
        :return: Captured image.
        """
        if not self.is_initialized:
            raise Exception("Camera is not initialized. Call initialize() before capturing images.")

        logger.debug("Capturing image from camera.")
        image = self.picam.capture_array()
        logger.debug("Image captured successfully.")
        return image

    def release(self) -> None:
        """
        Release the camera resources.
        """
        if self.is_initialized:
            logger.info("Releasing camera resources.")
            self.picam.stop()
            self.is_initialized = False
            logger.info("Camera resources released successfully.")