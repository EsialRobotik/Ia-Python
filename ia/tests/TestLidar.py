import logging
from time import sleep

from ia.api.detection.lidar import Lidar
from ia.asserv import Asserv
from ia.tests import AbstractTest


class TestLidar(AbstractTest):
    """
    A test class for the Lidar sensor.
    This class is used to test the functionality of the Lidar sensor by 
    initializing it with the configuration data and continuously printing 
    the detected points.
    Methods
    -------
    test():
        Initializes the Lidar sensor and continuously prints the detected points.
    """

    def test(self) -> None:
        logger = logging.getLogger(__name__)
        """
        Test method for initializing and using the Lidar class.
        This method initializes a Lidar object with configuration data and continuously
        prints the detected points from the Lidar sensor every second.
        Attributes:
            lidar (Lidar): An instance of the Lidar class initialized with the provided
                           configuration data.
        Configuration Data:
            detection:
                lidar:
                    serialPort (str): The serial port for the Lidar.
                    baudRate (int): The baud rate for the Lidar.
                    quality (int): The quality setting for the Lidar.
                    distance (int): The distance setting for the Lidar.
                    period (int): The period setting for the Lidar.
            asserv:
                serialPort (str): The serial port for the Asserv.
                baudRate (int): The baud rate for the Asserv.
        Loop:
            Continuously prints the detected points from the Lidar sensor every second.
        """

        lidar = Lidar(
            serial_port=self.config_data["detection"]["lidar"]["serialPort"], 
            baud_rate=self.config_data["detection"]["lidar"]["baudRate"], 
            quality=self.config_data["detection"]["lidar"]["quality"], 
            distance=self.config_data["detection"]["lidar"]["distance"], 
            period=self.config_data["detection"]["lidar"]["period"], 
            asserv=Asserv(
                serial_port=self.config_data["asserv"]["serialPort"],
                baud_rate=self.config_data["asserv"]["baudRate"],
                gostart_config={}
            )
        )
        while True:
            logger.info(lidar.get_detected_points())
            sleep(1)