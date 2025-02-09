import logging
import time

from tests.AbstractTest import AbstractTest
from asserv.Asserv import Asserv

class TestAsserv(AbstractTest):
    def test(self):
        logger = logging.getLogger(__name__)
        asserv = Asserv(
            serialPort=self.config_data['asserv']['serialPort'],
            baudRate=self.config_data['asserv']['baudRate'],
            gostart_config={}
        )
        while True:
            time.sleep(0.2)
            logger.info(f"Asserv status : {asserv.asserv_status}")
            logger.info(f"Asserv position : {asserv.position}")