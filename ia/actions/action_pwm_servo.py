import threading
import time
from typing import Optional

from gpiozero import AngularServo

from ia.actions.abstract_action import AbstractAction


class ActionPwmServo(AbstractAction):
    """"
    Class to represent a PwmServo action.
    """
    def __init__(self, gpio: int, loop: bool, angles: list[int], flags: Optional[str]) -> None:
        self.servo = AngularServo(
            pin=gpio,
            initial_angle=0,
            min_angle=-90,
            max_angle=90,
        )
        self.loop = loop
        self.flags = flags
        self.is_finished = loop # a loop must return immediately
        self.angles = angles
        self.thread = None

    @staticmethod
    def from_json(json_data: dict) -> 'ActionPwmServo':
        return ActionPwmServo(
            gpio=int(json_data['gpio']),
            loop=bool(json_data['loop']),
            angles=json_data['angles'],
            flags=json_data.get('flags')
        )
    
    def execute(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        for angle in self.angles:
            self.servo.angle = angle
            time.sleep(0.5)
        if self.loop:
            self._run()
        self.is_finished = True

    def finished(self) -> bool:
        return self.is_finished

    def stop(self) -> None:
        self.servo.stop()

    def reset(self) -> None:
        self.servo.angle = 0
        self.is_finished = self.loop 

    def get_flag(self) -> Optional[str]:
        return self.flags