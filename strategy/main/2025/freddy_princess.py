from strategy.core.task_list import TaskList
from strategy.enum.mirror import Mirror
from strategy.main.abstract_main import AbstractMain
from strategy.task.delete_zone import DeleteZone
from strategy.task.go import Go
from strategy.task.goto_astar import GoToAstar
from strategy.task.manipulation import Manipulation
from strategy.task.set_speed import SetSpeed


class FreddyPrincess(AbstractMain):
    def __init__(self):
        super().__init__()
        self.year: int = 2025
        self.start_x_0: int = 1800
        self.start_y_0: int = 1225
        self.start_theta_0: float = 0.0
        self.start_x_3000: int = 1800
        self.start_y_3000: int = 1775
        self.start_theta_3000: float = 0.0

    def generate(self):
        self.liberation_depart()
        self.banderole()
        self.gradin_so()
        self.generate_strategy()

    def liberation_depart(self):
        score = 0
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_jaune_back',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_bleu_back',
                mirror=Mirror.SPECIFIC
            ),
        )
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_jaune_side',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_bleu_side',
                mirror=Mirror.SPECIFIC
            ),
        )
        tasks_list.add(
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_jaune_front',
                mirror=Mirror.SPECIFIC
            ),
            DeleteZone(
                desc='Suppression zone de départ',
                item_id='start_bleu_front',
                mirror=Mirror.SPECIFIC
            ),
        )
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Libération départ jaune',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Libération départ bleu',
            id=1,
            score=score,
            priority=1
        ))

    def banderole(self):
        score = 20
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(SetSpeed(
            desc='Vitesse de dépose banderole',
            speed=25
        ))
        tasks_list.add(Go(
            desc='Position dépose banderole',
            dist=50,
            timeout=500
        ))
        tasks_list.add(Manipulation(
            desc='Dépose banderole',
            action_id='banderole_depose'
        ))
        tasks_list.add(Go(
            desc='Recule banderole',
            dist=-300
        ))
        tasks_list.add(SetSpeed(
            desc='Vitesse normale',
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

    def gradin_so(self):
        score = 12
        tasks_list = TaskList(mirror_size=3000)
        tasks_list.add(GoToAstar(
            desc='Positionnement sur le gradin SO',
            position_x=1300,
            position_y=750
        ))
        self.objectifs_couleur_0.append(tasks_list.generate_objective(
            name='Gradin SO',
            id=1,
            score=score,
            priority=1
        ))
        self.objectifs_couleur_3000.append(tasks_list.generate_mirror_objective(
            name='Gradin SO',
            id=1,
            score=score,
            priority=1
        ))

if __name__ == "__main__":
    strategy = FreddyPrincess()
    strategy.generate()