from enum import Enum

class LidarCoordinate(Enum):
    CARTESIAN = 'c'
    POLAR_DEGREES = 'd'
    POLAR_RADIANS = 'r'