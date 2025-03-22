from enum import Enum

class LidarCoordinate(Enum):
    """
    Enum representing the coordinate modes for the Lidar.

    Attributes:
        CARTESIAN (str): Cartesian coordinate mode.
        POLAR_DEGREES (str): Polar coordinate mode in degrees.
        POLAR_RADIANS (str): Polar coordinate mode in radians.
    """
    CARTESIAN = 'c'
    POLAR_DEGREES = 'd'
    POLAR_RADIANS = 'r'