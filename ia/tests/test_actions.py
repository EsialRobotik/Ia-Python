import logging
import time

from ia.actions.action_repository_factory import ActionRepositoryFactory
from ia.actions.serial_port import SerialPort
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.api.camera import Camera
from ia.tests.abstract_test import AbstractTest


class TestActions(AbstractTest):

    def test(self) -> None:
        logger = logging.getLogger(__name__)

        ax12_link_serial = None
        serial_ports = {}
        camera = None
        if self.config_data['actions'].get('ax12') is not None:
            logger.info(f"Instanciation of ax12 serial link {self.config_data['actions']['ax12']['serialPort']}@{self.config_data['actions']['ax12']['baudRate']}...")
            ax12_link_serial = AX12LinkSerial(self.config_data['actions']['ax12']['serialPort'], self.config_data['actions']['ax12']['baudRate'])
        if self.config_data['actions'].get('actuators') is not None:
            logger.info("Instanciation of actuators serial links...")
            for actuator_config in self.config_data['actions']['actuators']:
                if actuator_config['type'] == 'serial':
                    port_id = actuator_config.get('id', str(len(serial_ports)))
                    serial_ports[port_id] = SerialPort(actuator_config['serialPort'], actuator_config['baudRate'])
        if self.config_data['actions'].get('camera') is not None:
            logger.info("Instanciation of camera...")
            camera = Camera()
        logger.info("Instanciation action repository...")
        action_repo = ActionRepositoryFactory.from_json_files(
            self.config_data['actions']['dataDir'], ax12_link_serial, serial_ports, camera=camera
        )

        while True:
            command = input("Action: ")
            if action_repo.has_action(command):
                action_repo.get_action(command).reset()
                action_repo.get_action(command).execute()
                while not action_repo.get_action(command).finished():
                    time.sleep(0.01)
            else:
                print(f"L'action '{command}' n'existe pas")