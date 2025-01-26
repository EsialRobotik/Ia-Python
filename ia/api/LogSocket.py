import logging
import logging.handlers
logger = logging.getLogger(__name__)

class LogSocket:
    """
    A class to create a logging socket handler.
    Attributes:
    -----------
    socket_handler : logging.handlers.SocketHandler
        The socket handler for logging.
    Methods:
    --------
    __init__(host, port, who):
        Initializes the LogSocket with the given host, port, and identifier.
    get():
        Returns the socket handler.
    """

    def __init__(self, host, port, who):
        """
        Initializes a LogSocket object.
        Args:
            host (str): The host for the socket connection.
            port (int): The port number for the socket connection.
            who (str): Identifier for the log messages.
        Attributes:
            socket_handler (logging.handlers.SocketHandler): The handler for sending log messages to a remote socket.
        """

        self.socket_handler = logging.handlers.SocketHandler('localhost', 1664)
        formatter = logging.Formatter(f"%(asctime)s - {who} - %(name)s - %(levelname)s - %(message)s")
        self.socket_handler.setFormatter(formatter)
        logger.info(f"Creating LogSocket object with host {host} and port {port}.")

    def get(self):
        """
        Retrieve the socket handler.
        Returns:
            object: The socket handler instance.
        """

        return self.socket_handler