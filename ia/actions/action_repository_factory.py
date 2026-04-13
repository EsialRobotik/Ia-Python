import json
import logging
import os
from typing import Optional

from ia.actions.action_repository import ActionRepository
from ia.actions.registry import ACTION_TYPES
from ia.actions.serial_port import SerialPort
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.api.camera import Camera

# Importer le package types pour declencher l'enregistrement via @action_type
import ia.actions.types  # noqa: F401


class ActionRepositoryFactory:

    @staticmethod
    def from_json_files(
        folder: str,
        ax12_link_serial: Optional[AX12LinkSerial],
        serial_ports: Optional[dict[str, SerialPort]],
        camera: Optional[Camera] = None,
    ) -> ActionRepository:
        logger = logging.getLogger(__name__)
        action_repository = ActionRepository()
        actions_count = 0
        actions_alias_count = 0

        if not os.path.isdir(folder):
            raise FileNotFoundError(f"Actions folder not found: {folder}")

        deps = {
            "ax12_link": ax12_link_serial,
            "serial_ports": serial_ports or {},
            "action_repository": action_repository,
            "camera": camera,
        }

        for root, dirs, files in os.walk(folder):
            for file in files:
                if not file.endswith(".json"):
                    continue
                full_path = os.path.join(root, file)
                logger.info(f"loading {full_path}...")
                try:
                    with open(full_path) as f:
                        action_config = json.load(f)

                    action_id = file[:-5]
                    action_type_name = action_config.get("type")
                    if not action_type_name:
                        raise ValueError(f"Missing 'type' in {full_path}")

                    cls = ACTION_TYPES.get(action_type_name)
                    if cls is None:
                        raise ValueError(f"Unhandled action type: {action_type_name}")

                    action = cls.from_json(action_config.get("payload", {}), **deps)
                    action_repository.register_action(action_id, action)

                    if "alias" in action_config:
                        alias = action_config["alias"]
                        if action_repository.has_action(alias):
                            logger.warning(f"Action alias '{alias}' already exists and will be overridden by {full_path}")
                        else:
                            actions_alias_count += 1
                        action_repository.register_action(alias, action)

                    actions_count += 1
                except Exception as e:
                    logger.error(f"loading error for {full_path}: {e}")

        logger.info(f"Count of actions loaded from json files: {actions_count} ({actions_alias_count} alias)")
        return action_repository