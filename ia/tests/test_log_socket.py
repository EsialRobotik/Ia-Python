import logging
import logging.handlers
import time

from ia.api.log_socket import LogSocket
from ia.tests.abstract_test import AbstractTest


class TestLogSocket(AbstractTest):
    """
    TestLogSocket is a test class that extends AbstractTest to test the functionality of a logging socket.
    Methods:
        test():
            Creates a socket handler using LogSocket with configuration data and adds it to the root logger.
            Logs messages with different severity levels (info, debug, warning, error) to test the socket handler.
    """

    def test(self) -> None:
        """
        Test method to create a socket handler and log messages at different levels.
        This method performs the following steps:
        1. Creates a socket handler using the `LogSocket` class with the configuration data.
        2. Adds the created socket handler to the root logger.
        3. Logs messages at various levels (info, debug, warning, error) to test the socket handler.
        Configuration data required:
        - loggerSocket:
            - host: The host address for the socket.
            - port: The port number for the socket.
            - who: Identifier for the logger.
        Logs:
        - "log socket Test 1" at INFO level.
        - "log socket Test 2" at DEBUG level.
        - "log socket Test 3" at WARNING level.
        - "log socket Test 4" at ERROR level.
        """

        logger = logging.getLogger(__name__)
        # create a socket handler
        socket_handler = LogSocket(
            host=self.config_data['comSocket']['host']
        ).get()
        logging.getLogger('').addHandler(socket_handler)
        logger.info("log socket Test 1")
        logger.debug("log socket Test 2")
        logger.warning("log socket Test 3")
        logger.error("log socket Test 4")
        time.sleep(2)