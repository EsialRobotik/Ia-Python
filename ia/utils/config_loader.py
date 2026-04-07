import json
import os
from typing import Dict


def load_config(year: int, robot: str, config_base_path: str = "config") -> Dict:
    """Charge la config robot et fusionne la table partagée avec la marge spécifique au robot."""
    with open(os.path.join(config_base_path, str(year), robot, "config.json")) as f:
        config_data = json.load(f)

    with open(os.path.join(config_base_path, str(year), "table.json")) as f:
        table_data = json.load(f)

    table_data["marge"] = config_data["marge"]
    config_data["table"] = table_data

    return config_data