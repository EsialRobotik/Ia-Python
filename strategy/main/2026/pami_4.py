import logging
import sys

from strategy.core.task_list import TaskList
from strategy.main.abstract_main import AbstractMain
from strategy.task.goto import GoTo
from strategy.task.goto_astar import GoToAstar
from strategy.task.manipulation import Manipulation
from strategy.task.wait import Wait


class Pami4(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2026
        self.start_x_0: int = 390
        self.start_y_0: int = 80
        self.start_theta_0: float = 1.57079632679
        self.start_x_3000: int = 390
        self.start_y_3000: int = 2920
        self.start_theta_3000: float = 1.57079632679
        self.color0 = 'jaune'
        self.color3000 = 'bleu'

    def generate(self):
        score = 5
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='On commence à remuer les oreilles',
            action_id='oreilles'
        ))
        tasks_list.add(Wait(
            desc='On attends son tour',
            ms_count=87000
        ))
        tasks_list.add(GoToAstar(
            desc='On file dans le garde manger',
            position_x=1000,
            position_y=100,
        ))
        tasks_list.add(GoTo(
            desc='On entre dans le garde manger',
            position_x=1070,
            position_y=100,
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Pami 4',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Pami 4',
            id=1,
            score=score,
            priority=1
        ))
        self.generate_strategy('pami4')

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    strategy = Pami4()
    strategy.generate()