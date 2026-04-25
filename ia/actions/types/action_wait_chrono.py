import logging
import time
from typing import Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction
from ia.api.chrono import Chrono


@action_type("wait_chrono")
class ActionWaitChrono(ThreadedAction):

    def __init__(self, chrono: Chrono, target_seconds: int, flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.logger = logging.getLogger(__name__)
        self.chrono = chrono
        self.target_seconds = target_seconds

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionWaitChrono':
        chrono = deps.get("chrono")
        if chrono is None:
            raise ValueError("chrono dependency is required for wait_chrono action")
        if "targetSeconds" not in payload:
            raise ValueError("'targetSeconds' not found in wait_chrono action config payload")
        return cls(chrono, payload["targetSeconds"], payload.get("flags"))

    def _run(self) -> None:
        self.logger.info(f"Waiting for chrono to reach {self.target_seconds}s")
        while not self._stop_requested:
            if self.chrono.timestamp_start is not None and self.chrono.get_time_since_beginning() >= self.target_seconds:
                break
            time.sleep(0.01)
        self.logger.info(f"Chrono reached {self.target_seconds}s")
        self._finished = True