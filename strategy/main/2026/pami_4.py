import logging
import sys

from strategy.core.task_list import TaskList
from strategy.enum.mirror import Mirror
from strategy.main.abstract_main import AbstractMain
from strategy.task.add_zone import AddZone
from strategy.task.delete_zone import DeleteZone
from strategy.task.face import Face
from strategy.task.go import Go
from strategy.task.goto import GoTo
from strategy.task.goto_astar import GoToAstar
from strategy.task.halt_asserv import HaltAsserv
from strategy.task.manipulation import Manipulation
from strategy.task.wait import Wait
from strategy.task.wait_chrono import WaitChrono


class Pami4(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2026
        self.start_x_0: int = 390
        self.start_y_0: int = 80
        self.start_theta_0: float = 1.57079632679
        self.start_x_3000: int = 390
        self.start_y_3000: int = 2920
        self.start_theta_3000: float = -1.57079632679
        self.pivot_offset: float = 43.70
        self.color0 = 'jaune'
        self.color3000 = 'bleu'
        self.wait_chrono = 89

    def clear_zone(self, tasks_list: TaskList) -> None:
        tasks_list.add(
            DeleteZone(
                desc="On libère la zone caisses 1",
                item_id="caisse_jaune_1",
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc="On libère la zone caisses 1",
                item_id="caisse_bleu_1",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(
            DeleteZone(
                desc="On libère la zone caisses 3",
                item_id="caisse_jaune_3",
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc="On libère la zone caisses 3",
                item_id="caisse_bleu_3",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(
            DeleteZone(
                desc="On libère la zone caisses 4",
                item_id="caisse_jaune_4",
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc="On libère la zone caisses 4",
                item_id="caisse_bleu_4",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(AddZone(
            desc="On verrouille la zone",
            item_id="garde_manger_centre_1"
        ))
        tasks_list.add(
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_jaune_3",
                mirror=Mirror.SPECIFIC
            ),
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_bleu_3",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_jaune_4",
                mirror=Mirror.SPECIFIC
            ),
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_bleu_4",
                mirror=Mirror.SPECIFIC
            )
        )

    def generate(self):
        score = 5
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='On commence à remuer les oreilles',
            action_id='oreilles'
        ))

        #self.clear_zone(tasks_list)

        # Mode normal : attente complète (skippée en mode homologation)
        tasks_list.add(WaitChrono(
            desc='On attends son tour',
            chrono=self.wait_chrono
        ).set_forbidden_flag('homologation'))
        # Mode homologation : on raccourcit l'attente de 85 s
        tasks_list.add(WaitChrono(
            desc='On attends son tour (homologation)',
            chrono=max(0, self.wait_chrono - 85)
        ).set_needed_flag('homologation'))
        tasks_list.add(Go(
            desc='On avance un peu pour manoeuvrer',
            dist=100
        ))
        tasks_list.add(GoToAstar(
            desc='On file dans le garde manger',
            position_x=1200,
            position_y=400,
        ))
        tasks_list.add(GoTo(
            desc='On entre dans le garde manger',
            position_x=1200,
            position_y=180,
        ))
        tasks_list.add(Face(
            desc='On entre dans le garde manger',
            position_x=1200,
            position_y=000,
        ))
        tasks_list.add(HaltAsserv(
            desc='Freeze !!!'
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