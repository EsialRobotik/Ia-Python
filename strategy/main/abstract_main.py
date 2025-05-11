import json
import os
import traceback
from typing import List

from ia.pathfinding.astar import AStar
from ia.utils.position import Position
from strategy.core.objective import Objective
from strategy.core.strat import Strat


class AbstractMain:

    def __init__(self):
        self.objectifs_couleur_0: List[Objective] = []
        self.objectifs_couleur_3000: List[Objective] = []

        self.year: int = 0
        self.start_x_0: int = 0
        self.start_y_0: int = 0
        self.start_theta_0: float = 0.0
        self.start_x_3000: int = 0
        self.start_y_3000: int = 0
        self.start_theta_3000: float = 0.0

        self.configPath = "../../../config"

    def generate_strategy(self):
        # Création de la stratégie complète
        strat = Strat(
            couleur0=self.objectifs_couleur_0,
            couleur3000=self.objectifs_couleur_3000
        )

        print("#########################")
        print(strat)
        print("#########################")

        os.makedirs(f"{self.configPath}/{self.year}", exist_ok=True)
        with open(f"{self.configPath}/{self.year}/strategy.json", "w") as json_file:
            json.dump(strat.to_dict(), json_file, indent=4)

        print("Test de la strat 0")
        self.test_strategy(
            self.objectifs_couleur_0,
            self.start_x_0,
            self.start_y_0,
            self.start_theta_0,
            "strategyBig0.json",
            'color0'
        )

        print("Test de la strat 3000")
        self.test_strategy(
            self.objectifs_couleur_3000,
            self.start_x_3000,
            self.start_y_3000,
            self.start_theta_3000,
            "strategyBig3000.json",
            'color3000'
        )

    def test_strategy(self, objectives, start_x, start_y, start_theta, output_path, color):
        try:
            with open(f'{self.configPath}/{self.year}/config.json') as config_file:
                config_data = json.load(config_file)
                config_file.close()
                path_finding = AStar(
                    table_config=config_data['table'],
                    active_color=color
                )
                start_point = Position(start_x, start_y, start_theta)
                strat_simu = [{"task": "Position de départ", "command": "start", "position": start_point.to_dict()}]

                for objective in objectives:
                    for task in objective.tasks:
                        task.path_finding = path_finding
                        execution = task.execute(start_point)
                        print(execution)
                        if isinstance(execution, list):
                            strat_simu.extend(execution)
                        else:
                            strat_simu.append(execution)
                        start_point = task.end_point

                with open(output_path, "w") as strat_file:
                    json.dump(strat_simu, strat_file, indent=4)
        except Exception as e:
            print(f"Erreur lors du test de la stratégie : {e}")
            traceback.print_exc()