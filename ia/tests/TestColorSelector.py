from api.ColorSelector import ColorSelector
from tests.AbstractTest import AbstractTest
from time import sleep

class TestColorSelector(AbstractTest):
    """
    TestColorSelector is a test class that inherits from AbstractTest. It is used to test the functionality of the ColorSelector class.
    Methods
    -------
    test():
        Continuously checks and prints the status of color detection using the ColorSelector instance.
    """

    def test(self):
        """
        Tests the color detection functionality.
        This method initializes a ColorSelector object with the GPIO pin specified in the configuration data.
        It then enters an infinite loop, printing the result of the color detection every 0.5 seconds.
        """

        colorSelector = ColorSelector(self.config_data['gpioColorSelector'])
        while(True):
            print(f"Color 0 : {colorSelector.is_color_0()}")
            sleep(0.5)