import logging
logger = logging.getLogger(__name__)

from tests.AbstractTest import AbstractTest
from api.LogSocket import LogSocket

class TestLogSocket(AbstractTest):
    def test(self):
        # create a socket handler
        socket_handler = LogSocket(
            url=self.config_data['loggerSocket']['host'],
            port=self.config_data['loggerSocket']['port'],
            who=self.config_data['loggerSocket']['who']
        ).get()
        logging.getLogger('').addHandler(socket_handler)
        logger.info("log socket Test 1")
        logger.debug("log socket Test 2")
        logger.warning("log socket Test 3")
        logger.error("log socket Test 4")