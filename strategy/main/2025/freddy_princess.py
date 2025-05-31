import logging
import sys

from strategy.core.task_list import TaskList
from strategy.enum.mirror import Mirror
from strategy.main.abstract_main import AbstractMain
from strategy.task.delete_zone import DeleteZone
from strategy.task.face import Face
from strategy.task.go import Go
from strategy.task.goto import GoTo
from strategy.task.goto_astar import GoToAstar
from strategy.task.goto_back import GoToBack
from strategy.task.manipulation import Manipulation
from strategy.task.set_speed import SetSpeed
from strategy.task.wait import Wait


class FreddyPrincess(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2025
        self.start_x_0: int = 1750
        self.start_y_0: int = 1225
        self.start_theta_0: float = 0.0
        self.start_x_3000: int = 1750
        self.start_y_3000: int = 1775
        self.start_theta_3000: float = 0.0
        self.color0 = 'jaune'
        self.color3000 = 'bleu'

    def generate(self):
        self.banderole()
        self.gradin_so_se()
        self.gradin_o_e()
        #self.gradin_backstage()
        self.backstage()
        self.generate_strategy()

    def banderole(self):
        score = 20
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Go(
            desc='Position dépose banderole',
            dist=200,
            timeout=1000
        ))
        tasks_list.add(Manipulation(
            desc='Dépose banderole',
            action_id='ascenseur_depose_bordure'
        ))
        tasks_list.add(Wait(
            desc='On attends un peu, on est pas des bêtes',
            ms_count=500
        ))
        tasks_list.add(SetSpeed(
            desc='Doucement',
            speed=50
        ))
        tasks_list.add(Go(
            desc='Recule banderole',
            dist=-320,
        ))
        tasks_list.add(SetSpeed(
            desc='Retour à vitesse normale',
            speed=100
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Banderole',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Banderole',
            id=1,
            score=score,
            priority=1
        ))

    def gradin_so_se(self):
        score = 4
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='Ascenseur tout en bas',
            action_id='ascenseur_tout_en_bas'
        ))
        tasks_list.add(GoToAstar(
            desc='Positionnement sur le gradin SO / SE',
            position_x=1300,
            position_y=780
        ))
        tasks_list.add(GoTo(
            desc='Positionnement sur le gradin SO / SE',
            position_x=1300,
            position_y=775
        ))
        tasks_list.add(Face(
            desc='Alignement sur le gradin SO / SE',
            position_x=2000,
            position_y=775
        ))
        tasks_list.add(SetSpeed(
            desc='Low speed',
            speed=50
        ))
        tasks_list.add(GoTo(
            desc='Placement gradin SO / SE',
            position_x=1540,
            position_y=775
        ))
        self.get_gradin(tasks_list)
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de dépose du gradin SO',
                item_id='gradin_so',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de dépose du gradin SE',
                item_id='gradin_se',
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(GoTo(
            desc='Zone de dépose du gradin SO / SE',
            position_x=1700,
            position_y=775
        ))
        tasks_list.add(Face(
            desc='Alignement dépose gradin SO / SE',
            position_x=2000,
            position_y=775
        ))
        self.depose_gradin(tasks_list)
        tasks_list.add(SetSpeed(
            desc='Low speed',
            speed=100
        ))
        tasks_list.add(GoToBack(
            desc='Recule gradin SO / SE',
            position_x=1500,
            position_y=700
        ))
        tasks_list.add(GoToBack(
            desc='Recule gradin SO / SE',
            position_x=1300,
            position_y=700
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Gradin SO / SE',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Gradin SO / SE',
            id=1,
            score=score,
            priority=1
        ))

    def gradin_o_e(self):
        score = 4
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='Ascenseur survole plateforme',
            action_id='ascenseur_tout_en_bas'
        ))
        tasks_list.add(GoToAstar(
            desc='Positionnement sur le gradin O / E',
            position_x=700,
            position_y=1100
        ))
        tasks_list.add(Face(
            desc='Alignement sur le gradin O / E',
            position_x=2000,
            position_y=1100
        ))
        tasks_list.add(SetSpeed(
            desc='Low speed',
            speed=50
        ))
        tasks_list.add(GoTo(
            desc='Placement gradin O / E',
            position_x=830,
            position_y=1100
        ))
        self.get_gradin(tasks_list)
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de dépose du gradin O',
                item_id='gradin_o',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de dépose du gradin E',
                item_id='gradin_e',
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(GoToAstar(
            desc='Zone de dépose du gradin O / E',
            position_x=1700,
            position_y=1220
        ))
        tasks_list.add(Face(
            desc='Alignement dépose gradin O / E',
            position_x=2000,
            position_y=1220
        ))
        self.depose_gradin(tasks_list)
        tasks_list.add(Go(
            desc='Recule gradin',
            dist=-50
        ))
        tasks_list.add(SetSpeed(
            desc='Low speed',
            speed=100
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Gradin O / E',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Gradin O / E',
            id=1,
            score=score,
            priority=1
        ))

    def gradin_backstage(self):
        score = 8
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='Ascenseur tout en bas',
            action_id='ascenseur_tout_en_bas'
        ))
        tasks_list.add(GoToAstar(
            desc='Positionnement sur le gradin ONO / ENE',
            position_x=680,
            position_y=420
        ))
        tasks_list.add(GoTo(
            desc='Positionnement sur le gradin ONO / ENE',
            position_x=675,
            position_y=400
        ))
        tasks_list.add(Face(
            desc='Positionnement sur le gradin ONO / ENE',
            position_x=675,
            position_y=0
        ))
        tasks_list.add(SetSpeed(
            desc='Low speed',
            speed=50
        ))
        tasks_list.add(GoTo(
            desc='Positionnement sur le gradin ONO / ENE',
            position_x=675,
            position_y=300
        ))
        self.get_gradin(tasks_list)
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de dépose du gradin ONO',
                item_id='gradin_ono',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de dépose du gradin ENE',
                item_id='gradin_ene',
                mirror=Mirror.SPECIFIC
            )
        )
        tasks_list.add(Manipulation(
            desc="On lève un peu",
            action_id="ascenseur_appui_plateformes"
        ))
        tasks_list.add(Manipulation(
            desc="On éjecte les extérieurs",
            action_id="pinces_ext_pousser"
        ))
        tasks_list.add(Go(
            desc="On recule",
            dist=-50
        ))
        tasks_list.add(Manipulation(
            desc="On remet en neutre",
            action_id="pinces_ext_neutre"
        ))
        tasks_list.add(GoToBack(
            desc="On recule",
            position_x=675,
            position_y=400
        ))
        tasks_list.add(Manipulation(
            desc="On pose",
            action_id="ascenseur_tout_en_bas"
        ))
        # tasks_list.add(GoToAstar(
        #     desc='Zone de dépose du gradin SO / SE',
        #     position_x=1550,
        #     position_y=770
        # ))
        # tasks_list.add(GoTo(
        #     desc='Zone de dépose du gradin SO / SE',
        #     position_x=1600,
        #     position_y=775
        # ))
        # tasks_list.add(Face(
        #     desc="On s'aligne pour déposer le gradin",
        #     position_x=2000,
        #     position_y=775
        # ))
        # tasks_list.add(Manipulation(
        #     desc="On lève",
        #     action_id="ascenseur_tout_en_haut"
        # ))
        # tasks_list.add(GoTo(
        #     desc='Zone de dépose du gradin SO / SE',
        #     position_x=1700,
        #     position_y=775
        # ))
        # tasks_list.add(Manipulation(
        #     desc='On dépose le gradin',
        #     action_id="pinces_int_lacher"
        # ))
        # tasks_list.add(Manipulation(
        #     desc='On dépose le gradin',
        #     action_id="ascenseur_depose_etage"
        # ))
        # tasks_list.add(GoToBack(
        #     desc="On recule",
        #     position_x=1550,
        #     position_y=775
        # ))
        # tasks_list.add(Manipulation(
        #     desc="Ascenseur en bas",
        #     action_id="ascenseur_tout_en_bas"
        # ))
        # tasks_list.add(Manipulation(
        #     desc='On remet les pinces en neutre',
        #     action_id="pinces_neutre"
        # ))
        # tasks_list.add(SetSpeed(
        #     desc='Low speed',
        #     speed=100
        # ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Gradin Backstage',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Gradin Backstage',
            id=1,
            score=score,
            priority=1
        ))

    def backstage(self):
        score = 10
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Manipulation(
            desc='Ascenseur survole plateforme',
            action_id='ascenseur_tout_en_haut'
        ))
        tasks_list.add(GoToAstar(
            desc='Go backstage',
            position_x=630,
            position_y=360
        ))
        tasks_list.add(Face(
            desc='Alignement backstage',
            position_x=580,
            position_y=360
        ))
        tasks_list.add(Face(
            desc='Alignement backstage',
            position_x=0,
            position_y=360
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Backstage',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Backstage',
            id=1,
            score=score,
            priority=1
        ))

    def get_gradin(self, tasks_list: TaskList):
        tasks_list.add(Go(
            desc='On avance pour chopper',
            dist=50,
            timeout=500
        ))

    def depose_gradin(self, tasks_list: TaskList):
        tasks_list.add(Manipulation(
            desc='On décroche tout',
            action_id='pinces_lacher'
        ))
        tasks_list.add(Go(
             desc='On recule',
             dist=-180
        ))
        tasks_list.add(Manipulation(
            desc='On reviens neutre',
            action_id='pinces_neutre'
        ))
        # tasks_list.add(Manipulation(
        #     desc='Souffler pompe interieur',
        #     action_id='pompe_interieur_souffler'
        # ))
        # tasks_list.add(Wait(
        #     desc='Attente souffle',
        #     ms_count=250
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Arret pompe interieur',
        #     action_id='pompe_interieur_off'
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Arret pompe superieur',
        #     action_id='pompe_superieur_off'
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Souffler pompe exterieur',
        #     action_id='pompe_exterieur_souffler'
        # ))
        # tasks_list.add(Wait(
        #     desc='Attente souffle',
        #     ms_count=250
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Arret pompe exterieur',
        #     action_id='pompe_exterieur_off'
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Ascenseur tout en haut',
        #     action_id='ascenseur_tout_en_haut'
        # ))
        # tasks_list.add(Go(
        #     desc='Recule gradin',
        #     dist=-50
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Rentrée des pinces',
        #     action_id='pinces_rentrer'
        # ))
        # tasks_list.add(Manipulation(
        #     desc='Ascenseur survole plateforme',
        #     action_id='ascenseur_survole_plateformes'
        # ))

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)
    logger = logging.getLogger(__name__)
    logger.info("init logger")

    strategy = FreddyPrincess()
    strategy.generate()