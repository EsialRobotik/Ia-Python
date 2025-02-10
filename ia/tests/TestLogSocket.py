import logging
import logging.handlers
import socket
import threading
import time

from ia.api import LogSocket
from ia.tests import AbstractTest


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

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 4269))
        self.sock.send(b'logListener')
        self.read_thread = threading.Thread(target=self.receive_message)
        self.read_thread.daemon = True
        self.read_thread.start()

        logger = logging.getLogger(__name__)
        # create a socket handler
        socket_handler = LogSocket(host='localhost').get()
        logging.getLogger('').addHandler(socket_handler)
        logger.info("log socket Test 1")
        logger.debug("log socket Test 2")
        logger.warning("log socket Test 3")
        logger.error("log socket Test 4")
        time.sleep(2)
        self.sock.close()

    def receive_message(self):
        print("Starting to receive messages")
        while True:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                print(f"Received message: {message}")
            except socket.error as e:
                print(f"Failed to receive message: {e}")