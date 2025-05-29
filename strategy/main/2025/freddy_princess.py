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
        #self.gradin_so_se()
        #self.gradin_o_e()
        self.backstage()
        self.generate_strategy()

    def banderole(self):
        score = 20
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(Go(
            desc='Position dépose banderole',
            dist=150,
            timeout=1000
        ))
        tasks_list.add(Manipulation(
            desc='Dépose banderole',
            action_id='ascenseur_depose_bordure'
        ))
        tasks_list.add(Wait(
            desc='On attends un peu, on est pas des bêtes',
            ms_count=1000
        ))
        tasks_list.add(Go(
            desc='Recule banderole',
            dist=-320,
            timeout=1000
        ))
        tasks_list.add(Manipulation(
            desc='Ascenseur survole plateforme',
            action_id='ascenseur_tout_en_haut'
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
        score = 12
        tasks_list = TaskList(mirror_size=3000)
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
        tasks_list.add(GoTo(
            desc='Placement gradin SO / SE',
            position_x=1540,
            position_y=775
        ))
        #self.get_gradin(tasks_list)
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
            position_x=1750,
            position_y=775
        ))
        tasks_list.add(Face(
            desc='Alignement dépose gradin SO / SE',
            position_x=2000,
            position_y=775
        ))
        #self.depose_gradin(tasks_list)
        tasks_list.add(GoToBack(
            desc='Recule gradin SO / SE',
            position_x=1500,
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
        score = 12
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc='Positionnement sur le gradin O / E',
            position_x=750,
            position_y=1100
        ))
        tasks_list.add(Face(
            desc='Alignement sur le gradin O / E',
            position_x=2000,
            position_y=1100
        ))
        tasks_list.add(GoTo(
            desc='Placement gradin O / E',
            position_x=830,
            position_y=1100
        ))
        #self.get_gradin(tasks_list)
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
            position_x=1750,
            position_y=1220
        ))
        tasks_list.add(Face(
            desc='Alignement dépose gradin O / E',
            position_x=2000,
            position_y=1220
        ))
        #self.depose_gradin(tasks_list)
        tasks_list.add(Go(
            desc='Recule gradin',
            dist=-50
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

    def backstage(self):
        score = 10
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc='Go backstage',
            position_x=630,
            position_y=350
        ))
        tasks_list.add(Face(
            desc='Alignement backstage',
            position_x=600,
            position_y=350
        ))
        tasks_list.add(Face(
            desc='Alignement backstage',
            position_x=0,
            position_y=350
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
        tasks_list.add(Manipulation(
            desc='Ascenseur appui sur les plateformes',
            action_id='ascenseur_appui_plateformes'
        ))
        tasks_list.add(Manipulation(
            desc='Allumage pompe plateforme',
            action_id='pompe_superieur_aspirer'
        ))
        tasks_list.add(Manipulation(
            desc='Allumage pompe interieur',
            action_id='pompe_interieur_aspirer'
        ))
        tasks_list.add(Manipulation(
            desc='Allumage pompe exterieur',
            action_id='pompe_exterieur_aspirer'
        ))
        tasks_list.add(Manipulation(
            desc='Sortie des pinces',
            action_id='pinces_sortir'
        ))
        tasks_list.add(Wait(
            desc='Attente de la prise du gradin',
            ms_count=250
        ))
        tasks_list.add(Manipulation(
            desc='Rentrée des pinces',
            action_id='pinces_rentrer'
        ))
        tasks_list.add(Go(
            desc='Recule gradin',
            dist=-50
        ))
        tasks_list.add(Manipulation(
            desc='Ascenseur tout en haut',
            action_id='ascenseur_tout_en_haut'
        ))
        tasks_list.add(Go(
            desc='Avance gradin',
            dist=50
        ))
        tasks_list.add(Manipulation(
            desc='Sortie des pinces',
            action_id='pinces_sortir'
        ))
        tasks_list.add(Manipulation(
            desc='Ascenseur depose haut',
            action_id='ascenseur_tout_en_haut_depose'
        ))

    def depose_gradin(self, tasks_list: TaskList):
        tasks_list.add(Manipulation(
            desc='Souffler pompe interieur',
            action_id='pompe_interieur_souffler'
        ))
        tasks_list.add(Wait(
            desc='Attente souffle',
            ms_count=250
        ))
        tasks_list.add(Manipulation(
            desc='Arret pompe interieur',
            action_id='pompe_interieur_off'
        ))
        tasks_list.add(Manipulation(
            desc='Arret pompe superieur',
            action_id='pompe_superieur_off'
        ))
        tasks_list.add(Manipulation(
            desc='Souffler pompe exterieur',
            action_id='pompe_exterieur_souffler'
        ))
        tasks_list.add(Wait(
            desc='Attente souffle',
            ms_count=250
        ))
        tasks_list.add(Manipulation(
            desc='Arret pompe exterieur',
            action_id='pompe_exterieur_off'
        ))
        tasks_list.add(Manipulation(
            desc='Ascenseur tout en haut',
            action_id='ascenseur_tout_en_haut'
        ))
        tasks_list.add(Go(
            desc='Recule gradin',
            dist=-50
        ))
        tasks_list.add(Manipulation(
            desc='Rentrée des pinces',
            action_id='pinces_rentrer'
        ))
        tasks_list.add(Manipulation(
            desc='Ascenseur survole plateforme',
            action_id='ascenseur_survole_plateformes'
        ))

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