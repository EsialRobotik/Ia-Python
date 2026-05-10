"""
État partagé du RabbitControlCenter exposé via signaux Qt.

Les workers réseau / série émettent des signaux que l'UI consomme :
- robot_state_changed : un robot s'est connecté, déconnecté, ou a changé de couleur
- log_record / log_record_parsed : nouvelle ligne de log reçue
- match_started : un robot a annoncé "Match lancé"
- switches_changed : nouvelle trame des 12 interrupteurs
"""

from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QObject, Signal


# Nombre d'interrupteurs et étiquettes (bp1..bp4 puis sw1..sw8)
SWITCH_LABELS: list[str] = [f"bp{i + 1}" for i in range(4)] + [f"sw{i + 1}" for i in range(8)]
SWITCH_COUNT = len(SWITCH_LABELS)


@dataclass
class RobotState:
    robot_id: str
    connected: bool = False
    color: Optional[str] = None  # nom de couleur (ex. "jaune", "bleu")


@dataclass
class ControlCenterModel:
    robots: dict[str, RobotState] = field(default_factory=dict)
    switches: list[bool] = field(default_factory=lambda: [False] * SWITCH_COUNT)
    match_started: bool = False


class ControlCenterState(QObject):
    """Hub Qt centralisant les signaux d'événements des workers."""

    robot_state_changed = Signal(str)              # robot_id
    log_record = Signal(str)                        # ligne formatée
    log_record_parsed = Signal(str, str, str, str)  # ts, who, level, message
    match_started = Signal()
    switches_changed = Signal(list)                 # list[bool] de taille SWITCH_COUNT

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.model = ControlCenterModel()

    # --- Robots ---------------------------------------------------------------

    def _ensure_robot(self, robot_id: str) -> RobotState:
        robot = self.model.robots.get(robot_id)
        if robot is None:
            robot = RobotState(robot_id=robot_id)
            self.model.robots[robot_id] = robot
        return robot

    def set_robot_connected(self, robot_id: str, connected: bool) -> None:
        robot = self._ensure_robot(robot_id)
        if robot.connected == connected:
            return
        robot.connected = connected
        if not connected:
            robot.color = None
        self.robot_state_changed.emit(robot_id)

    def set_robot_color(self, robot_id: str, color: str) -> None:
        robot = self._ensure_robot(robot_id)
        if robot.color == color:
            return
        robot.color = color
        self.robot_state_changed.emit(robot_id)

    # --- Switches -------------------------------------------------------------

    def set_switches(self, values: list[bool]) -> None:
        if len(values) != SWITCH_COUNT:
            return
        if self.model.switches == values:
            return
        self.model.switches = list(values)
        self.switches_changed.emit(list(values))

    # --- Match ----------------------------------------------------------------

    def declare_match_started(self) -> None:
        if self.model.match_started:
            return
        self.model.match_started = True
        self.match_started.emit()

    def reset_match(self) -> None:
        self.model.match_started = False
