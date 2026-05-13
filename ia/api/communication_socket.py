import logging
logger = logging.getLogger(__name__)

import queue
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
    messages : queue.Queue[str]
        FIFO thread-safe des messages reçus, alimentée par `receive_message`
        et consommée par `CommunicationManager.read_from_server`. Chaque entrée
        correspond à un chunk `recv()` (donc potentiellement plusieurs messages
        concaténés si l'expéditeur n'a pas espacé ses envois).
    sock : socket.socket
        The socket object used for communication.
    read_thread : threading.Thread
        The thread responsible for reading messages from the server.
    """

    def __init__(self, host: str, port: int, who: str | None = None) -> None:
        """
        Initializes the CommunicationSocket instance.
        Args:
            host (str): The hostname or IP address of the server to connect to.
            port (int): The port number of the server to connect to.
            who (str | None): Robot identifier sent during the handshake.
                If provided, the socket announces itself as ``robot#<who>`` so the
                RabbitControlCenter can track which robot is connected.
        """

        self.host = host
        self.port = port
        self.who = who
        self.messages: "queue.Queue[str]" = queue.Queue()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to {self.host} on port {self.port}")
            handshake = f"robot#{who}" if who else "robot"
            self.send_message(handshake)
        except socket.error as e:
            logger.error(f"Failed to connect to {self.host} on port {self.port}: {e}")
        self.read_thread = threading.Thread(target=self.receive_message)
        self.read_thread.daemon = True
        self.read_thread.start()

    def receive_message(self) -> None:
        """
        Boucle de lecture du socket : empile chaque message non vide dans
        `self.messages` pour consommation par le thread principal via
        `CommunicationManager.read_from_server`.

        Le précédent attribut `last_message` était écrasé à chaque trame sans
        être consommé, ce qui provoquait un re-traitement en boucle côté
        master_loop tant que le robot recevait des messages.
        """

        while True:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                logger.info(f"Received message: {message}")
                if len(message) > 0:
                    self.messages.put(message)
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