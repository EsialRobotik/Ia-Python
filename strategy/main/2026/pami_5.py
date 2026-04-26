import logging
import sys

from strategy.core.task_list import TaskList
from strategy.enum.mirror import Mirror
from strategy.main.abstract_main import AbstractMain
from strategy.task.face import Face
from strategy.task.goto import GoTo
from strategy.task.goto_back import GoToBack
from strategy.task.manipulation import Manipulation
from strategy.task.orbital_turn import OrbitalTurn
from strategy.task.wait_chrono import WaitChrono


class Pami5(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2026
        self.start_x_0: int = 60
        self.start_y_0: int = 692
        self.start_theta_0: float = 1.57079632679
        self.start_x_3000: int = 60
        self.start_y_3000: int = 2308
        self.start_theta_3000: float = -1.57079632679
        self.pivot_offset: float = 43.70
        self.color0 = 'jaune'
        self.color3000 = 'bleu'

    def generate(self):
        score = 5
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='On commence à remuer les oreilles',
            action_id='oreilles'
        ))
        tasks_list.add(GoTo(
            desc="On trace au centre",
            position_x=60,
            position_y=1350
        ))
        tasks_list.add(
            OrbitalTurn(
                desc="On pivote",
                degrees=90,
                pivot_offset=self.pivot_offset,
                forward=True,
                on_right_wheel=True,
                mirror=Mirror.SPECIFIC
            ),
            OrbitalTurn(
                desc="On pivote",
                degrees=90,
                pivot_offset=self.pivot_offset,
                forward=True,
                on_right_wheel=False,
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(GoTo(
            desc="On se positionne",
            position_x=220,
            position_y=1482
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=220,
            position_y=0
        ))
        tasks_list.add(GoTo(
            desc="On pousse tout",
            position_x=220,
            position_y=1100
        ))
        tasks_list.add(GoToBack(
            desc="On recule",
            position_x=220,
            position_y=1250
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=2000,
            position_y=1250
        ))
        tasks_list.add(WaitChrono(
            desc="On attends le bon moment",
            chrono=90
        ))
        tasks_list.add(GoTo(
            desc="On se presque jette dans le vide",
            position_x=420,
            position_y=1250
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Pami 5',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Pami 5',
            id=1,
            score=score,
            priority=1
        ))
        self.generate_strategy('pami5')

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    strategy = Pami5()
    strategy.generate()