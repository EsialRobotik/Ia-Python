import math

from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position
from strategy.enum.mirror import Mirror
from strategy.task.abstract_task import AbstractTask


class OrbitalTurn(AbstractTask):

    def __init__(self, desc: str, degrees: float, pivot_offset: float, forward: bool = True, on_right_wheel: bool = True, mirror: Mirror = Mirror.MIRRORY):
        super().__init__(
            desc=desc,
            dist=degrees,
            task_type=StepType.MOVEMENT,
            subtype=StepSubType.ORBITAL_TURN,
            mirror=mirror,
            forward=forward,
            on_right_wheel=on_right_wheel
        )
        self.pivot_offset = pivot_offset

    def execute(self, start_point: Position):
        theta = start_point.theta
        angle_rad = math.radians(self.dist)

        # Le pivot est sur la roue codeuse droite ou gauche (axe Y local du robot)
        if self.on_right_wheel:
            pivot_x = start_point.x + self.pivot_offset * math.sin(theta)
            pivot_y = start_point.y - self.pivot_offset * math.cos(theta)
            rot = -angle_rad if self.forward else angle_rad
        else:
            pivot_x = start_point.x - self.pivot_offset * math.sin(theta)
            pivot_y = start_point.y + self.pivot_offset * math.cos(theta)
            rot = angle_rad if self.forward else -angle_rad

        # Position relative du robot par rapport au pivot
        dx = start_point.x - pivot_x
        dy = start_point.y - pivot_y

        # Appliquer la rotation
        new_x = pivot_x + dx * math.cos(rot) - dy * math.sin(rot)
        new_y = pivot_y + dx * math.sin(rot) + dy * math.cos(rot)
        new_theta = theta + rot

        self.end_point = Position(int(new_x), int(new_y), new_theta)
        return {
            "task": self.desc,
            "command": f"orbital-turn#{self.dist};{1 if self.forward else 0};{1 if self.on_right_wheel else 0}",
            "position": self.end_point.to_dict()
        }