import json
import logging
import os

from ia.actions.action_list import ActionList
from ia.actions.action_repository import ActionRepository
from ia.actions.action_wait import ActionWait
from ia.actions.actuators.actuator_action_factory import ActuatorActionFactory
from ia.actions.actuators.actuator_link_repository import ActuatorLinkRepository
from ia.actions.ax12.action_ax12_factory import ActionAX12Factory
from ia.api.ax12.ax12_link_serial import AX12LinkSerial


class ActionRepositoryFactory:
    """
    Factory class to create an ActionRepository from various sources.
    """

    @staticmethod
    def from_json_files(folder: str, ax12_link_serial: AX12LinkSerial, actuator_link_repository: ActuatorLinkRepository) -> ActionRepository:
        """
        Read all actions json found into the given folder and put them into an ActionRepository object
        """
        logger = logging.getLogger(__name__)
        actions = dict()
        actions_count = 0
        actions_alias_count = 0
        action_repository = ActionRepository(dict())
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    logger.info(f"loading {full_path}...")
                    with open(full_path) as action_file:
                        try:
                            action_id_long = file[:-5]
                            action_config = json.load(action_file)
                            action_file.close()

                            if "type" in action_config:
                                action_type = action_config["type"]
                                match action_type:
                                    case "AX12":
                                        ax12_action = ActionAX12Factory.action_ax12_from_json(action_config["payload"], ax12_link_serial)
                                        actions[action_id_long] = ax12_action
                                    case "wait":
                                        if "duration" in action_config["payload"]:
                                            actions[action_id_long] = ActionWait(action_config["payload"]["duration"], None)
                                        else:
                                            raise Exception(f"'duration' not found in wait action config payload")
                                    case "list":
                                        if "list" in action_config["payload"]:
                                            action_list = ActionList(action_repository, action_config["payload"]["list"], None)
                                            actions[action_id_long] = action_list
                                        else:
                                            raise Exception(f"'list' not found in list action config payload")
                                    case "actuator":
                                        actions[action_id_long] = ActuatorActionFactory.action_actuator_from_json(action_config["payload"], actuator_link_repository)
                                    case default:
                                        raise Exception(f"Unhandled action type : {action_type}")
                            if "alias" in action_config:
                                action_alias = action_config["alias"]
                                if action_alias in actions:
                                    logger.warning(f"Action alias '{action_alias}' already exists in action pool and will be ovveriden by action file {full_path}")
                                else:
                                    actions_alias_count += 1
                                actions[action_alias] = actions[action_id_long]
                            actions_count += 1
                        except Exception as e:
                            logger.error(f"loading error : {e}")

        logger.info(f"Count of actions loaded from json files : {actions_count} ({actions_alias_count} alias))")
        for action_id in actions.keys():
            action_repository.register_action(action_id, actions[action_id])

        # TODO déclencher la vérification des ActionList

        return action_repository