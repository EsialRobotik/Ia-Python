import logging
import time

from ia.asservissement.asserv import Asserv
from ia.tests.abstract_test import AbstractTest


class TestCalage(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        logger.info("Init asserv")
        asserv = Asserv(
            serial_port=self.config_data['asserv']['serialPort'],
            baud_rate=self.config_data['asserv']['baudRate'],
            gostart_config={}
        )
        time.sleep(0.2)
        color = 'jaune'
        logger.info(f"go_start {color}")
        asserv.go_start(color)