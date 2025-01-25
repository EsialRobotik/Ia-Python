import time

from api.Chrono import Chrono
from tests.AbstractTest import AbstractTest

class TestChrono(AbstractTest):
    def test(self):
        match_duration = self.config_data['matchDuration']
        print(f"Match duration: {self.config_data['matchDuration']} seconds")
        # Create a chrono
        chrono = Chrono(match_duration=match_duration)
        chrono.start()
        # Print the remaining time
        print(f"Time since begining : {chrono.get_time_since_beginning()}")
        print(chrono)
        # Simulate 30 seconds of match time
        time.sleep(5)
        # Print the remaining time again
        print(f"Time since begining : {chrono.get_time_since_beginning()}")
        print(chrono)