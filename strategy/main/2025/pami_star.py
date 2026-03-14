import logging
import sys

from strategy.core.task_list import TaskList
from strategy.main.abstract_main import AbstractMain
from strategy.task.face import Face
from strategy.task.go import Go
from strategy.task.goto import GoTo
from strategy.task.set_position import SetPosition
from strategy.task.wait import Wait


class PamiStar(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2025
        self.start_x_0: int = 60
        self.start_y_0: int = 80
        self.start_theta_0: float = -1.57079632679
        self.start_x_3000: int = 60
        self.start_y_3000: int = 2920
        self.start_theta_3000: float = 1.57079632679
        self.color0 = 'jaune'
        self.color3000 = 'bleu'

    def generate(self):
        score = 20
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Wait(
            desc='On attends son tour',
            ms_count=500#85000
        ))
        tasks_list.add(GoTo(
            desc='On monte sur scène',
            position_x=60,
            position_y=180,
        ))
        tasks_list.add(GoTo(
            desc='On monte sur scène',
            position_x=150,
            position_y=1300,
        ))
        tasks_list.add(Face(
            desc='On regarde la foule',
            position_x=2000,
            position_y=1300,
        ))
        tasks_list.add(Go(
            desc='On se calle le dos bien droit',
            dist=-150,
            timeout=500
        ))
        tasks_list.add(SetPosition(
            desc='On met à jour la position',
            position_x=80,
            position_y=1300,
            angle_theta=0
        ))
        tasks_list.add(GoTo(
            desc='On fait la star',
            position_x=450,
            position_y=1300,
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Être une star',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Être une star',
            id=1,
            score=score,
            priority=1
        ))
        self.generate_strategy('pami1')

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    strategy = PamiStar()
    strategy.generate()