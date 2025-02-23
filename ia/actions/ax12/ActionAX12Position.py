from ia.actions.AbstractAction import AbstractAction
from ia.api.ax12.AX12 import AX12
from ia.api.ax12.AX12Position import AX12Position
from typing import Optional

class ActionAX12Position(AbstractAction):

    def __init__(self, ax12: AX12, angle: AX12Position) -> None:
        self.ax12 = ax12
        self.angle = angle
        self.executed = False
        self.commandSent = False

    def execute(self) -> None:
        if (self.finished()):
            return None
        if self.commandSent == False:
            self.commandSent = True
            self.ax12.set_servo_position(self.angle.getRawAngle())


    def finished(self) -> bool:
        if self.executed:
            return True
        if (self.commandSent == False):
            return False
        self.executed = self.ax12.is_moving() == False
        return self.executed

    def stop(self) -> None:
        # TODO asservir l'AX12 à  sa position courante ?
        return None

    def reset(self) -> None:
        self.executed = False
        self.commandSent = False

    def getFlag(self) -> Optional[str]:
        return None