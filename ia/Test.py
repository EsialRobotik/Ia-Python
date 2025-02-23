import logging.handlers
import sys

from ia.tests import TestPathfinding

logger = logging.getLogger(__name__)

import argparse
import json

from tests.TestChrono import TestChrono
from tests.TestPullCord import TestPullCord
from tests.TestColorSelector import TestColorSelector
from tests.TestNextion import TestNextion
from tests.TestLogSocket import TestLogSocket
from tests.TestCommunicationSocket import TestCommunicationSocket
from tests.TestAX12 import TestAX12
from tests.TestSrf04 import TestSrf04
from tests.TestLidar import TestLidar
from tests.TestAsserv import TestAsserv
from tests.TestActions import TestActions

if __name__ == "__main__":
    # manage arguments
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("mode", type=str, help="System to check from :  chrono, pullcord, color, nection, log_socket, com_socket")
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
    logger.info("init logger")

    # run the test
    logger.info(f"Run {args.mode} for year {args.year}")
    with open(f'config/{args.year}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        match args.mode:
            case 'chrono':
                TestChrono(config_data).test()
            case 'pullcord':
                TestPullCord(config_data).test()
            case 'color':
                TestColorSelector(config_data).test()
            case 'nextion':
                TestNextion(config_data).test()
            case 'log_socket':
                TestLogSocket(config_data).test()
            case 'com_socket':
                TestCommunicationSocket(config_data).test()
            case 'ax12':
                TestAX12(config_data).test()
            case 'srf04':
                TestSrf04(config_data).test()
            case 'lidar':
                TestLidar(config_data).test()
            case 'asserv':
                TestAsserv(config_data).test()
            case 'actions':
                TestActions(config_data).test()
            case 'pathfinding':
                TestPathfinding(config_data).test()
        