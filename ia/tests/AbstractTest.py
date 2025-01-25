from abc import ABC, abstractmethod

class AbstractTest(ABC):
    def __init__(self, config_data):
        self.config_data = config_data

    @abstractmethod
    def test(self):
        # Execute test
        pass