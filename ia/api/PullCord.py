from gpiozero import Button
from time import sleep

class PullCord:
    """
    A class to detect the state of a pull cord using a button.
    Attributes:
    -----------
    button : Button
        An instance of the Button class representing the pull cord button.
    Methods:
    --------
    __init__(pin):
        Initializes the PullCord with the specified pin.
    get_state():
        Returns the current state of the button (pressed or not pressed).
    wait_for_state(expected_state):
        Waits until the button state matches the expected state.
    """


    def __init__(self, pin):
        """
        Initializes the PullCord with the specified pin.
        Args:
            pin (int): The GPIO pin number to which the pull cord button is connected.
        """

        self.button = Button(pin)

    def get_state(self):
        """
        Get the current state of the button.
        Returns:
            bool: True if the button is pressed, False otherwise.
        """

        return self.button.is_pressed

    def wait_for_state(self, expected_state):
        """
        Waits until the state of the object matches the expected state.
        This method continuously checks the current state of the object by calling
        the `get_state` method and compares it to the `expected_state`. It pauses
        for 0.1 seconds between each check to avoid excessive CPU usage.
        Args:
            expected_state: The state that the object is expected to reach.
        """

        while self.get_state() != expected_state:
            sleep(0.1)

# Example usage:
# detector = PullCordDetector(pin=17)
# print(detector.getState())
# detector.waitForPullCord(expected_state=True)