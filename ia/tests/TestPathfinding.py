import logging
import time

from ia.pathfinding import Pathfinding
from ia.tests import AbstractTest


class TestPathfinding(AbstractTest):
    def test(self) -> None:
        logger = logging.getLogger(__name__)
        total_time = time.time_ns()
        table = Pathfinding(table_config=self.config_data['table'], active_color='color0')  # Utilisation de la configuration JSON
        logger.info(f"Initialisation in {(time.time_ns() - total_time) / 1000000:.2f} ms")
        start = (1800, 750)
        goal = (700, 580)
        start_time = time.time_ns()
        path = table.a_star(start, goal)
        logger.info(f"A* end computation in {(time.time_ns() - start_time) / 1000000:.2f} ms")
        if path is not None:
            for position in path:
                logger.info(position)
        else:
            logger.info("Aucun chemin trouvé")
        logger.info(f"Total computation in {(time.time_ns() - total_time) / 1000000:.2f} ms")