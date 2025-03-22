import logging
from ia.actions.actuators.abstract_actuator_link import AbstractActuatorLink

import time

import serial

from ia.actions.actuators.abstract_actuator_link import AbstractActuatorLink


class SerialActuatorLink(AbstractActuatorLink):
    """
    Class to represent a Serial communication link to an actuator
    """

    def __init__(self, serial_port: str, baud_rate: int) -> None:
        self.logger = logging.getLogger(__name__)
        try:
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=0.05
            )
            self.serial.dtr = False
            self.serial.rts = False
            self.serial.open()
        except serial.SerialException as e:
            if str(e) == 'Port is already open.':
                self.serial.close()
                self.serial.open()
            else:
                raise Exception("Error initializing serial port: " + str(e))

    def send_command(self, cmd: bytes, wait_response: bool, timeout: float) -> bytearray:
        response = bytearray()
        try:
            self.serial.write(cmd)
            self.serial.flush()

            writetime = time.time()
            while wait_response:
                # Read data from the serial port
                data = self.serial.read()
                if not data and (len(response) > 0 or time.time() - writetime > timeout):
                    break
                response.extend(data)
        except serial.SerialException as e:
            raise Exception("Error sending command: " + str(e))
        return response