import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import json
from tests.TestChrono import TestChrono

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a mode and a year.")
    parser.add_argument("mode", type=str, help="System to check")
    parser.add_argument("year", type=int, help="Year in integer format")
    args = parser.parse_args()

    print(f"The provided year is: {args.year}")
    with open(f'config/{args.year}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        if args.mode == 'chrono':
            TestChrono(config_data).test()
        