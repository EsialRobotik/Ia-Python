import logging
from time import sleep

from ia.api import PullCord
from ia.tests import AbstractTest


class TestPullCord(AbstractTest):
    """
    TestPullCord is a test class that inherits from AbstractTest. It is designed to test the functionality of a pull cord detector.
    Methods
    -------
    test():
        Continuously checks and prints the state of the pull cord detector at regular intervals.
    """

    def test(self) -> None:
        """
        Continuously prints the state of the pull cord at regular intervals.
        This method initializes a PullCord object using the GPIO pin
        specified in the configuration data. It then enters an infinite loop
        where it prints the current state of the pull cord every 0.5 seconds.
        Note:
            This method runs indefinitely and will need to be manually stopped.
        """
        logger = logging.getLogger(__name__)
        pullCord = PullCord(self.config_data['gpioPullCord'])
        while True:
            logger.info(f"Pull cord : {pullCord.get_state()}")
            sleep(0.5)