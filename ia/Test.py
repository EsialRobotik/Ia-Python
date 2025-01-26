import argparse
import json

from tests.TestChrono import TestChrono
from tests.TestPullCord import TestPullCord
from tests.TestColorSelector import TestColorSelector

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("mode", type=str, help="System to check from :  chrono, pullcord, color")
    parser.add_argument("year", type=int, help="Year in integer format")
    args = parser.parse_args()

    print(f"Run {args.mode} for year {args.year}")
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
        