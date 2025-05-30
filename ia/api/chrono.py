import logging
import threading
from datetime import datetime


class Chrono:
    """
    A class used to represent a Chronometer for a match.
    Attributes
    ----------
    match_duration : int
        The duration of the match in seconds.
    timestamp_start : float
        The timestamp when the match started.
    timer : threading.Timer
        A timer object to handle the match duration.
    Methods
    -------
    __str__():
        Returns a string representation of the remaining match time and total match duration.
    start_match(master_loop):
        Starts the match timer and sets the start timestamp.
    get_time_since_beginning():
        Returns the time elapsed since the match started in seconds.
    """

    def __init__(self, match_duration: int) -> None:
        """
        Initializes a new instance of the Chrono class.
        Args:
            match_duration (int): The duration of the match in seconds.
        Attributes:
            match_duration (int): The duration of the match in seconds.
            timestamp_start (None or float): The start time of the match, initialized to None.
            timer (None or threading.Timer): The timer object, initialized to None.
        """

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Creating Chrono object with match duration of {match_duration} seconds.")
        self.match_duration = match_duration
        self.timestamp_start = None
        self.timer = None

    def __str__(self) -> str:
        """
        Returns a string representation of the remaining match duration.
        The method calculates the remaining time by subtracting the elapsed time 
        (in seconds) since the match started from the total match duration.
        Returns:
            str: A string in the format "remaining_time / match_duration".
        """

        current_time = int(datetime.now().timestamp())
        chrono = self.match_duration - (current_time - self.timestamp_start)
        return f"{chrono} / {self.match_duration}"

    def start_match(self, match_end: callable) -> None:
        """
        Starts the match timer and schedules the match end.
        This method records the current timestamp as the start time of the match
        and initializes a timer that will call the `match_end` method of the 
        `master_loop` object after the duration of the match has elapsed.
        Args:
            match_end (callable): A callback for the end of the match
        """

        self.start()
        self.timer = threading.Timer(self.match_duration, match_end)
        self.timer.start()

    def start(self) -> None:
        """
        Starts the match timer.
        This method records the current timestamp as the start time of the match.
        """

        self.logger.info("Starting match timer...")
        self.timestamp_start = int(datetime.now().timestamp())

    def get_time_since_beginning(self) -> int:
        """
        Calculate the time elapsed since the start timestamp in seconds.
        Returns:
            int: The time elapsed since the start timestamp in seconds.
        """

        current_time = int(datetime.now().timestamp())
        return current_time - self.timestamp_start
    
# Example usage:
# chrono = Chrono(match_duration=60)
# chrono.start_match(master_loop)   # Start the match timer
# print(chrono)                     # Print the remaining time
# time.sleep(30)                    # Simulate 30 seconds of match time
# print(chrono)                     # Print the remaining time again