import logging
import logging.handlers
logger = logging.getLogger(__name__)

class LogSocket:
    def __init__(self, url, port, who):
        self.socket_handler = logging.handlers.SocketHandler('localhost', 1664)
        formatter = logging.Formatter(f"%(asctime)s - {who} - %(name)s - %(levelname)s - %(message)s")
        self.socket_handler.setFormatter(formatter)
        logger.info(f"Creating LogSocket object with url {url} and port {port}.")

    def get(self):
        return self.socket_handler