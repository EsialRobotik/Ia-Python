import logging
import time

from ia.asservissement.asserv import Asserv
from ia.tests.abstract_test import AbstractTest


class TestAsserv(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        asserv = Asserv(
            serial_port=self.config_data['asserv']['serialPort'],
            baud_rate=self.config_data['asserv']['baudRate'],
            gostart_config={}
        )
        time.sleep(0.2)
        logger.info(f"Asserv status : {asserv.asserv_status}")
        logger.info(f"Asserv position : {asserv.position}")
        asserv.go(100)
        asserv.wait_for_asserv()
        time.sleep(0.2)
        logger.info(f"Asserv status : {asserv.asserv_status}")
        logger.info(f"Asserv position : {asserv.position}")
        asserv.go(-100)
        asserv.wait_for_asserv()
        time.sleep(0.2)
        logger.info(f"Asserv status : {asserv.asserv_status}")
        logger.info(f"Asserv position : {asserv.position}")