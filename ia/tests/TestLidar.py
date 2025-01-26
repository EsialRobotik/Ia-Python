from api.PullCord import PullCord
from tests.AbstractTest import AbstractTest
from time import sleep
from api.detection.lidar.Lidar import Lidar
from asserv.Asserv import Asserv

class TestLidar(AbstractTest):
    def test(self):
        lidar = Lidar(
            serial_port=self.config_data["detection"]["lidar"]["serialPort"], 
            baud_rate=self.config_data["detection"]["lidar"]["baudRate"], 
            quality=self.config_data["detection"]["lidar"]["quality"], 
            distance=self.config_data["detection"]["lidar"]["distance"], 
            period=self.config_data["detection"]["lidar"]["period"], 
            asserv=Asserv(
                serial_port=self.config_data["asserv"]["serialPort"], 
                baud_rate=self.config_data["asserv"]["baudRate"]
            )
        )
        while True:
            print(lidar.get_detected_points())
            sleep(1)