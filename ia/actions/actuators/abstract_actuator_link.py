from abc import ABC, abstractmethod

class AbstractActuatorLink(ABC):
    """
    Abstratc class to represent a proxy that can communicate with an actuator
    """

    @abstractmethod
    def send_command(self, cmd: bytes, wait_response: bool, timeout: float) -> bytearray:
        """
        Send the given command to the actuator.
        If waitResponse == True, waits the response of the actuator. Otherwise returns instantly an empty bytearray.
        """
        pass