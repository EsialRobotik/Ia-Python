import logging
logger = logging.getLogger(__name__)

import serial
import math
import threading
from enum import Enum
from typing import List, Tuple
from asserv.Asserv import Asserv
from detection.lidar.LidarCoordinate import LidarCoordinate
from detection.lidar.LidarMode import LidarMode

class Lidar:
    def __init__(self, serial_port: str, baud_rate: int, quality: int, distance: int, period: int, asserv: Asserv):
        logger.info(f"Init Lidar on port {serial_port} with baud rate {baud_rate}")
        self.lidar_serial = serial.Serial(serial_port, baud_rate)
        self.detected_points = []
        self.asserv = asserv
        self.init(quality=quality, distance=distance, period=period)
        self.read_thread = threading.Thread(target=self.parse_lidar_measures)
        self.read_thread.daemon = True
        self.read_thread.start()

    def init(self, quality: int, distance: int, period: int):
        self.reset()
        self.set_coordinate_mode(LidarCoordinate.CARTESIAN)
        self.set_mode(LidarMode.CLUSTERING_ONE_LINE)
        self.set_quality(quality)
        self.set_distance(distance)
        self.set_period(period)
        self.start_scan()

    def parse_lidar_measures(self):
        self.detected_points.clear()
        serial_buffer = self.lidar_serial.readline().decode('ascii').strip()
        logger.debug(f"Lidar buffer: {serial_buffer}")
        points = serial_buffer.split('#')
        for point in points:
            coordinates = point.split(';')
            if len(coordinates) == 2:
                try:
                    x = float(coordinates[0])
                    y = float(coordinates[1])
                    relative_x = x - self.asserv.get_position().x
                    relative_y = y - self.asserv.get_position().y
                    angle = self.asserv.get_position().theta
                    rotated_x = relative_x * math.cos(angle) + relative_y * math.sin(angle)
                    rotated_y = -relative_x * math.sin(angle) + relative_y * math.cos(angle)
                    logger.debug(f"Lidar detection: {self.asserv.get_position()}")
                    self.detected_points.append((round(rotated_x), round(rotated_y)))
                except ValueError:
                    logger.error(f"Parsing error: {point}")
            else:
                logger.error(f"Parsing error: {point}")

    def start_scan(self):
        self.lidar_serial.write(b's')

    def stop_scan(self):
        self.lidar_serial.write(b'h')

    def set_mode(self, mode: LidarMode):
        self.lidar_serial.write(mode.value.encode())

    def set_period(self, period: int):
        self.lidar_serial.write(f'p{period}'.encode())

    def start_motor(self):
        self.lidar_serial.write(b'r1')

    def stop_motor(self):
        self.lidar_serial.write(b'r0')

    def ask_lidar_info(self):
        self.lidar_serial.write(b'i')

    def reset(self):
        self.lidar_serial.write(b'e')

    def get_quality(self):
        self.lidar_serial.write(b'q')

    def set_quality(self, value: int):
        self.lidar_serial.write(f'q{value}'.encode())

    def get_distance(self):
        self.lidar_serial.write(b'd')

    def set_distance(self, value: int):
        self.lidar_serial.write(f'd{value}'.encode())

    def get_health(self):
        self.lidar_serial.write(b'l')

    def get_coordinate_mode(self):
        self.lidar_serial.write(b'f')

    def set_coordinate_mode(self, coordinate_mode: LidarCoordinate):
        self.lidar_serial.write(coordinate_mode.value.encode())

    def get_detected_points(self) -> List[Tuple[int, int]]:
        return self.detected_points