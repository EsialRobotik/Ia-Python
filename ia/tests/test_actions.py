import logging
import time

from ia.actions.action_repository_factory import ActionRepositoryFactory
from ia.actions.actuators.actuator_link_repository_factory import ActuatorLinkRepositoryFactory
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.tests.abstract_test import AbstractTest


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

        logger.info(f"Instanciation of ax12 serial link {self.config_data['actions']['ax12']['serialPort']}@{self.config_data['actions']['ax12']['baudRate']}...")
        ax12_link_serial = AX12LinkSerial(self.config_data['actions']['ax12']['serialPort'], self.config_data['actions']['ax12']['baudRate'])
        logger.info("Instanciation of actuators serial links...")
        actuator_link_repository = ActuatorLinkRepositoryFactory.actuator_link_repository_from_json(self.config_data['actions']['actuators'])
        logger.info("Instanciation action repository...")
        actionRepo = ActionRepositoryFactory.from_json_files(self.config_data['actions']['dataDir'], ax12_link_serial, actuator_link_repository)

        while True:
            command = input("Action: ")
            if actionRepo.has_action(command):
                actionRepo.get_action(command).reset()
                actionRepo.get_action(command).execute()
                while not actionRepo.get_action(command).finished():
                    time.sleep(0.01)
            else:
                print(f"L'action '{command}' n'existe pas")