import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import json
import time

from api.Chrono import Chrono

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    args = parser.parse_args()

    print(f"The provided year is: {args.year}")
    with open(f'config/{args.year}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        print(f"Match duration: {config_data['matchDuration']} seconds")
        chrono = Chrono(match_duration=config_data['matchDuration'])
        chrono.start()
        print(f"Time since begining : {chrono.get_time_since_beginning()}") # Print the remaining time
        time.sleep(5) # Simulate 30 seconds of match time
        print(f"Time since begining : {chrono.get_time_since_beginning()}") # Print the remaining time again