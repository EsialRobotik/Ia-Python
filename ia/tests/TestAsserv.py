import logging
import time

from ia.asserv import Asserv
from ia.tests import AbstractTest


class TestAsserv(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        asserv = Asserv(
            serial_port=self.config_data['asserv']['serialPort'],
            baud_rate=self.config_data['asserv']['baudRate'],
            gostart_config={}
        )
        while True:
            time.sleep(0.2)
            logger.info(f"Asserv status : {asserv.asserv_status}")
            logger.info(f"Asserv position : {asserv.position}")