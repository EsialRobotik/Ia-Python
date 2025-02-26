from abc import ABC, abstractmethod
from typing import Optional

class AbstractAction(ABC):
    """
    Abstract class for executing and controlling robot actions.
    """

    @abstractmethod
    def execute(self) -> None:
        """
        Start the action execution. Should be non-blocking.
        Should not start again a finished action until reset() has been invoked
        """
        pass

    @abstractmethod
    def finished(self) -> bool:
        """
        Return true if the action has been executed and is done
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Should immediately stop the action
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the action so it can be re-executed whit execute()
        """
        pass

    @abstractmethod
    def get_flag(self) -> Optional[str]:
        """
        Return potential existing flag of the action to help AI in its decision process
        """
        pass