import time

from ia.pathfinding import Table, Pathfinding
from ia.pathfinding.astar.Astar import Astar
from ia.tests import AbstractTest
from ia.utils import Position


class TestPathfinding(AbstractTest):
    def test(self) -> None:
        file_path = 'config/2025/table0.tbl'
        table = Table(file_path)
        table.load_json_from_file(file_path='config/2025/config.json')
        astart = Astar(table)
        pathfinding = Pathfinding(astart)
        pathfinding.compute_path(
            start=Position(x=1000, y=700),
            end=Position(x=1700, y=2000)
        )
        while not pathfinding.is_computation_ended():
            time.sleep(0.05)
        path = pathfinding.get_last_computed_path()
        if path is not None:
            for position in path:
                print(position)
        else:
            print("Aucun chemin trouvé")