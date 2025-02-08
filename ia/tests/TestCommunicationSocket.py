from api.CommunicationSocket import CommunicationSocket
from tests.AbstractTest import AbstractTest
from time import sleep
import logging

class TestCommunicationSocket(AbstractTest):
    def test(self):
        logger = logging.getLogger(__name__)
        socket1 = CommunicationSocket(
            host=self.config_data['comSocket']['host'],
            port=self.config_data['comSocket']['port'],
        );
        sleep(1)
        socket2 = CommunicationSocket(
            host=self.config_data['comSocket']['host'],
            port=self.config_data['comSocket']['port'],
        );
        sleep(1)
        socket1.send_message("Hello from socket1")
        sleep(1)
        logger.info(f"Message on socket2: {socket2.last_message}")
        socket2.send_message("Hello from socket2")
        sleep(1)
        logger.info(f"Message on socket1: {socket1.last_message}")