from time import sleep

from ia.api import NextionNX32224T024
from ia.tests import AbstractTest


class TestNextion(AbstractTest):
    """
    TestNextion is a test class for interacting with a Nextion display.
    Methods
    -------
    test():
        Runs a sequence of commands to test the Nextion display, including 
        navigating through pages, waiting for calibration, displaying 
        calibration status messages, and updating the score.
    """

    def test(self) -> None:
        """
        Test method to interact with the Nextion display.
        This method performs the following actions:
        1. Initializes the Nextion display with the specified serial port, baud rate, and color.
        2. Navigates to the "init" page on the display.
        3. Waits for the display calibration to complete.
        4. Displays a series of calibration status messages with delays in between.
        5. Navigates to the "ready" page and then to the "score" page.
        6. Increments the score in a loop and updates the display with the new score.
        Attributes:
            nextion (NextionNX32224T024): Instance of the Nextion display class.
            score (int): Variable to keep track of the score.
        """

        nextion = NextionNX32224T024(
            serial_port=self.config_data['nextion']['serialPort'],
            baud_rate=self.config_data['nextion']['baudRate'],
            color0=self.config_data['table']['color0']
        )
        nextion.goto_page("init")
        nextion.wait_for_calibration()
        nextion.display_calibration_status("Coucou")
        sleep(0.5)
        nextion.display_calibration_status("La forme ?")
        sleep(0.5)
        nextion.display_calibration_status("Bien ou bien ?")
        sleep(0.5)
        nextion.display_calibration_status("Allez, qu'on en finisse")
        sleep(2)
        nextion.goto_page("ready")
        sleep(2)
        nextion.goto_page("score")
        score = 0
        for i in range(5):
            sleep(0.5)
            score += 3
            nextion.display_score(score)