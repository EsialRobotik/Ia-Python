import logging
import sys

from strategy.core.task_list import TaskList
from strategy.main.abstract_main import AbstractMain
from strategy.task.face import Face
from strategy.task.go import Go
from strategy.task.goto import GoTo
from strategy.task.goto_back import GoToBack
from strategy.task.halt_asserv import HaltAsserv
from strategy.task.manipulation import Manipulation
from strategy.task.set_position import SetPosition
from strategy.task.wait_chrono import WaitChrono


class Pami5(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2026
        self.start_x_0: int = 80
        self.start_y_0: int = 692
        self.start_theta_0: float = 1.57079632679
        self.start_x_3000: int = 80
        self.start_y_3000: int = 2308
        self.start_theta_3000: float = -1.57079632679
        self.pivot_offset: float = 43.70
        self.color0 = 'jaune'
        self.color3000 = 'bleu'
        self.wait_chrono=90

    def tag(self, task, needed_flag: str = None):
        """Stampe une tâche avec un `needed_flag` si fourni, sinon la renvoie telle quelle."""
        if needed_flag:
            task.set_needed_flag(needed_flag)
        return task

    def calage(self, tasks_list, needed_flag: str = None):
        tasks_list.add(self.tag(Face(
            desc="On s'aligne",
            position_x=2000,
            position_y=1250
        ), needed_flag))
        tasks_list.add(self.tag(Go(
            desc="On se recale",
            dist=-400,
            timeout=2000
        ), needed_flag))
        tasks_list.add(self.tag(SetPosition(
            desc="On se recale",
            position_x=80,
            position_y=1250,
            angle_theta=0
        ), needed_flag))
        tasks_list.add(self.tag(Go(
            desc="On se dégage du bord",
            dist=100
        ), needed_flag))
        tasks_list.add(self.tag(GoTo(
            desc="On reviens en place pour le finish",
            position_x=220,
            position_y=1250
        ), needed_flag))

    def solo_ninja(self, tasks_list):
        # Toutes les actions du solo ninja (et le calage qui suit) sont
        # conditionnées au flag "solo-pami", déclenchable à distance via
        # `add-flag#solo-pami` côté serveur.
        flag = "solo-pami"
        tasks_list.add(self.tag(GoTo(
            desc="On pousse tout de l'autre côté",
            position_x=220,
            position_y=3000 - 1070
        ), flag))
        tasks_list.add(self.tag(GoToBack(
            desc="On recule",
            position_x=220,
            position_y=3000 - 1250
        ), flag))
        tasks_list.add(self.tag(GoTo(
            desc="On reviens en place pour le finish",
            position_x=220,
            position_y=1250
        ), flag))
        self.calage(tasks_list, needed_flag=flag)

    def generate(self):
        score = 5
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='On commence à remuer les oreilles',
            action_id='oreilles'
        ))
        tasks_list.add(GoTo(
            desc="On trace au centre",
            position_x=80,
            position_y=1500
        ))
        tasks_list.add(Face(
            desc="On pivote",
            position_x=2000,
            position_y=1500
        ))
        tasks_list.add(GoTo(
            desc="On se positionne",
            position_x=220,
            position_y=1500
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=220,
            position_y=0
        ))
        tasks_list.add(GoTo(
            desc="On pousse tout",
            position_x=220,
            position_y=1070
        ))
        tasks_list.add(GoToBack(
            desc="On recule",
            position_x=220,
            position_y=1250
        ))

        self.calage(tasks_list)

        # Les tâches de solo_ninja sont gardées en permanence dans la stratégie
        # et conditionnées au flag "solo-pami" : elles sont skippées si le flag
        # n'est pas présent, et exécutées dès qu'un `add-flag#solo-pami` arrive.
        self.solo_ninja(tasks_list)

        # Mode normal : attente complète (skippée en mode homologation)
        tasks_list.add(WaitChrono(
            desc="On attends le bon moment",
            chrono=self.wait_chrono
        ).set_forbidden_flag('homologation'))
        # Mode homologation : on raccourcit l'attente de 85 s
        tasks_list.add(WaitChrono(
            desc="On attends le bon moment (homologation)",
            chrono=max(0, self.wait_chrono - 85)
        ).set_needed_flag('homologation'))
        tasks_list.add(GoTo(
            desc="On se presque jette dans le vide",
            position_x=420,
            position_y=1250
        ))
        tasks_list.add(Face(
            desc="On se presque jette dans le vide",
            position_x=2000,
            position_y=1250
        ))
        tasks_list.add(HaltAsserv(
            desc='Freeze !!!'
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