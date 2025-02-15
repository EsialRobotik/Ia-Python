import logging

from ia.utils import Position

logger = logging.getLogger(__name__)

from gpiozero import DistanceSensor

class Srf04:
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


    def __init__(self, trigger: int, echo: int, x: int, y: int, angle: int, threshold: int) -> None:
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

        logger.info(f"Creating Srf04 object with trigger {trigger}, echo {echo}, x {x}, y {y}, angle {angle}, threshold {threshold}.")
        self.trigger = trigger
        self.echo = echo
        self.sensor = DistanceSensor(echo=echo, trigger=trigger)
        self.x = x
        self.y = y
        self.angle = angle
        self.threshold = threshold

    def get_position(self) -> Position:
        """
        Returns the position of the sensor as a Position object.
        """
        
        return Position(x=self.x, y=self.y, theta=self.angle)
    
    def get_threshold(self) -> int:
        """
        Returns the distance threshold of the sensor.
        """

        return self.threshold
    
    def get_distance(self) -> int:
        """
        Get the distance measured by the SRF04 sensor.
        Returns:
            float: The distance measured by the sensor in millimeters.
        """

        return int(self.sensor.distance * 1000)