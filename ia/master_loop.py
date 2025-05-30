import logging
import logging.handlers
import threading
import time
from typing import Optional, Dict

from ia.api.chrono import Chrono
from ia.api.nextion_nx32224t024 import NextionNX32224T024
from ia.api.pull_cord import PullCord
from ia.asservissement.asserv_status import AsservStatus
from ia.manager.action_manager import ActionManager
from ia.manager.communication_manager import CommunicationManager
from ia.manager.detection_manager import DetectionManager
from ia.manager.movement_manager import MovementManager
from ia.manager.strategy_manager import StrategyManager
from ia.pathfinding.astar import AStar
from ia.strategy.objective import Objective
from ia.strategy.step import Step
from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position


class MasterLoop:

    current_objective: Optional[Objective]
    current_step: Optional[Step]

    def __init__(
        self,
        action_manager: ActionManager,
        comm_config: Dict,
        detection_manager: DetectionManager,
        movement_manager: MovementManager,
        strategy_manager: StrategyManager,
        table_config: Dict,
        chrono: Chrono,
        pull_cord: PullCord,
        nextion_display: NextionNX32224T024
    ) -> None:
        self.comm_config = comm_config
        self.communication_manager = None
        self.table_config = table_config
        self.pathfinding = None

        self.action_manager = action_manager
        self.detection_manager = detection_manager
        self.movement_manager = movement_manager
        self.strategy_manager = strategy_manager
        self.chrono = chrono
        self.pull_cord = pull_cord
        self.nextion_display = nextion_display
        self.interrupted = False
        self.score = 0
        self.astar_launch = False
        self.logger = logging.getLogger(__name__)

        self.something_detected = False
        self.moving_forward = False
        self.is_color0 = True

    def init(self) -> None:
        """
        Initialize the Nextion display and perform the necessary setup steps.
        """
        self.logger.info("Init mainLoop")
        self.nextion_display.goto_page("init")
        self.logger.info("Attente lancement calibration")
        self.nextion_display.wait_for_calibration()

        self.logger.info("Initialisation des actionneurs")
        self.nextion_display.display_calibration_status("Initialisation des actionneurs")
        self.action_manager.init()

        self.logger.info("Calage bordure")
        self.nextion_display.display_calibration_status("Calage bordure")
        self.movement_manager.go_start(self.nextion_display.color)

        self.logger.info("Calibration OK, attente tirette")
        self.nextion_display.display_calibration_status("Attente tirette pour depart")
        self.pull_cord.wait_for_state(True)
        self.logger.info("Tirette insérée, fin de la calibration")

        self.logger.info("Initialisation du pathfinding")
        self.nextion_display.display_calibration_status("Initialisation du pathfinding")
        self.pathfinding = AStar(
            table_config=self.table_config,
            active_color=self.nextion_display.color
        )
        self.logger.info("Initialisation du pathfinding OK")

        if self.comm_config['active']:
            self.logger.info("Initialisation du communication manager")
            self.nextion_display.display_calibration_status("Initialisation du communication manager")
            self.communication_manager = CommunicationManager(
                action_manager=self.action_manager,
                pathfinding=self.pathfinding,
                comm_config=self.comm_config
            )
            self.logger.info("Initialisation du communication manager OK")

        self.logger.info("Pré-chargement de la stratégie")
        self.is_color0 = self.nextion_display.is_color0()
        self.strategy_manager.prepare_objectives(self.is_color0)
        self.logger.info(f"Stratégie chargée : {len(self.strategy_manager.objectives)} objectifs")

        # Prepare first objective and strategy
        self.current_objective = self.strategy_manager.get_next_objective()
        self.current_step = self.current_objective.get_next_step(self.strategy_manager.action_flags)
        self.logger.info(f"Premier Objectif : {self.current_objective}")
        self.logger.info(f"Première Step : {self.current_step}")

        self.logger.info("Prêt pour départ")
        self.nextion_display.goto_page("ready")

    def match_end(self) -> None:
        """
        End the match and perform necessary shutdown actions.

        This method logs the end of the match, stops the movement manager, detection manager,
        and action supervisor, updates the score with any funny actions, and sets the interrupted flag.
        """
        self.logger.info("Fin du match")
        # Stop the asservissement here
        self.logger.info("Arrêt asservissement")
        self.movement_manager.halt_asserv(False)

        # Don't forget actions
        self.logger.info("Arrêt actionneurs")
        self.action_manager.stop_actions()

        self.interrupted = True
        self.update_score()

    def update_score(self) -> None:
        """
        Update the score displayed on the Nextion display.
        """
        self.nextion_display.display_score(self.score)

    def compute_astar(self, goal: Position) -> None:
        """
        Compute the astar path.
        """
        pathfinding_thread = threading.Thread(target=self.pathfinding.a_star(
            start=self.movement_manager.current_position(),
            goal=goal
        ))
        pathfinding_thread.daemon = True
        pathfinding_thread.start()
        self.astar_launch = True

    def execute_current_step(self) -> None:
        """
        Execute the current strategy based on its type and subtype.

        This method checks the type and subtype of the current strategy and performs the corresponding action,
        such as executing a manipulation command, computing an A* path, or updating a dynamic zone.

        Returns
        -------
        None
        """
        if not self.current_step:
            return
        elif self.current_step.action_type == StepType.MANIPULATION:
            self.logger.info(f"Manipulation id : {self.current_step.id_action}")
            self.action_manager.execute_command(self.current_step.id_action)
        elif self.current_step.action_type == StepType.MOVEMENT:
            self.logger.info(f"Déplacement {self.current_step.sub_type}")
            if self.current_step.sub_type == StepSubType.GOTO_ASTAR:
                # We need to launch the astar
                self.compute_astar(self.current_step.position)
                self.astar_launch = True
            elif self.current_step.sub_type == StepSubType.GOTO_CHAIN:
                self.logger.info("Goto chain")
                path: list[Position] = []
                end_pos: Position = self.current_step.position
                path.append(Position(end_pos.x, end_pos.y))
                while self.current_objective.get_next_step_real() is not None and \
                        self.current_objective.get_next_step_real().sub_type == StepSubType.GOTO_CHAIN:
                    self.current_step = self.current_objective.get_next_step(self.strategy_manager.action_flags)
                    self.logger.info(f"Compute enchain, strategy = {self.current_step.description}")
                    end_pos = self.current_step.position
                    path.append(Position(end_pos.x, end_pos.y))
                self.logger.info(f"Enchain {len(path)} actions")
                self.movement_manager.execute_movement(path)
            else:
                self.movement_manager.execute_step_deplacement(self.current_step)
        elif self.current_step.action_type == StepType.ELEMENT:
            if self.current_step.sub_type == StepSubType.DELETE_ZONE:
                self.logger.info(f"Libération de la zone interdite {self.current_step.item_id}")
                self.pathfinding.update_dynamic_zone(self.current_step.item_id, False)
                if self.communication_manager is not None:
                    self.communication_manager.send_delete_zone(self.current_step.item_id)
            elif self.current_step.sub_type == StepSubType.ADD_ZONE:
                self.logger.info(f"Ajout de la zone interdite {self.current_step.item_id}")
                self.pathfinding.update_dynamic_zone(self.current_step.item_id, True)
                if self.communication_manager is not None:
                    self.communication_manager.send_add_zone(self.current_step.item_id)

    def current_step_ended(self) -> bool:
        """
        Check if the current strategy has ended.

        Returns
        -------
        bool
            True if the current strategy has ended, False otherwise.
        """
        step_type: StepType = self.current_step.action_type
        if step_type == StepType.MOVEMENT and self.current_step.sub_type == StepSubType.WAIT_CHRONO:
            return (self.current_step.timeout * 1000) <= self.chrono.get_time_since_beginning()
        elif step_type == StepType.MOVEMENT and self.current_step.sub_type == StepSubType.WAIT:
            try:
                time.sleep(self.current_step.timeout // 1000)
            except InterruptedError as e:
                self.logger.error(e)
            return True
        elif step_type == StepType.MOVEMENT and self.movement_manager.is_last_ordered_movement_ended():
            return True
        elif step_type == StepType.MANIPULATION and self.action_manager.is_last_execution_finished():
            if self.action_manager.action_flag is not None:
                self.strategy_manager.add_action_flag(self.action_manager.action_flag)
            return True
        elif step_type == StepType.ELEMENT:
            return True
        return False

    def must_stop_from_emergency_detection(self) -> bool:
        # On vérifie la détection courte portée des SRF
        if self.detection_manager.is_emergency_detection_front():
            self.logger.info("Détection avant")
            self.movement_manager.halt_asserv(True)
            self.moving_forward = True
            self.something_detected = True
            return True
        elif self.detection_manager.is_emergency_detection_back():
            self.logger.info("Détection arrière")
            self.movement_manager.halt_asserv(True)
            self.moving_forward = False
            self.something_detected = True
            return True
        return False

    def update_step(self) -> None:
        self.logger.info(f"Step terminée : {self.current_step.description}")

        self.current_step = None
        if self.current_objective.has_next_step():
            self.current_step = self.current_objective.get_next_step(self.strategy_manager.action_flags)
            self.logger.info(f"Prochaine Step : {self.current_step.description}")
        else:
            self.logger.info(
                f"Objectif terminé : {self.current_objective.description} - {self.current_objective.points}")
            self.score += self.current_objective.points
            self.update_score()

            if self.current_objective.action_flag is not None:
                self.logger.info(f"Lever de l'action flage : {self.current_objective.action_flag}")
                self.strategy_manager.add_action_flag(self.current_objective.action_flag)

            self.current_objective = self.strategy_manager.get_next_objective()
            if self.current_objective is None:
                self.logger.info("Plus d'objectif, fin du match")
                self.interrupted = True
            else:
                self.logger.info(f"Prochain Objectif : {self.current_objective.description}")
                self.current_step = self.current_objective.get_next_step(self.strategy_manager.action_flags)
                self.logger.info(f"Première Step : {self.current_step.description}")
        self.execute_current_step()

    def check_detection_status(self) -> None:
        if self.moving_forward and not self.detection_manager.is_emergency_detection_front(True):
            self.logger.info("Fin détection avant")
            self.movement_manager.resume_asserv()
            self.something_detected = False
        elif not self.moving_forward and not self.detection_manager.is_emergency_detection_back(True):
            self.logger.info("Fin détection arrière")
            self.movement_manager.resume_asserv()
            self.something_detected = False

    def main_loop(self) -> None:
        self.logger.info("Début de la boucle principale")

        # Attente lancement du match en retirant la tirette
        self.logger.info("Attente lancement match")
        self.pull_cord.wait_for_state(False)

        # Lancement du match
        self.logger.info("Match lancé")
        self.chrono.start_match(self.match_end)
        self.nextion_display.goto_page("score")
        self.movement_manager.is_match_started = True
        self.execute_current_step()
        self.update_score()

        # Boucle principale
        while not self.interrupted:

            # Si pas d'obstacle détecté par les SRF
            if not self.something_detected:

                # On vérifie la détection courte portée des SRF
                if self.must_stop_from_emergency_detection():
                    continue

                # Si le pathfinding est en cours, on l'attends
                if self.astar_launch:
                    if self.pathfinding.computation_finished:
                        # Une fois le path trouvé, on l'exécute
                        self.logger.info("Astar terminé")
                        self.astar_launch = False
                        self.movement_manager.execute_movement(self.pathfinding.path)
                    else:
                        # On attend un peu avant de refaire un tour de boucle pour ne pas surcharger le CPU
                        time.sleep(0.01)
                else:
                    if self.current_step_ended():
                        # On passe à la strategy ou l'objectif suivant
                        self.update_step()
                    else:
                        if (self.movement_manager.asserv.asserv_status == AsservStatus.STATUS_BLOCKED
                                and (self.current_step.sub_type != StepSubType.GO or self.current_step.timeout == 0)):
                            self.logger.info("Asserv bloquée")
                            # todo faut faire un truc intelligent maintenant
                        elif (self.current_step.sub_type == StepSubType.GOTO_ASTAR
                              and self.detection_manager.is_trajectory_blocked(self.movement_manager.goto_queue)):
                            self.logger.info("Trajectoire bloquée, lancement nouveau calcul de trajectoire")
                            self.movement_manager.halt_asserv(False)
                            self.execute_current_step()

            # Si obstacle détecté par les SRF
            else:
                self.check_detection_status()

            if self.communication_manager is not None:
                # On check les communications serveurs
                self.communication_manager.read_from_server()

            # On laisse souffler le CPU mais pas trop
            time.sleep(0.001)

        self.logger.info("Fin de la boucle principale")
        self.logger.info(f"Score final : {self.score}")
        self.logger.info(f"Temps restant : {self.chrono}")