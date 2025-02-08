from tests.AbstractTest import AbstractTest
from time import sleep
from api.detection.ultrasound.Srf04 import Srf04
import logging

class TestSrf04(AbstractTest):
    """
    A test class for the SRF04 ultrasonic sensors.
    This class is designed to test the functionality of multiple SRF04 sensors
    by reading their distance measurements in a loop and printing the results.
    Attributes:
        config_data (dict): Configuration data containing GPIO pin mappings and sensor parameters.
    Methods:
        test():
            Initializes the SRF04 sensors with the provided GPIO pin mappings and sensor parameters.
            Continuously reads and prints the distance measurements from each sensor.
    """

    def test(self):
        """
        Tests the functionality of the Srf04 ultrasonic sensors.
        This method initializes four Srf04 sensors (front left, front middle, front right, and back)
        using GPIO pin configurations from the `config_data` dictionary. It then enters an infinite loop
        where it continuously prints the distance readings from each sensor every second.
        Attributes:
            gpioList (list): A list of dictionaries containing GPIO pin configurations for the sensors.
        Srf04 Parameters:
            trigger (int): GPIO pin number for the trigger.
            echo (int): GPIO pin number for the echo.
            x (float): X-coordinate of the sensor.
            y (float): Y-coordinate of the sensor.
            angle (float): Angle of the sensor.
            threshold (float): Distance threshold for the sensor.
        Infinite Loop:
            Prints the distance readings from each sensor every second.
        """

        logger = logging.getLogger(__name__)
        gpioList = self.config_data["detection"]["ultrasound"]["gpioList"];
        frontLeft = Srf04(
            trigger=gpioList[0]['trigger'],
            echo=gpioList[0]['echo'],
            x=gpioList[0]['x'],
            y=gpioList[0]['y'],
            angle=gpioList[0]['angle'],
            threshold=gpioList[0]['threshold']
        )
        frontMiddle = Srf04(
            trigger=gpioList[1]['trigger'],
            echo=gpioList[1]['echo'],
            x=gpioList[1]['x'],
            y=gpioList[1]['y'],
            angle=gpioList[1]['angle'],
            threshold=gpioList[1]['threshold']
        )
        frontRight = Srf04(
            trigger=gpioList[2]['trigger'],
            echo=gpioList[2]['echo'],
            x=gpioList[2]['x'],
            y=gpioList[2]['y'],
            angle=gpioList[2]['angle'],
            threshold=gpioList[2]['threshold']
        )
        back = Srf04(
            trigger=gpioList[3]['trigger'],
            echo=gpioList[3]['echo'],
            x=gpioList[3]['x'],
            y=gpioList[3]['y'],
            angle=gpioList[3]['angle'],
            threshold=gpioList[3]['threshold']
        )
        while True:
            logger.info(f"Front Left: {frontLeft.get_distance()}")
            logger.info(f"Front Middle: {frontMiddle.get_distance()}")
            logger.info(f"Front Right: {frontRight.get_distance()}")
            logger.info(f"Back: {back.get_distance()}")
            sleep(1)