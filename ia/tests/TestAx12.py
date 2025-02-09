from api.PullCord import PullCord
from tests.AbstractTest import AbstractTest
from time import sleep
from api.ax12 import AX12
from api.ax12 import AX12LinkSerial
import logging
from time import sleep

class TestAx12(AbstractTest):
    """
    A test class for the AX12 servos.
    This class is used to test the functionality of the AX12 servos by 
    initializing it with the configuration data, reading it's current
    position and blinking its led
    Methods
    -------
    test():
        Initializes the AX12 servo prints its position and blinks its led
    """

    def test(self):
        logger = logging.getLogger(__name__)
        """
        Test method for initializing and using the AX12 class.
        This method initializes an AX12 object with configuration data and reads it's current
        position and blinks its led
        Attributes:
            link (AX12LinkSerial): An instance of the AX12LinkSerial class initialized with
                                   the provided configuration data.
            ax12 (AX12): An instance of the AX12 class initialized with the AX12LinkSerial 
        Configuration Data:
            actions:
                ax12:
                    serie (str): The serial port for the AX12 bus.
                    baud (int): The baud rate for the AX12 bus.
        Loop:
            Continuously blink the AX12 led every second.
        """
        logger.info(f"Instanciation de la laision série {self.config_data['actions']['ax12']['serie']}@{self.config_data['actions']['ax12']['baud']}...")
        link = AX12LinkSerial(self.config_data['actions']['ax12']['serie'], self.config_data['actions']['ax12']['baud'])

        axid = 12
        logger.info(f"Instanciation de l'ax12 n°{axid}...")
        ax12 = AX12(
            address=axid,
            serialLink=link
        )

        logger.info(f"Position brute actuelle du sevro : {ax12.read_servo_position()}")
        logger.info(f"Clignotement de la led pour toujours...")
        while True:
            ax12.set_led(True)
            sleep(1)
            ax12.set_led(False)
            sleep(1)