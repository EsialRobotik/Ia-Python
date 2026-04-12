import argparse
import logging.handlers
import sys
import time

from ia.actions.action_repository_factory import ActionRepositoryFactory
from ia.actions.serial_port import SerialPort
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.api.ax12.ax12_servo import AX12Servo
from ia.api.ax12.enums.ax12_address import AX12Address
from ia.api.chrono import Chrono
from ia.api.color_selector import ColorSelector
from ia.api.detection.lidar.lidar_rpa2 import LidarRpA2
from ia.api.detection.ultrasound.srf_factory import SrfFactory
from ia.api.log_socket import LogSocket
from ia.api.nextion_nx32224t024 import NextionNX32224T024
from ia.api.pull_cord import PullCord
from ia.asservissement.asserv import Asserv
from ia.manager.action_manager import ActionManager
from ia.manager.detection_manager import DetectionManager
from ia.manager.movement_manager import MovementManager
from ia.manager.strategy_manager import StrategyManager
from ia.master_loop import MasterLoop
from ia.utils.config_loader import load_config
from ia.utils.robot import Robot
from ia.utils.robot_filter import RobotFilter

if __name__ == "__main__":
    # manage arguments
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    parser.add_argument("robot", type=str, help="Robot type from Robot enum")
    parser.add_argument("log_level", type=str, help="Set log level among : CRITICAL, FATAL, ERROR, WARN, INFO, DEBUG")
    args = parser.parse_args()

    # set logger level
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()[args.log_level.upper()])

    # create file handler which logs even debug messages
    file_handler = logging.handlers.RotatingFileHandler(filename='logs/log.log', backupCount=50)
    file_handler.doRollover()

    # create stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)
    # add the handlers to the logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(stdout_handler)

    logger = logging.getLogger(__name__)
    logger.info("Init logger")

    # run
    robot = Robot(args.robot)
    logger.info(f"Lancement IA {args.year} pour {robot.value}")
    config_data = load_config(args.year, robot.value)

    # Init socket logger handler
    if config_data['loggerSocket']['active']:
        socket_handler = LogSocket(
            host=config_data['loggerSocket']['host']
        ).get()
        socket_handler.addFilter(RobotFilter(config_data['loggerSocket']['who']))
        logging.getLogger().addHandler(socket_handler)

    # Init divers
    comm_config=config_data["comSocket"]
    table_config=config_data["table"]
    logger.info("Init asservissement")
    asserv = Asserv(
        serial_port=config_data["asserv"]["serialPort"],
        baud_rate=config_data["asserv"]["baudRate"],
        gostart_config=config_data["asserv"]["goStart"],
    )
    logger.info("Init asservissement OK")

    # Init action manager
    logger.info("Init action manager")
    ax12_link = None
    serial_ports = {}
    stop_hooks = []
    if config_data['actions'].get('ax12') is not None:
        ax12_link = AX12LinkSerial(
            serial_port=config_data["actions"]["ax12"]["serialPort"],
            baud_rate=config_data["actions"]["ax12"]["baudRate"]
        )
        def make_ax12_stop_hook(link):
            def hook():
                link.enable_dtr(False)
                link.enable_rts(False)
                ax = AX12Servo(AX12Address.AX12_ADDRESS_BROADCAST.value, link)
                ax.disable_torque()
                link.serial.close()
            return hook
        stop_hooks.append(make_ax12_stop_hook(ax12_link))
    if config_data['actions'].get('actuators') is not None:
        for actuator_config in config_data['actions']['actuators']:
            if actuator_config['type'] == 'serial':
                port_id = actuator_config.get('id', str(len(serial_ports)))
                serial_ports[port_id] = SerialPort(actuator_config['serialPort'], actuator_config['baudRate'])
    action_repository = ActionRepositoryFactory.from_json_files(
        folder=config_data['actions']['dataDir'],
        ax12_link_serial=ax12_link,
        serial_ports=serial_ports
    )
    action_manager = ActionManager(
        action_repository=action_repository,
        actions_config=config_data["actions"],
        stop_hooks=stop_hooks,
    )
    logger.info("Init action manager OK")

    # Init detection manager
    logger.info("Init detection manager")
    lidar = None
    if config_data["detection"].get("lidar") is not None:
        lidar = LidarRpA2(
            serial_port=config_data["detection"]["lidar"]["serialPort"],
            baud_rate=config_data["detection"]["lidar"]["baudRate"],
            quality=config_data["detection"]["lidar"]["quality"],
            distance=config_data["detection"]["lidar"]["distance"],
            period=config_data["detection"]["lidar"]["period"],
            asserv=asserv
        )
    ultrasound_config = config_data["detection"]["ultrasound"]
    srf = []
    for srfConfig in ultrasound_config['gpioList']:
        srf.append(SrfFactory.build_srf(
            srf_config=srfConfig,
            window_size=ultrasound_config["windowSize"]
        ))
    detection_manager = DetectionManager(
        sensors=srf,
        lidar=lidar,
        asserv=asserv,
        table_config=table_config,
    )
    logger.info("Init detection manager OK")

    # Init movement manager
    logger.info("Init movement manager")
    movement_manager = MovementManager(asserv=asserv)
    logger.info("Init movement manager OK")

    # Init strategy manager
    logger.info("Init strategy manager")
    strategy_manager = StrategyManager(year=args.year, robot=robot)
    logger.info("Init strategy manager OK")

    # Init chrono
    logger.info("Init chrono")
    chrono = Chrono(config_data['matchDuration'])
    logger.info("Init chrono OK")

    # Init pull cord
    logger.info("Init pull cord")
    pull_cord = PullCord(config_data['gpioPullCord'])
    logger.info("Init pull cord OK")

    # Init color selector
    color_selector = None
    if config_data.get('gpioPullCord') is not None:
        color_selector = ColorSelector(config_data.get('gpioColorSelector'))

    # Init nextion
    nextion_display = None
    if config_data.get('nextion') is not None:
        logger.info("Init nextion")
        nextion_display = NextionNX32224T024(
            serial_port=config_data['nextion']['serialPort'],
            baud_rate=config_data['nextion']['baudRate'],
            color0=config_data['table']['color0']
        )
        logger.info("Init nextion OK")

    # Init master loop
    logger.info("Init master loop")
    master_loop = MasterLoop(
        action_manager=action_manager,
        comm_config=comm_config,
        detection_manager=detection_manager,
        movement_manager=movement_manager,
        strategy_manager=strategy_manager,
        table_config=table_config,
        chrono=chrono,
        pull_cord=pull_cord,
        nextion_display=nextion_display,
        color_selector=color_selector
    )

    # Start execution
    logger.info("Init the MasterLoop")
    master_loop.init()
    logger.info("Start the MasterLoop")
    master_loop.main_loop()

    # When master loop is finished, we wait for the end of the match
    while True:
        time.sleep(1)
        if master_loop.interrupted:
            break

    # wait a little more, just in case
    time.sleep(5)
    logger.info("End of the MasterLoop")