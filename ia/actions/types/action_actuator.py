import logging
from typing import Optional

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction
from ia.actions.serial_port import SerialPort


@action_type("actuator")
class ActionActuator(ThreadedAction):
    """Envoie une sequence de commandes texte a un actionneur via port serie."""

    def __init__(self, port: SerialPort, commands: list[dict], flags: Optional[list[str]] = None) -> None:
        super().__init__(flags)
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.commands = commands

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionActuator':
        if "actuatorLink" not in payload:
            raise ValueError("No 'actuatorLink' config found")
        link_id = payload["actuatorLink"]
        serial_ports = deps.get("serial_ports", {})
        if link_id not in serial_ports:
            raise ValueError(f"No serial port with id '{link_id}' found")
        if "commands" not in payload:
            raise ValueError("Command list 'commands' is empty in config")
        return cls(serial_ports[link_id], payload["commands"])

    def _run(self) -> None:
        for cmd in self.commands:
            if self._stop_requested:
                break
            command_str = cmd["command"]
            is_async = cmd.get("async", False)
            timeout = cmd.get("timeout")
            response = self.port.send(command_str, wait_response=not is_async, timeout=timeout)
            if not is_async and response != "ok":
                if not response:
                    self.logger.warning(f'Command "{command_str}" returned an unexpected empty response')
                else:
                    self.logger.warning(f'Command "{command_str}" returned an unexpected string: "{response}"')
        self._finished = True