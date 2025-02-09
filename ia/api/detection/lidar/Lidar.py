import logging
logger = logging.getLogger(__name__)

import serial
import math
import threading
from enum import Enum
from typing import List, Tuple
from asserv.Asserv import Asserv
from api.detection.lidar.LidarCoordinate import LidarCoordinate
from api.detection.lidar.LidarMode import LidarMode

class Lidar:
    def __init__(self, serial_port: str, baud_rate: int, quality: int, distance: int, period: int, asserv: Asserv):
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

    def init(self, quality: int, distance: int, period: int):
        self.reset()
        self.set_coordinate_mode(LidarCoordinate.CARTESIAN)
        self.set_mode(LidarMode.CLUSTERING_ONE_LINE)
        self.set_quality(quality)
        self.set_distance(distance)
        self.set_period(period)
        self.start_scan()

    def parse_lidar_measures(self):
        while True:
            serial_buffer = self.lidar_serial.readline().decode('ascii').strip()
            self.detected_points.clear()
            logger.debug(f"Lidar buffer: {serial_buffer}")
            if (len(serial_buffer) == 0):
                continue
            points = serial_buffer.split('#')
            for point in points:
                coordinates = point.split(';')
                if len(coordinates) == 2:
                    try:
                        x = float(coordinates[0])
                        y = float(coordinates[1])
                        relative_x = x - self.asserv.position.x
                        relative_y = y - self.asserv.position.y
                        angle = self.asserv.position.theta
                        rotated_x = relative_x * math.cos(angle) + relative_y * math.sin(angle)
                        rotated_y = -relative_x * math.sin(angle) + relative_y * math.cos(angle)
                        logger.debug(f"Lidar detection: {self.asserv.position}")
                        self.detected_points.append((round(rotated_x), round(rotated_y)))
                    except ValueError:
                        logger.error(f"Parsing error: {point}")
                else:
                    logger.error(f"Parsing error: {point}")

    def start_scan(self):
        logger.info("Start lidar scan")
        self.lidar_serial.write(b's')

    def stop_scan(self):
        logger.info("Stop lidar scan")
        self.lidar_serial.write(b'h')

    def set_mode(self, mode: LidarMode):
        logger.info(f"Set lidar mode to m{mode.value}")
        self.lidar_serial.write(f'm{mode.value}'.encode())

    def set_period(self, period: int):
        logger.info(f"Set lidar period to p{period}")
        self.lidar_serial.write(f'p{period}'.encode())

    def start_motor(self):
        logger.info("Start lidar motor")
        self.lidar_serial.write(b'r1')

    def stop_motor(self):
        logger.info("Stop lidar motor")
        self.lidar_serial.write(b'r0')

    def ask_lidar_info(self):
        logger.info("Ask lidar info")
        self.lidar_serial.write(b'i')

    def reset(self):
        logger.info("Reset lidar")
        self.lidar_serial.write(b'e')

    def get_quality(self):
        logger.info("Get lidar quality")
        self.lidar_serial.write(b'q')

    def set_quality(self, value: int):
        logger.info(f"Set lidar quality to q{value}")
        self.lidar_serial.write(f'q{value}'.encode())

    def get_distance(self):
        logger.info("Get lidar distance")
        self.lidar_serial.write(b'd')

    def set_distance(self, value: int):
        logger.info(f"Set lidar distance to d{value}")
        self.lidar_serial.write(f'd{value}'.encode())

    def get_health(self):
        logger.info("Get lidar health")
        self.lidar_serial.write(b'l')

    def get_coordinate_mode(self):
        logger.info("Get lidar coordinate mode")
        self.lidar_serial.write(b'f')

    def set_coordinate_mode(self, coordinate_mode: LidarCoordinate):
        logger.info(f"Set lidar coordinate mode to f{coordinate_mode.value}")
        self.lidar_serial.write(f'f{coordinate_mode.value}'.encode())

    def get_detected_points(self) -> List[Tuple[int, int]]:
        return self.detected_points