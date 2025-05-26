import math
from abc import ABC, abstractmethod

from ia.utils.position import Position


class Srf(ABC):
    """
    Classe abstraite pour représenter un capteur SRF.
    """

    def __init__(self, desc: str, x: int, y: int, angle: int, threshold: int, window_size: int) -> None:
        """
        Initialise le capteur SRF avec les paramètres donnés.
        """
        self.desc = desc
        self.x = x
        self.y = y
        self.angle = angle
        self.threshold = threshold
        self.window_size = window_size

    def get_position(self) -> Position:
        """
        Returns the position of the sensor as a Position object.
        """

        return Position(x=self.x, y=self.y, theta=math.radians(self.angle))

    @abstractmethod
    def get_distance(self) -> int:
        """
        Return the average measured distance from the sensor in the window of size windows_size in millimeters.
        """
        pass