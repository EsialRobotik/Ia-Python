from ia.actions.AbstractAction import AbstractAction
from ia.api.ax12.AX12 import AX12
from typing import Optional

class ActionAX12DisableTorque(AbstractAction):

    def __init__(self, ax12: AX12) -> None:
        self.ax12 = ax12
        self.executed = False

    def execute(self) -> None:
        self.ax12.disable_torque()
        self.executed = True
        pass

    def finished(self) -> bool:
        return self.executed

    def stop(self) -> None:
        return None

    def reset(self) -> None:
        self.executed = False

    def getFlag(self) -> Optional[str]:
        return None