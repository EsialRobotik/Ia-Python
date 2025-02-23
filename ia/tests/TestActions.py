import logging
from time import sleep

from ia.api.ax12 import AX12LinkSerial, AX12, AX12Position
from ia.tests import AbstractTest
from ia.actions.ActionRepository import ActionRepository
from ia.actions.ActionRepositoryFactory import ActionRepositoryFactory
from ia.actions.ax12.ActionAX12Position import ActionAX12Position
import time

class TestActions(AbstractTest):
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

    def test(self) -> None:
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
        actionRepo = ActionRepositoryFactory.fromJsonFiles(self.config_data['actions']['dataDir'], link)

        while True:
            command = input("Action: ")
            if actionRepo.hasAction(command):
                actionRepo.getAction(command).reset()
                actionRepo.getAction(command).execute()
                while not actionRepo.getAction(command).finished():
                    time.sleep(0.01)
            else:
                print(f"L'action '{command}' n'existe pas")