import logging
import math
import time
from typing import Optional

from ia.asservissement.asserv import Asserv
from ia.asservissement.asserv_status import AsservStatus
from ia.asservissement.movement_direction import MovementDirection
from ia.strategy.step import Step
from ia.strategy.step_sub_type import StepSubType
from ia.utils.position import Position


class MovementManager:
    def __init__(self, asserv: Asserv, unblock_goto_config: Optional[dict] = None) -> None:
        """
        Initializes the MovementManager with an Asserv object

        Parameters
        ----------
        asserv : asserv
            An instance of the Asserv class used for movement control.
        unblock_goto_config : dict, optional
            Configuration for the GOTO/GOTO_BACK stuck-detection rescue maneuver.
            Recognized keys:
                - active (bool): enable/disable the feature (default True)
                - durationMs (int): time without progress before triggering rescue (default 1000)
                - movementThresholdMm (int): travel below this in the window counts as "not moving" (default 5)
                - recoveryDistanceMm (int): distance of the back-off go() (default 50)
                - maxAttempts (int): max consecutive rescue attempts before giving up (default 3)
                - recoveryTimeoutMs (int): timeout for the back-off go to complete (default 3000)
        """
        self.asserv = asserv
        self.logger = logging.getLogger(__name__)
        self.goto_queue = []
        self.is_match_started = False
        self.current_step = None

        cfg = unblock_goto_config or {}
        self.unblock_active: bool = bool(cfg.get('active', True))
        self.unblock_duration_ms: int = int(cfg.get('durationMs', 1000))
        self.unblock_movement_threshold_mm: int = int(cfg.get('movementThresholdMm', 5))
        self.unblock_recovery_distance_mm: int = int(cfg.get('recoveryDistanceMm', 50))
        self.unblock_max_attempts: int = int(cfg.get('maxAttempts', 3))
        self.unblock_recovery_timeout_ms: int = int(cfg.get('recoveryTimeoutMs', 3000))

        # Active goto tracking (set when a precise GOTO/GOTO_BACK is in progress).
        self._active_goto_target: Optional[Position] = None
        self._active_goto_direction: MovementDirection = MovementDirection.NONE
        self._stuck_reference_position: Optional[Position] = None
        self._stuck_window_start_ts: Optional[float] = None
        self._unblock_attempts: int = 0

    def current_position(self) -> Position:
        """
        Get the current position of the robot.

        Returns
        -------
        position
            The current position of the robot.
        """
        return self.asserv.position

    def execute_movement(self, trajectory: list[Position]) -> None:
        """
        Call for a goto solved by astar.

        Parameters
        ----------
        trajectory : list[Point]
            The trajectory to follow.
        """
        self.logger.info(f"executeMovement = [{', '.join(str(p) for p in trajectory)}]")
        self.logger.info(f"isMatchStarted = {self.is_match_started}")
        self.goto_queue.clear()
        if len(trajectory) > 2:
            # Remove the first point which is the starting point and the last to finish on a precise goto
            for point in trajectory[1:-1]:
                self.goto_queue.append(point)
                if self.is_match_started:
                    self.asserv.go_to_chain(Position(point.x, point.y))
                    try:
                        import time
                        time.sleep(0.01)
                    except InterruptedError as e:
                        self.logger.error(e)
        if len(trajectory) > 0:
            last_point = trajectory[-1]
            self.goto_queue.append(last_point)
            if self.is_match_started:
                self.asserv.go_to(Position(last_point.x, last_point.y))
                self._arm_unblock_tracking(Position(last_point.x, last_point.y), MovementDirection.FORWARD)
        self.logger.info(f"executeMovement goto_queue = [{', '.join(str(p) for p in self.goto_queue)}]")

    def execute_step_deplacement(self, step: Step) -> None:
        """
        Executes a movement strategy based on the given strategy configuration.

        Parameters
        ----------
        step : step
            The strategy configuration to execute.
        """
        self.current_step = step
        if step.sub_type == StepSubType.FACE:
            self.asserv.face(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.GO:
            if step.timeout > 0:
                self.asserv.enable_low_speed(True)
            self.asserv.go(step.distance)
            if step.timeout > 0:
                self.asserv.wait_for_halted_or_blocked(step.timeout)
                self.asserv.emergency_stop()
                self.asserv.emergency_reset()
                self.asserv.enable_low_speed(False)
        elif step.sub_type == StepSubType.GOTO:
            self.asserv.go_to(Position(step.position.x, step.position.y))
            self._arm_unblock_tracking(Position(step.position.x, step.position.y), MovementDirection.FORWARD)
        elif step.sub_type == StepSubType.GOTO_BACK:
            self.asserv.go_to_reverse(Position(step.position.x, step.position.y))
            self._arm_unblock_tracking(Position(step.position.x, step.position.y), MovementDirection.BACKWARD)
        elif step.sub_type == StepSubType.GOTO_CHAIN:
            self.asserv.go_to_chain(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.SET_SPEED:
            self.asserv.set_speed(step.distance)
        elif step.sub_type == StepSubType.SET_POSITION:
            self.asserv.set_odometrie(step.position.x, step.position.y, step.distance)
        elif step.sub_type == StepSubType.ORBITAL_TURN:
            self.asserv.orbital_turn(step.distance, step.forward, step.on_right_wheel)

    def halt_asserv(self, temporary: bool) -> None:
        """
        Halts the Asserv system.

        Parameters
        ----------
        temporary : bool
            If True, the halt is temporary and the queue is adjusted accordingly.
            If False, the queue is cleared and the system is stopped.
        """
        self.logger.info(f"haltAsserv, goto_queue.size() = {len(self.goto_queue)} - temporary = {temporary}")
        self._clear_unblock_tracking()
        if not temporary:
            self.goto_queue.clear()
        else:
            self.logger.info(f"goto_queue.size() = {len(self.goto_queue)} - self.asservissement.get_queue_size() = {self.asserv.queue_size}")
            if len(self.goto_queue) > 0 and len(self.goto_queue) - self.asserv.queue_size > 0 and self.asserv.queue_size > 0:
                self.goto_queue = self.goto_queue[len(self.goto_queue) - self.asserv.queue_size:]
            self.logger.info(f"new goto_queue size = {len(self.goto_queue)}")
            self.logger.info(f"[{', '.join(str(p) for p in self.goto_queue)}]")
        self.asserv.emergency_stop()

    def resume_asserv(self) -> bool:
        """
        Resume the asservissement. If the asservissement was halted definitely it should not be restarted.

        Returns
        -------
        bool
            True if the resume was successful, False otherwise.
        """
        self.logger.info(f"resumeAsserv, goto_queue.size() = {len(self.goto_queue)}")
        self.asserv.emergency_reset()
        if len(self.goto_queue) > 0:
            self.execute_movement(list(self.goto_queue))
            # Wait a bit to ensure that the asservissement has received at least one new command and is up to date
            try:
                import time
                time.sleep(0.2)
            except InterruptedError as e:
                self.logger.error(e)
            return True
        else:
            if self.current_step is not None:
                self.execute_step_deplacement(self.current_step)
            return False

    def is_last_ordered_movement_ended(self) -> bool:
        """
        Checks if the last ordered movement has ended.

        Returns:
        -------
        bool
            True if the last ordered movement has ended, False otherwise.
        """
        is_finished: bool = self.asserv.is_last_command_finished()
        if is_finished:
            self.goto_queue.clear()
            self.current_step = None
            self._clear_unblock_tracking()
        return is_finished

    def go_start(self, color: str) -> None:
        """
        Executes the goStart command on the asservissement.

        Parameters:
        ----------
        color : str
            Determines the starting configuration based on color.

        Returns:
        -------
        None
        """
        try:
            self.asserv.go_start(color)
        except Exception as e:
            self.logger.error(e)

    def is_blocked(self) -> bool:
        """
        Checks if the robot is blocked.

        Returns:
        -------
        bool
            True if the robot is blocked, False otherwise.
        """
        return (self.asserv.asserv_status == AsservStatus.STATUS_BLOCKED
            and self.current_step.sub_type != StepSubType.GO
            and self.current_step.timeout == 0)

    def _arm_unblock_tracking(self, target: Position, direction: MovementDirection) -> None:
        """
        Arms the stuck-goto detection for the given precise GOTO/GOTO_BACK target.
        """
        if not self.unblock_active:
            return
        self._active_goto_target = target
        self._active_goto_direction = direction
        self._stuck_reference_position = Position(self.asserv.position.x, self.asserv.position.y)
        self._stuck_window_start_ts = time.monotonic()
        self._unblock_attempts = 0

    def _clear_unblock_tracking(self) -> None:
        self._active_goto_target = None
        self._active_goto_direction = MovementDirection.NONE
        self._stuck_reference_position = None
        self._stuck_window_start_ts = None
        self._unblock_attempts = 0

    def check_stuck_goto(self) -> None:
        """
        Detects when a precise GOTO/GOTO_BACK is stuck near its target (typically because
        of a small lateral offset the robot cannot correct) and triggers a rescue maneuver:
        a short go() in the opposite direction followed by a re-issue of the original goto.

        Should be called regularly from the main loop while a movement is in progress.
        """
        if not self.unblock_active or self._active_goto_target is None:
            return
        # Only meaningful when the asserv is actively running a command.
        if self.asserv.asserv_status != AsservStatus.STATUS_RUNNING:
            return
        # Only watch the final precise goto: skip while any chain command is still pending
        # behind the current one (the firmware reports only commands queued *after* the current
        # one, so queue_size == 0 means the final go_to is the one being executed).
        if self.asserv.queue_size > 0:
            self._stuck_reference_position = Position(self.asserv.position.x, self.asserv.position.y)
            self._stuck_window_start_ts = time.monotonic()
            return

        current = self.asserv.position
        ref = self._stuck_reference_position
        if ref is None or self._stuck_window_start_ts is None:
            self._stuck_reference_position = Position(current.x, current.y)
            self._stuck_window_start_ts = time.monotonic()
            return

        delta = math.hypot(current.x - ref.x, current.y - ref.y)
        if delta > self.unblock_movement_threshold_mm:
            # Robot is still progressing — slide the window forward.
            self._stuck_reference_position = Position(current.x, current.y)
            self._stuck_window_start_ts = time.monotonic()
            return

        elapsed_ms = (time.monotonic() - self._stuck_window_start_ts) * 1000.0
        if elapsed_ms < self.unblock_duration_ms:
            return

        # Stuck for long enough → rescue.
        self._attempt_unblock_recovery()

    def _attempt_unblock_recovery(self) -> None:
        target = self._active_goto_target
        direction = self._active_goto_direction
        if target is None or direction == MovementDirection.NONE:
            return

        if self._unblock_attempts >= self.unblock_max_attempts:
            self.logger.warning(
                f"[UNBLOCK] Abandon : {self._unblock_attempts} tentatives sans succès "
                f"vers {target} (position courante {self.asserv.position})"
            )
            self._clear_unblock_tracking()
            return

        self._unblock_attempts += 1
        # Opposite direction: GOTO (FORWARD) → recule, GOTO_BACK (BACKWARD) → avance.
        rescue_distance = (-self.unblock_recovery_distance_mm
                           if direction == MovementDirection.FORWARD
                           else self.unblock_recovery_distance_mm)

        self.logger.warning(
            f"[UNBLOCK] Goto bloqué près de {target} (position {self.asserv.position}, "
            f"direction {direction.name}). Tentative #{self._unblock_attempts}/"
            f"{self.unblock_max_attempts} : arrêt asserv, go({rescue_distance}) puis renvoi du goto."
        )

        # The original goto is still RUNNING in the firmware: any new command would be
        # queued behind it and never execute. Stop and reset to flush the firmware queue
        # before sending the rescue go(). NB: we deliberately bypass halt_asserv/resume_asserv
        # because those touch the Python goto_queue and clear the unblock tracking.
        self.asserv.emergency_stop()
        self.asserv.emergency_reset()

        self.asserv.go(rescue_distance)
        self.asserv.wait_for_halted_or_blocked(self.unblock_recovery_timeout_ms)
        # If the rescue go is still running after the timeout, stop it cleanly so the
        # following goto starts from a settled state.
        if self.asserv.asserv_status == AsservStatus.STATUS_RUNNING:
            self.logger.warning("[UNBLOCK] Recul non terminé dans le délai, arrêt forcé avant renvoi du goto.")
            self.asserv.emergency_stop()
            self.asserv.emergency_reset()

        if direction == MovementDirection.FORWARD:
            self.asserv.go_to(target)
        else:
            self.asserv.go_to_reverse(target)

        # Restart the stuck-detection window from the post-recovery position.
        self._stuck_reference_position = Position(self.asserv.position.x, self.asserv.position.y)
        self._stuck_window_start_ts = time.monotonic()

        self.logger.info(f"[UNBLOCK] Goto vers {target} renvoyé après tentative #{self._unblock_attempts}.")