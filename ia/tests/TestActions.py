import logging
import time

from ia.actions.ActionRepositoryFactory import ActionRepositoryFactory
from ia.api.ax12 import AX12LinkSerial
from ia.tests import AbstractTest


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
        actionRepo = ActionRepositoryFactory.from_json_files(self.config_data['actions']['dataDir'], link)

        while True:
            command = input("Action: ")
            if actionRepo.has_action(command):
                actionRepo.get_action(command).reset()
                actionRepo.get_action(command).execute()
                while not actionRepo.get_action(command).finished():
                    time.sleep(0.01)
            else:
                print(f"L'action '{command}' n'existe pas")