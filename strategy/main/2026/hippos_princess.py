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
from strategy.task.goto_back import GoToBack
from strategy.task.manipulation import Manipulation
from strategy.task.reset_flag import ResetFlag
from strategy.task.set_speed import SetSpeed


class HypposPrincess(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2026
        self.start_x_0: int = 150
        self.start_y_0: int = 350
        self.start_theta_0: float = 0
        self.start_x_3000: int = 150
        self.start_y_3000: int = 2650
        self.start_theta_3000: float = 0
        self.color0 = 'jaune'
        self.color3000 = 'bleu'

        self.distance_photo = 380

    def generate(self):
        self.quitter_depart()
        self.get_caisse_3()
        self.depose_garde_manger_centre_1()
        self.get_caisse_4()
        self.regler_temperature()
        self.depose_garde_manger_centre_2()
        self.get_caisse_2()
        self.depose_garde_manger_couleur_2()
        self.get_caisse_1()
        self.depose_garde_manger_couleur_1()
        self.generate_strategy('princess')

    def quitter_depart(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoTo(
            desc="On quitte la zone de départ",
            position_x=350,
            position_y=350
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='On quitte la zone de départ',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='On quitte la zone de départ',
            id=1,
            score=score,
            priority=1
        ))

    def get_caisse_1(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position caisse 1",
            position_x=800,
            position_y=250 + self.distance_photo,
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=800,
            position_y=0,
        ))
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        tasks_list.add(
            Manipulation(
                desc="Photo caisse",
                action_id="detect_noisettes_bleues",
                mirror=Mirror.SPECIFIC
            ),
            Manipulation(
                desc="Photo caisse",
                action_id="detect_noisettes_jaunes",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        self.ramasser_caisses(tasks_list)
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
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Ramassage caisses 1',
            id=2,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Ramassage caisses 1',
            id=2,
            score=score,
            priority=1
        ))

    def get_caisse_2(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position caisse 2",
            position_x=1600,
            position_y=250 + self.distance_photo,
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=1600,
            position_y=0,
        ))
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        tasks_list.add(
            Manipulation(
                desc="Photo caisse 3",
                action_id="detect_noisettes_bleues",
                mirror=Mirror.SPECIFIC
            ),
            Manipulation(
                desc="Photo caisse 3",
                action_id="detect_noisettes_jaunes",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        self.ramasser_caisses(tasks_list)
        tasks_list.add(
            DeleteZone(
                desc="On libère la zone caisses 2",
                item_id="caisse_jaune_2",
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc="On libère la zone caisses 2",
                item_id="caisse_bleu_2",
                mirror=Mirror.SPECIFIC
            )
        )
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Ramassage caisses 2',
            id=2,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Ramassage caisses 2',
            id=2,
            score=score,
            priority=1
        ))

    def get_caisse_3(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position caisse 3",
            position_x=1200 - self.distance_photo,
            position_y=1150,
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=2000,
            position_y=1150,
        ))
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        tasks_list.add(
            Manipulation(
                desc="Photo caisse 3",
                action_id="detect_noisettes_bleues",
                mirror=Mirror.SPECIFIC
            ),
            Manipulation(
                desc="Photo caisse 3",
                action_id="detect_noisettes_jaunes",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        self.ramasser_caisses(tasks_list)
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
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Ramassage caisses 3',
            id=2,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Ramassage caisses 3',
            id=2,
            score=score,
            priority=1
        ))

    def get_caisse_4(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position caisse 4",
            position_x=1750 - self.distance_photo,
            position_y=1100,
        ))
        tasks_list.add(Face(
            desc="On s'aligne",
            position_x=2000,
            position_y=1100,
        ))
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        tasks_list.add(
            Manipulation(
                desc="Photo caisse 4",
                action_id="detect_noisettes_bleues",
                mirror=Mirror.SPECIFIC
            ),
            Manipulation(
                desc="Photo caisse 3",
                action_id="detect_noisettes_jaunes",
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(Manipulation(
            desc="Petite pause",
            action_id="wait_500ms"
        ))
        self.ramasser_caisses(tasks_list)
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
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Ramassage caisses 4',
            id=4,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Ramassage caisses 4',
            id=4,
            score=score,
            priority=1
        ))

    def depose_garde_manger_centre_1(self):
        score = 17
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position garde manger centre 1",
            position_x=1200,
            position_y=1200,
        ))
        tasks_list.add(GoTo(
            desc="Position de largage",
            position_x = 1200,
            position_y = 1300,
        ))
        self.larguer_caisses(tasks_list)
        tasks_list.add(GoToBack(
            desc="On se dégage pour la suite",
            position_x = 1200,
            position_y = 1200,
        ))
        tasks_list.add(AddZone(
            desc="On verrouille la zone",
            item_id="garde_manger_centre_1"
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Largage garde manger centre 1',
            id=3,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Largage garde manger centre 1',
            id=3,
            score=score,
            priority=1
        ))

    def depose_garde_manger_centre_2(self):
        score = 17
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position garde manger centre 2",
            position_x=1600,
            position_y=1500,
        ))
        tasks_list.add(GoTo(
            desc="Position de largage",
            position_x = 1700,
            position_y = 1500,
        ))
        self.larguer_caisses(tasks_list)
        tasks_list.add(GoToBack(
            desc="On se dégage pour la suite",
            position_x=1600,
            position_y=1500,
        ))
        tasks_list.add(AddZone(
            desc="On verrouille la zone",
            item_id="garde_manger_centre_2"
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Largage garde manger centre 2',
            id=5,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Largage garde manger centre 2',
            id=5,
            score=score,
            priority=1
        ))

    def depose_garde_manger_couleur_1(self):
        score = 17
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position garde manger couleur 1",
            position_x=1200,
            position_y=400,
        ))
        tasks_list.add(GoTo(
            desc="Position de largage",
            position_x = 1200,
            position_y = 300,
        ))
        self.larguer_caisses(tasks_list)
        tasks_list.add(GoToBack(
            desc="On se dégage pour la suite",
            position_x=1200,
            position_y=400,
        ))
        tasks_list.add(
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_jaune_1",
                mirror=Mirror.SPECIFIC
            ),
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_bleu_1",
                mirror=Mirror.SPECIFIC
            )
        )
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Largage garde manger couleur 1',
            id=5,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Largage garde manger couleur 1',
            id=5,
            score=score,
            priority=1
        ))

    def depose_garde_manger_couleur_2(self):
        score = 17
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position garde manger couleur 2",
            position_x=1600,
            position_y=700,
        ))
        tasks_list.add(GoTo(
            desc="Position de largage",
            position_x = 1700,
            position_y = 700,
        ))
        self.larguer_caisses(tasks_list)
        tasks_list.add(GoToBack(
            desc="On se dégage pour la suite",
            position_x=1600,
            position_y=700,
        ))
        tasks_list.add(
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_jaune_2",
                mirror=Mirror.SPECIFIC
            ),
            AddZone(
                desc="On verrouille la zone",
                item_id="garde_manger_bleu_2",
                mirror=Mirror.SPECIFIC
            )
        )
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Largage garde manger couleur 2',
            id=5,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Largage garde manger couleur 2',
            id=5,
            score=score,
            priority=1
        ))

    def regler_temperature(self):
        score = 10
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc="Position temperature garde-manger centre 2",
            position_x=1600,
            position_y=1500,
        ))
        tasks_list.add(GoTo(
            desc="On se met proche du bord",
            position_x=1700,
            position_y=1500,
        ))
        tasks_list.add(Face(
            desc="Alignement",
            position_x=1700,
            position_y=0,
        ))
        tasks_list.add(SetSpeed(
            desc="Piano piano",
            speed=50
        ))
        # todo on sort le bras
        tasks_list.add(GoTo(
            desc="On règle la température",
            position_x=1700,
            position_y=700,
        ))
        # todo on rentre le bras
        tasks_list.add(SetSpeed(
            desc="Full speed",
            speed=100
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Réglage de la température',
            id=5,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Réglage de la température',
            id=5,
            score=score,
            priority=1
        ))

    def ramasser_caisses(self, task_list):
        task_list.add(Manipulation(
            desc="On lève l'ascenseur",
            action_id="lever"
        ))
        task_list.add(Manipulation(
            desc="On ouvre les doigts",
            action_id="ouvrir"
        ))
        task_list.add(SetSpeed(
            desc="Piano piano",
            speed=50
        ))
        task_list.add(Go(
            desc="On se colle aux caisse",
            dist=260
        ))
        task_list.add(Go(
            desc="On se décolle des caisse",
            dist=-35
        ))
        task_list.add(Manipulation(
            desc="On ramasse",
            action_id="routine_ramasser_ecarter"
        ))
        task_list.add(Manipulation(
            desc="SIT AND ROTATE 1",
            action_id="tourner_pince_1_180"
        ).set_needed_flag("rotateNut1"))
        task_list.add(Manipulation(
            desc="SIT AND ROTATE 2",
            action_id="tourner_pince_2_180"
        ).set_needed_flag("rotateNut2"))
        task_list.add(Manipulation(
            desc="SIT AND ROTATE 3",
            action_id="tourner_pince_3_180"
        ).set_needed_flag("rotateNut3"))
        task_list.add(Manipulation(
            desc="SIT AND ROTATE 4",
            action_id="tourner_pince_4_180"
        ).set_needed_flag("rotateNut4"))
        task_list.add(Manipulation(
            desc="Les caisses qui collent",
            action_id="coller"
        ))
        task_list.add(SetSpeed(
            desc="Distorsion maximum",
            speed=100
        ))

    def larguer_caisses(self, task_list):
        task_list.add(Manipulation(
            desc="On pose les caisses",
            action_id="routine_coller_poser"
        ))
        task_list.add(ResetFlag(
            desc="On reset les flags de rotations",
            flags=["rotateNut1", "rotateNut2", "rotateNut3", "rotateNut4"],
        ))

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    strategy = HypposPrincess()
    strategy.generate()