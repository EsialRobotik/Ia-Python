import logging

from ia.api.detection.ultrasound.Srf import Srf

logger = logging.getLogger(__name__)

from gpiozero import DistanceSensor

class Srf04(Srf):
    """
    A class to represent an SRF04 ultrasonic sensor.
    Attributes
    ----------
    trigger : int
        GPIO pin number for the trigger.
    echo : int
        GPIO pin number for the echo.
    sensor : DistanceSensor
        Instance of the DistanceSensor class.
    x : int
        X-coordinate of the sensor's position.
    y : int
        Y-coordinate of the sensor's position.
    angle : int
        Orientation angle of the sensor.
    threshold : int
        Distance threshold for the sensor.
    Methods
    -------
    get_position():
        Returns the position of the sensor as a Position object.
    get_threshold():
        Returns the distance threshold of the sensor.
    get_distance():
        Returns the measured distance from the sensor in milimeters.
    """


    def __init__(self, trigger: int, echo: int, x: int, y: int, angle: int, threshold: int, window_size: int) -> None:
        """
        Initializes the Srf04 sensor with the given parameters.
        Args:
            trigger (int): GPIO pin number for the trigger.
            echo (int): GPIO pin number for the echo.
            x (int): X-coordinate of the sensor's position.
            y (int): Y-coordinate of the sensor's position.
            angle (int): Angle at which the sensor is mounted.
            threshold (int): Distance threshold for detection.
        """

        super().__init__(x, y, angle, threshold, window_size)
        logger.info(f"Creating Srf04 object with trigger {trigger}, echo {echo}, x {x}, y {y}, angle {angle}, threshold {threshold}.")
        self.trigger = trigger
        self.echo = echo
        self.sensor = DistanceSensor(
            echo=echo,
            trigger=trigger,
            queue_len= self.window_size
        )

    def get_distance(self) -> int:
        """
        Return the average measured distance from the sensor in the window of size windows_size in millimeters.
        Returns:
            float: The average distance measured by the sensor in millimeters.
        """
        return int(self.sensor.value * 1000)