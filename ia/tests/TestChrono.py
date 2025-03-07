import logging
import time

from ia.api import Chrono
from ia.tests import AbstractTest


class TestChrono(AbstractTest):
    """
    TestChrono is a test class that inherits from AbstractTest. It is used to test the functionality of the Chrono class.
    Methods
    -------
    test():
        Executes the test by creating a Chrono instance, starting it, and printing the elapsed time at different intervals.
    """


    def test(self) -> None:
        """
        Test the Chrono class functionality.
        This method performs the following steps:
        1. Retrieves the match duration from the configuration data.
        2. Prints the match duration.
        3. Creates a Chrono instance with the match duration.
        4. Starts the Chrono.
        5. Prints the time since the beginning of the match.
        6. Simulates 5 seconds of match time.
        7. Prints the time since the beginning of the match again.
        Attributes:
            config_data (dict): Configuration data containing 'matchDuration'.
        Returns:
            None
        """
        logger = logging.getLogger(__name__)
        match_duration = self.config_data['matchDuration']
        logger.info(f"Match duration: {self.config_data['matchDuration']} seconds")
        # Create a chrono
        chrono = Chrono(match_duration=match_duration)
        chrono.start()
        # Print the remaining time
        logger.info(f"Time since begining : {chrono.get_time_since_beginning()}")
        logger.info(chrono)
        # Simulate 30 seconds of match time
        time.sleep(5)
        # Print the remaining time again
        logger.info(f"Time since begining : {chrono.get_time_since_beginning()}")
        logger.info(chrono)