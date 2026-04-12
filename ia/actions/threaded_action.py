import threading
from abc import abstractmethod
from typing import Optional

from ia.actions.abstract_action import AbstractAction


class ThreadedAction(AbstractAction):
    """Base pour toute action qui s'execute dans un thread daemon."""

    def __init__(self, flags: Optional[str] = None) -> None:
        self.flags = flags
        self._thread: Optional[threading.Thread] = None
        self._finished = False
        self._stop_requested = False

    def execute(self) -> None:
        if self._thread is not None:
            return
        self._finished = False
        self._stop_requested = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def finished(self) -> bool:
        return self._finished

    def stop(self) -> None:
        self._stop_requested = True

    def reset(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self.stop()
            self._thread.join()
        self._thread = None
        self._finished = False
        self._stop_requested = False

    def get_flag(self) -> Optional[str]:
        return self.flags

    @abstractmethod
    def _run(self) -> None:
        """Le travail reel de l'action. Doit mettre self._finished = True a la fin."""
        pass