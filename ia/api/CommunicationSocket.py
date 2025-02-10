import logging
logger = logging.getLogger(__name__)

import socket
import threading

class CommunicationSocket:
    """
    A class to handle socket communication.
    Attributes:
    -----------
    host : str
        The hostname or IP address of the server to connect to.
    port : int
        The port number of the server to connect to.
    last_message : str or None
        The last message received from the server.
    sock : socket.socket
        The socket object used for communication.
    read_thread : threading.Thread
        The thread responsible for reading messages from the server.
    Methods:
    --------
    __init__(self, host, port):
        Initializes the CommunicationSocket with the given host and port, 
        and starts the connection and read thread.
    receive_message(self):
        Continuously receives messages from the server and updates the 
        last_message attribute.
    send_message(self, message):
        Sends a message to the server.
    """

    def __init__(self, host: str, port: int) -> None:
        """
        Initializes the CommunicationSocket instance.
        Args:
            host (str): The hostname or IP address of the server to connect to.
            port (int): The port number of the server to connect to.
        Attributes:
            host (str): The hostname or IP address of the server.
            port (int): The port number of the server.
            last_message (str or None): The last message received from the server.
            sock (socket.socket): The socket object used for communication.
            read_thread (threading.Thread): The thread responsible for reading messages from the server.
        Raises:
            socket.error: If the connection to the server fails.
        """

        self.host = host
        self.port = port
        self.last_message = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to {self.host} on port {self.port}")
            self.send_message("robot")
        except socket.error as e:
            logger.error(f"Failed to connect to {self.host} on port {self.port}: {e}")
        self.read_thread = threading.Thread(target=self.receive_message)
        self.read_thread.daemon = True
        self.read_thread.start()
        
    def receive_message(self) -> None:
        """
        Continuously receives messages from the socket.
        This method runs an infinite loop that attempts to receive messages from the socket.
        If a message is successfully received, it is decoded from UTF-8 and logged.
        If the message has a length greater than 0, it is stored as the last received message.
        If a socket error occurs during message reception, an error is logged.
        Raises:
            socket.error: If there is an error receiving the message from the socket.
        """

        while True:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                logger.info(f"Received message: {message}")
                if len(message) > 0:
                    self.last_message = message
            except socket.error as e:
                logger.error(f"Failed to receive message: {e}")

    def send_message(self, message: str) -> None:
        """
        Sends a message through the socket.
        Args:
            message (str): The message to be sent.
        Raises:
            socket.error: If there is an error sending the message.
        Logs:
            Info: When the message is successfully sent.
            Error: If there is a failure in sending the message.
        """

        try:
            self.sock.send(f"{message}".encode())
            logger.info(f"Sent message: {message}")
        except socket.error as e:
            logger.error(f"Failed to send message: {e}")