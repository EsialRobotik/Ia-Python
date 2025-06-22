import logging

from ia.api.detection.lidar.lidar_coordinate import LidarCoordinate
from ia.api.detection.lidar.lidar_mode import LidarMode
from ia.asservissement import asserv
from ia.asservissement.asserv import Asserv
from ia.utils.position import Position

logger = logging.getLogger(__name__)

import serial
import math
import threading
from typing import List, Tuple

class LidarRpA2:
    """
    Lidar class for managing communication and data processing from a Lidar sensor.

    Attributes:
        lidar_serial (serial.Serial): The serial connection to the Lidar sensor.
        detected_points (List[Tuple[int, int]]): List of points detected by the Lidar.
        asserv (asserv): Instance of the Asserv class to get the current position.

    Methods:
        __init__(serial_port: str, baud_rate: int, quality: int, distance: int, period: int, asservissement: Asserv) -> None:
            Initializes the Lidar object with connection and configuration parameters.

        init(quality: int, distance: int, period: int) -> None:
            Initializes the Lidar with quality, distance, and period parameters.

        parse_lidar_measures() -> None:
            Continuously reads and parses Lidar measurements.

        start_scan() -> None:
            Starts the Lidar scan.

        stop_scan() -> None:
            Stops the Lidar scan.

        set_mode(mode: LidarMode) -> None:
            Sets the operating mode of the Lidar.

        set_period(period: int) -> None:
            Sets the measurement period of the Lidar.

        start_motor() -> None:
            Starts the Lidar motor.

        stop_motor() -> None:
            Stops the Lidar motor.

        ask_lidar_info() -> None:
            Requests information from the Lidar.

        reset() -> None:
            Resets the Lidar.

        get_quality() -> None:
            Gets the current quality of the Lidar.

        set_quality(value: int) -> None:
            Sets the quality of the Lidar.

        get_distance() -> None:
            Gets the current distance of the Lidar.

        set_distance(value: int) -> None:
            Sets the distance of the Lidar.

        get_health() -> None:
            Gets the health status of the Lidar.

        get_coordinate_mode() -> None:
            Gets the current coordinate mode of the Lidar.

        set_coordinate_mode(coordinate_mode: LidarCoordinate) -> None:
            Sets the coordinate mode of the Lidar.

        get_detected_points() -> List[Tuple[int, int]]:
            Returns the list of points detected by the Lidar.
    """
    def __init__(self, serial_port: str, baud_rate: int, quality: int, distance: int, period: int, asserv: Asserv) -> None:
        """
        Initializes the Lidar object with connection and configuration parameters.

        Args:
            serial_port (str): The serial port to which the Lidar is connected.
            baud_rate (int): The baud rate for the serial communication.
            quality (int): The quality parameter for the Lidar.
            distance (int): The distance parameter for the Lidar.
            period (int): The period parameter for the Lidar.
            asserv (asserv): An instance of the Asserv class to get the current position.
        """

        logger.info(f"Init Lidar on port {serial_port} with baud rate {baud_rate}")
        self.lidar_serial = serial.Serial(
            port=serial_port, 
            baudrate=baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        self.detected_points = []
        self.asserv = asserv
        self.read_thread = threading.Thread(target=self.parse_lidar_measures)
        self.read_thread.daemon = True
        self.read_thread.start()
        self.init(quality=quality, distance=distance, period=period)

    def init(self, quality: int, distance: int, period: int) -> None:
        """
        Initializes the Lidar with quality, distance, and period parameters.

        Args:
            quality (int): The quality parameter for the Lidar.
            distance (int): The distance parameter for the Lidar.
            period (int): The period parameter for the Lidar.
        """

        self.reset()
        self.set_coordinate_mode(LidarCoordinate.POLAR_RADIANS)
        self.set_mode(LidarMode.CLUSTERING_ONE_LINE)
        self.set_quality(quality)
        self.set_distance(distance)
        self.set_period(period)
        self.start_scan()

    def parse_lidar_measures(self) -> None:
        """
        Continuously reads and parses Lidar measurements.

        This method runs an infinite loop that reads data from the Lidar's serial port.
        It decodes the data from ASCII, strips any leading/trailing whitespace, and
        splits the data into individual points. Each point is then parsed into x and y
        coordinates, which are transformed relative to the current position and orientation
        of the robot. The transformed coordinates are stored in the `detected_points` list.

        Note:
            This method will block indefinitely. Ensure that it is run in a separate
            thread or process if you need your program to perform other tasks concurrently.
        """

        while True:
            serial_buffer = self.lidar_serial.readline().decode('ascii').strip()
            self.detected_points.clear()
            logger.debug(f"Lidar buffer: {serial_buffer}")
            if len(serial_buffer) == 0:
                continue
            points = serial_buffer.split('#')
            for point in points:
                coordinates = point.split(';')
                if len(coordinates) == 2:
                    try:
                        angle = float(coordinates[0])
                        distance = float(coordinates[1])

                        # Position relative au robot
                        x_obstacle_relative_to_robot = distance * math.cos(angle)
                        y_obstacle_relative_to_robot = distance * math.sin(angle)

                        robot_position = self.asserv.position

                        # Changement de repère (robot -> table)
                        x_obstacle_relative_to_table = int(
                            robot_position.x +
                            x_obstacle_relative_to_robot * math.cos(robot_position.theta) -
                            y_obstacle_relative_to_robot * math.sin(robot_position.theta)
                        )
                        y_obstacle_relative_to_table = int(
                            robot_position.y +
                            x_obstacle_relative_to_robot * math.sin(robot_position.theta) +
                            y_obstacle_relative_to_robot * math.cos(robot_position.theta)
                        )

                        detected_point = Position(round(x_obstacle_relative_to_table), round(y_obstacle_relative_to_table))
                        logger.debug(f"Lidar detection: {detected_point}")
                        self.detected_points.append(detected_point)
                    except ValueError:
                        logger.error(f"Parsing error: {point}")
                else:
                    logger.error(f"Parsing error: {point}")

    def start_scan(self) -> None:
        """
        Starts the Lidar scan.
        """

        logger.info("Start lidar scan")
        self.lidar_serial.write(b's')

    def stop_scan(self) -> None:
        """
        Stops the Lidar scan.
        """

        logger.info("Stop lidar scan")
        self.lidar_serial.write(b'h')

    def set_mode(self, mode: LidarMode) -> None:
        """
        Sets the operating mode of the Lidar.

        Args:
            mode (lidar_mode): The mode to set for the Lidar.
        """

        logger.info(f"Set lidar mode to m{mode.value}")
        self.lidar_serial.write(f'm{mode.value}'.encode())

    def set_period(self, period: int) -> None:
        """
        Sets the measurement period of the Lidar.

        Args:
            period (int): The period to set for the Lidar.
        """
        logger.info(f"Set lidar period to p{period}")
        self.lidar_serial.write(f'p{period}'.encode())

    def start_motor(self) -> None:
        """
        Starts the Lidar motor.
        """
        logger.info("Start lidar motor")
        self.lidar_serial.write(b'r1')

    def stop_motor(self) -> None:
        """
        Stops the Lidar motor.
        """
        logger.info("Stop lidar motor")
        self.lidar_serial.write(b'r0')

    def ask_lidar_info(self) -> None:
        """
        Requests information from the Lidar.
        """
        logger.info("Ask lidar info")
        self.lidar_serial.write(b'i')

    def reset(self) -> None:
        """
        Resets the Lidar.
        """
        logger.info("Reset lidar")
        self.lidar_serial.write(b'e')

    def get_quality(self) -> None:
        """
        Gets the current quality of the Lidar.
        """
        logger.info("Get lidar quality")
        self.lidar_serial.write(b'q')

    def set_quality(self, value: int) -> None:
        """
        Sets the quality of the Lidar.

        Args:
            value (int): The quality value to set for the Lidar.
        """
        logger.info(f"Set lidar quality to q{value}")
        self.lidar_serial.write(f'q{value}'.encode())

    def get_distance(self) -> None:
        """
        Gets the current distance of the Lidar.
        """
        logger.info("Get lidar distance")
        self.lidar_serial.write(b'd')

    def set_distance(self, value: int) -> None:
        """
        Sets the distance of the Lidar.

        Args:
            value (int): The distance value to set for the Lidar.
        """
        logger.info(f"Set lidar distance to d{value}")
        self.lidar_serial.write(f'd{value}'.encode())

    def get_health(self) -> None:
        """
        Gets the health status of the Lidar.
        """
        logger.info("Get lidar health")
        self.lidar_serial.write(b'l')

    def get_coordinate_mode(self) -> None:
        """
        Gets the current coordinate mode of the Lidar.
        """
        logger.info("Get lidar coordinate mode")
        self.lidar_serial.write(b'f')

    def set_coordinate_mode(self, coordinate_mode: LidarCoordinate) -> None:
        """
        Sets the coordinate mode of the Lidar.

        Args:
            coordinate_mode (lidar_coordinate): The coordinate mode to set for the Lidar.
        """
        logger.info(f"Set lidar coordinate mode to f{coordinate_mode.value}")
        self.lidar_serial.write(f'f{coordinate_mode.value}'.encode())