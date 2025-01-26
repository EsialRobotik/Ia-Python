import logging
logger = logging.getLogger(__name__)

import argparse
import json

from tests.TestChrono import TestChrono
from tests.TestPullCord import TestPullCord
from tests.TestColorSelector import TestColorSelector
from tests.TestNextion import TestNextion

if __name__ == "__main__":
    # manage arguments
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("mode", type=str, help="System to check from :  chrono, pullcord, color")
    parser.add_argument("year", type=int, help="Year in integer format")
    parser.add_argument("log_level", type=str, help="Year in integer format")
    args = parser.parse_args()

    # set logger level
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()[args.log_level.upper()])
    # create file handler which logs even debug messages
    fh = logging.FileHandler('logs/log.log')
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logging.getLogger('').addHandler(fh)

    # run the test
    print(f"Run {args.mode} for year {args.year}")
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
        