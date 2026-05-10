import logging
logger = logging.getLogger(__name__)

from gpiozero import Button

class ColorSelector:
    """
    A class used to represent a Color Button.
    Inherits from the Button class and adds functionality to detect a specific color state.
    Attributes
    ----------
    pin : int
        The pin number associated with the button.
    Methods
    -------
    isColor0():
        Checks if the button is not pressed, indicating the detection of color 0.
    """

    def __init__(self, pin: int) -> None:
        """
        Initialize the ColorDetector with the specified pin.
        Args:
            pin (int): The pin number to which the ColorDetector is connected.
        """

        logger.info(f"Creating ColorSelector object with pin {pin}.")
        self.button = Button(pin)
    
    def is_color_0(self) -> bool:
        """
        Check if the color sensor is not pressed.
        Returns:
            bool: True if the color sensor is not pressed, False otherwise.
        """

        return not self.button.is_pressed

    def on_change(self, callback) -> None:
        """
        Register a callback invoked whenever the switch state changes
        (rising edge AND falling edge). gpiozero calls the callback from a
        background thread, so the callback should be lightweight and
        thread-safe.
        """
        self.button.when_pressed = lambda *_: callback()
        self.button.when_released = lambda *_: callback()
    
# Example usage:
# color_button = ColorSelector(pin=17)
# print(color_button.is_color_0())