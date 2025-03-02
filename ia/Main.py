import argparse
import json
import logging.handlers
import sys
import time

from ia import MasterLoop
from ia.actions import ActionRepositoryFactory
from ia.api import Chrono, PullCord, NextionNX32224T024
from ia.api.ax12 import AX12LinkSerial
from ia.api.detection.lidar import Lidar
from ia.api.detection.ultrasound import SrfFactory
from ia.asserv import Asserv
from ia.manager import ActionManager, DetectionManager, MovementManager, StrategyManager

if __name__ == "__main__":
    # manage arguments
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    parser.add_argument("log_level", type=str, help="Set log level among : CRITICAL, FATAL, ERROR, WARN, INFO, DEBUG")
    args = parser.parse_args()

    # set logger level
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()[args.log_level.upper()])
    # create file handler which logs even debug messages
    file_handler = logging.handlers.RotatingFileHandler(filename='logs/log.log', backupCount=50)
    file_handler.doRollover()
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

    # run the test
    logger.info(f"Lancement IA {args.year}")
    with open(f'config/{args.year}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()

        # Init divers
        comm_config=config_data["comSocket"]
        table_config=config_data["table"]
        logger.info("Init asserv")
        asserv = Asserv(
            serial_port=config_data["asserv"]["serialPort"],
            baud_rate=config_data["asserv"]["baudRate"],
            gostart_config=config_data["asserv"]["goStart"],
        )
        logger.info("Init asserv OK")

        # Init action manager
        logger.info("Init action manager")
        ax12_link = AX12LinkSerial(
            serial_port=config_data["action"]["ax12"]["serialPort"],
            baud_rate=config_data["action"]["ax12"]["baudRate"]
        )
        action_repository = ActionRepositoryFactory.from_json_files(
            folder=config_data['actions']['dataDir'],
            ax12_link_serial=ax12_link
        )
        action_manager = ActionManager(
            action_repository=action_repository,
            ax12_link=ax12_link,
            actions_config=config_data["actions"],
        )
        logger.info("Init action manager OK")

        # Init detection manager
        logger.info("Init detection manager")
        lidar = Lidar(
            serial_port=config_data["detection"]["lidar"]["serialPort"],
            baud_rate=config_data["detection"]["lidar"]["baudRate"],
            quality=config_data["detection"]["lidar"]["quality"],
            distance=config_data["detection"]["lidar"]["distance"],
            period=config_data["detection"]["lidar"]["period"],
            asserv=asserv
        )
        ultrasound_config = config_data["detection"]["ultrasound"]
        srf = []
        for srf in ultrasound_config['gpioList']:
            srf.append(SrfFactory.build_srf(
                srf_config=srf,
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
        strategy_manager = StrategyManager(year=args.year)
        logger.info("Init strategy manager OK")

        # Init chrono
        logger.info("Init chrono")
        chrono = Chrono(config_data)
        logger.info("Init chrono OK")

        # Init pull cord
        logger.info("Init pull cord")
        pull_cord = PullCord(config_data['gpioPullCord'])
        logger.info("Init pull cord OK")

        # Init nextion
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
            nextion_display=nextion_display
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