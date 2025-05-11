import logging
import time

from ia.pathfinding.astar import AStar
from ia.tests.abstract_test import AbstractTest
from ia.utils.position import Position


class TestPathfinding(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        total_time = time.time_ns()
        table = AStar(table_config=self.config_data['table'], active_color='color0')  # Utilisation de la configuration JSON
        logger.info(f"Initialisation in {(time.time_ns() - total_time) / 1000000:.2f} ms")
        start = Position(700, 500)
        goal = Position(1400, 2300)

        table.update_dynamic_zone('start_jaune_back', False)
        table.update_dynamic_zone('start_jaune_side', False)
        table.update_dynamic_zone('start_jaune_front', False)

        table.a_star(start, goal)
        path = table.path
        if path is not None:
            for position in path:
                logger.info(position)
        else:
            logger.info("Aucun chemin trouvé")
        logger.info(f"Total computation in {(time.time_ns() - total_time) / 1000000:.2f} ms")