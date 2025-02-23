import logging

from ia.asserv import Asserv, AsservStatus
from ia.step import StepSubType, Step
from ia.utils import Position


class MovementManager:
    def __init__(self, asserv: Asserv) -> None:
        """
        Initializes the MovementManager with an Asserv object

        Parameters
        ----------
        asserv : Asserv
        An instance of the Asserv class used for movement control.
        """
        self.asserv = asserv
        self.logger = logging.getLogger(__name__)
        self.goto_queue = []
        self.is_match_started = False
        self.current_step = None

    def execute_movement(self, trajectory: list[Position]) -> None:
        """
        Call for a goto solved by astar.

        Parameters
        ----------
        trajectory : list[Point]
            The trajectory to follow.
        """
        self.logger.info(f"executeMovement = {trajectory}")
        self.logger.info(f"isMatchStarted = {self.is_match_started}")
        self.goto_queue.clear()
        if len(trajectory) > 2:
            # Remove the first point which is the starting point and the last to finish on a precise goto
            for point in trajectory[1:len(trajectory) - 2]:
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
        self.logger.info(f"executeMovement goto_queue = {self.goto_queue}")

    def execute_step_deplacement(self, step: Step) -> None:
        """
        Executes a movement step based on the given step configuration.

        Parameters
        ----------
        step : Step
            The step configuration to execute.
        """
        self.current_step = step
        if step.sub_type == StepSubType.FACE:
            self.asserv.face(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.GO:
            self.asserv.go(step.distance)
            if step.timeout > 0:
                self.asserv.enable_low_speed(True)
                self.asserv.wait_for_halted_or_blocked(step.timeout)
                self.asserv.emergency_stop()
                self.asserv.emergency_reset()
                self.asserv.enable_low_speed(False)
        elif step.sub_type == StepSubType.GOTO:
            self.asserv.go_to(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.GOTO_BACK:
            self.asserv.go_to_reverse(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.GOTO_CHAIN:
            self.asserv.go_to_chain(Position(step.position.x, step.position.y))
        elif step.sub_type == StepSubType.SET_SPEED:
            self.asserv.set_speed(step.distance)

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
        if not temporary:
            self.goto_queue.clear()
        else:
            self.logger.info(f"goto_queue.size() = {len(self.goto_queue)} - self.asserv.get_queue_size() = {self.asserv.queue_size}")
            if len(self.goto_queue) > 0 and len(self.goto_queue) - self.asserv.queue_size > 0 and self.asserv.queue_size > 0:
                self.goto_queue = self.goto_queue[len(self.goto_queue) - self.asserv.queue_size:]
            self.logger.info(f"new goto_queue size = {len(self.goto_queue)}")
            self.logger.info(str(self.goto_queue))
        self.asserv.emergency_stop()
        if not temporary:
            self.asserv.stop()

    def resume_asserv(self) -> bool:
        """
        Resume the asserv. If the asserv was halted definitely it should not be restarted.

        Returns
        -------
        bool
            True if the resume was successful, False otherwise.
        """
        self.logger.info(f"resumeAsserv, goto_queue.size() = {len(self.goto_queue)}")
        self.asserv.emergency_reset()
        if len(self.goto_queue) > 0:
            self.execute_movement(list(self.goto_queue))
            # Wait a bit to ensure that the asserv has received at least one new command and is up to date
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
        is_finished: bool = self.asserv.queue_size == 0 and self.asserv.asserv_status == AsservStatus.STATUS_IDLE
        if is_finished:
            self.goto_queue.clear()
            self.current_step = None
        return is_finished

    def go_start(self, is_color0: bool) -> None:
        """
        Executes the goStart command on the asserv.

        Parameters:
        ----------
        is_color0 : bool
            Determines the starting configuration based on color.

        Returns:
        -------
        None
        """
        try:
            self.asserv.go_start(is_color0)
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