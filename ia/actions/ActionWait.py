from ia.actions.AbstractAction import AbstractAction
from ia.api.ax12.AX12 import AX12
from ia.api.ax12.AX12Position import AX12Position
from typing import Optional
from ia.actions.ActionRepository import ActionRepository
from typing import List
import threading
import time
import logging

class ActionWait(AbstractAction):

    def __init__(self, durationSeconds: float, flags: Optional[str]) -> None:
        self.logger = logging.getLogger(__name__)
        self.durationSeconds = durationSeconds
        self.flags = flags
        self.timerThread = None

    def execute(self) -> None:
        if self.timerThread == None:
            self.logger.debug(f"start waiting of {self.durationSeconds} second(s)")
            self.isFinished = False
            self.timerThread = threading.Timer(self.durationSeconds, self.timerEnd)
            self.timerThread.start()

    def finished(self) -> bool:
        return self.isFinished

    def stop(self) -> None:
        if not self.timerThread == None and self.timerThread.is_alive:
            self.timerThread.cancel()

    def reset(self) -> None:
        if self.timerThread == None:
            return
        if self.timerThread.is_alive:
            self.timerThread.cancel()
        self.timerThread = None

    def getFlag(self) -> Optional[str]:
        return self.flags

    def timerEnd(self):
        self.logger.debug(f"waiting finished")
        self.isFinished = True
    