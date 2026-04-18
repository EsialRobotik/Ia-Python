import logging
import time
from typing import Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction


@action_type("wait")
class ActionWait(ThreadedAction):

    def __init__(self, duration_ms: float, flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.logger = logging.getLogger(__name__)
        self.duration_ms = duration_ms

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionWait':
        if "durationMs" not in payload:
            raise ValueError("'durationMs' not found in wait action config payload")
        return cls(payload["durationMs"], payload.get("flags"))

    def _run(self) -> None:
        self.logger.info(f"start waiting of {self.duration_ms} millisecond(s)")
        deadline = time.time() + (self.duration_ms / 1000.)
        while time.time() < deadline and not self._stop_requested:
            time.sleep(0.01)
        self.logger.info("waiting finished")
        self._finished = True