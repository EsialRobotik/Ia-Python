import argparse
import json
import logging.handlers
import sys

from ia.tests import TestPathfinding
from ia.tests.TestStrategyManager import TestStrategyManager
from tests.TestAX12 import TestAX12
from tests.TestActions import TestActions
from tests.TestAsserv import TestAsserv
from tests.TestChrono import TestChrono
from tests.TestColorSelector import TestColorSelector
from tests.TestCommunicationSocket import TestCommunicationSocket
from tests.TestLidar import TestLidar
from tests.TestLogSocket import TestLogSocket
from tests.TestNextion import TestNextion
from tests.TestPullCord import TestPullCord
from tests.TestSrf04 import TestSrf04

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
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    # run the test
    logger.info(f"Run {args.mode} for year {args.year}")
    with open(f'config/{args.year}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        match args.mode:
            case 'chrono':
                TestChrono(config_data, args.year).test()
            case 'pullcord':
                TestPullCord(config_data, args.year).test()
            case 'color':
                TestColorSelector(config_data, args.year).test()
            case 'nextion':
                TestNextion(config_data, args.year).test()
            case 'log_socket':
                TestLogSocket(config_data, args.year).test()
            case 'com_socket':
                TestCommunicationSocket(config_data, args.year).test()
            case 'ax12':
                TestAX12(config_data, args.year).test()
            case 'srf04':
                TestSrf04(config_data, args.year).test()
            case 'lidar':
                TestLidar(config_data, args.year).test()
            case 'asserv':
                TestAsserv(config_data, args.year).test()
            case 'actions':
                TestActions(config_data, args.year).test()
            case 'pathfinding':
                TestPathfinding(config_data, args.year).test()
            case 'strategy':
                TestStrategyManager(config_data, args.year).test()
            case default:
                raise logger.error(f"Mode {args.mode} does not exist")