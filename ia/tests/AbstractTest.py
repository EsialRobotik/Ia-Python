from abc import ABC, abstractmethod

class AbstractTest(ABC):
    """
    AbstractTest is an abstract base class that defines the structure for test classes.
    Attributes:
        config_data (dict): Configuration data required for the test.
    Methods:
        test():
            Abstract method that should be implemented by subclasses to execute the test.
    """


    def __init__(self, config_data: dict) -> None:
        """
        Initializes the AbstractTest instance with the provided configuration data.
        Args:
            config_data (dict): A dictionary containing configuration data.
        """

        self.config_data = config_data

    @abstractmethod
    def test(self) -> None:
        """
        Executes the test.

        This method is intended to be overridden by subclasses to implement
        specific test logic.
        """
        pass