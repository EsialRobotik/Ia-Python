import logging
from typing import Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction
from ia.api.camera import Camera


@action_type("camera_init")
class ActionCameraInit(ThreadedAction):
    """Initialise le hardware camera. A lancer une fois au démarrage avant toute action camera."""

    def __init__(self, camera: Camera, flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.logger = logging.getLogger(__name__)
        self.camera = camera

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionCameraInit':
        camera = deps.get("camera")
        if camera is None:
            raise ValueError("camera dependency is required for camera_init action")
        return cls(camera)

    def _run(self) -> None:
        self.logger.info("Start camera initialization")
        self.camera.initialize()
        self.logger.info("Camera initialization finished")
        self._finished = True
