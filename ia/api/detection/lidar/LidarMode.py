from enum import Enum

class LidarMode(Enum):
    """
    Enum representing the operating modes for the Lidar.

    Attributes:
        STANDARD (str): Standard operating mode.
        CLUSTERING (str): Clustering mode.
        CLUSTERING_ONE_LINE (str): Clustering mode with one line.
    """
    STANDARD = 'f'
    CLUSTERING = 'c'
    CLUSTERING_ONE_LINE = 'o'