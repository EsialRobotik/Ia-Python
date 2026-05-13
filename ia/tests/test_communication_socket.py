import logging
from time import sleep

from ia.api.communication_socket import CommunicationSocket
from ia.tests.abstract_test import AbstractTest


class TestCommunicationSocket(AbstractTest):
    def test(self):
        logger = logging.getLogger(__name__)
        socket1 = CommunicationSocket(
            host=self.config_data['comSocket']['host'],
            port=self.config_data['comSocket']['port'],
        )
        sleep(1)
        socket2 = CommunicationSocket(
            host=self.config_data['comSocket']['host'],
            port=self.config_data['comSocket']['port'],
        )
        sleep(1)
        socket1.send_message("Hello from socket1")
        sleep(1)
        logger.info(f"Message on socket1: {list(socket1.messages.queue)}")
        logger.info(f"Message on socket2: {list(socket2.messages.queue)}")
        socket2.send_message("Hello from socket2")
        sleep(1)
        logger.info(f"Message on socket1: {list(socket1.messages.queue)}")
        logger.info(f"Message on socket2: {list(socket2.messages.queue)}")