import time
from typing import Optional

from gpiozero import AngularServo

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction


@action_type("pwm_servo")
class ActionPwmServo(ThreadedAction):
    """Controle un servo PWM via GPIO."""

    def __init__(self, gpio: int, loop: bool, angles: list[int], flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.servo = AngularServo(
            pin=gpio,
            initial_angle=0,
            min_angle=-90,
            max_angle=90,
        )
        self.loop = loop
        self.angles = angles

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionPwmServo':
        return cls(
            gpio=int(payload['gpio']),
            loop=bool(payload['loop']),
            angles=payload['angles'],
            flags=payload.get('flags')
        )

    def execute(self) -> None:
        if self.loop:
            # une action en boucle est consideree comme terminee immediatement
            self._finished = True
        super().execute()

    def stop(self) -> None:
        super().stop()
        self.servo.stop()

    def reset(self) -> None:
        super().reset()
        self.servo.angle = 0

    def _run(self) -> None:
        while True:
            for angle in self.angles:
                if self._stop_requested:
                    return
                self.servo.angle = angle
                time.sleep(0.5)
            if not self.loop:
                break
        self._finished = True