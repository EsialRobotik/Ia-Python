import logging

from ia.api.detection.ultrasound.srf08 import Srf08
from ia.tests.abstract_test import AbstractTest


class TestSrf08(AbstractTest):
    """
    A test class for the SRF08 ultrasonic sensors.
    This class is designed to test the functionality of multiple SRF04 sensors
    by reading their distance measurements in a loop and printing the results.
    Attributes:
        config_data (dict): Configuration data containing GPIO pin mappings and sensor parameters.
    Methods:
        test():
            Initializes the SRF04 sensors with the provided GPIO pin mappings and sensor parameters.
            Continuously reads and prints the distance measurements from each sensor.
    """

    def test(self) -> None:
        """
        Tests the functionality of the Srf08 ultrasonic sensors.
        This method initializes all Srf08 sensors from the `config_data` dictionary. It then enters an infinite loop
        where it continuously prints the distance readings from each sensor every second.
        Infinite Loop:
            Prints the distance readings from each sensor every second.
        """

        logger = logging.getLogger(__name__)
        addresses = self.config_data["detection"]["ultrasound"]["gpioList"]
        window_size = self.config_data["detection"]["ultrasound"]["windowSize"]
        srfs = []
        for address in addresses:
            srfs.append(Srf08(
                desc=address['desc'],
                address=address['address'],
                x=address['x'],
                y=address['y'],
                angle=address['angle'],
                threshold=address['threshold'],
                window_size=window_size
            ))
        while True:
            for srf in srfs:
                logger.info(f'{srf.desc} : {srf.get_distance()}mm')