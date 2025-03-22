import json
import logging

from ia.actions.actuators.action_actuator import ActionActuator
from ia.actions.actuators.actuator_command import ActuatorCommand
from ia.actions.actuators.actuator_link_repository import ActuatorLinkRepository


class ActuatorActionFactory:

    @staticmethod
    def action_actuator_from_json(actuator_config: json, actuator_link_repository: ActuatorLinkRepository) -> ActionActuator:
        logger = logging.getLogger(__name__)
        if not 'actuatorLink' in actuator_config:
            raise Exception("No 'actuatorLink' config found")
        actuator_link_id = actuator_config['actuatorLink']
        if not actuator_link_repository.has_actuator_link(actuator_link_id):
            raise Exception(f"No 'actuatorLink' with value '{actuator_link_id}' in ActuatorLinkRepository")

        if not 'commands' in actuator_config:
            raise Exception(f"Command list 'commands' is empty in config")
    
        commandlist = []
        for actuator_command_config in actuator_config['commands']:
            commandlist.append(ActuatorActionFactory.actuator_command_from_json(actuator_command_config))
        return ActionActuator(actuator_link_repository.get_actuator_link(actuator_link_id), commandlist, None)

    
    @staticmethod
    def actuator_command_from_json(command_config: json) -> ActuatorCommand:
        command = command_config['command']
        isasync = False
        if 'async' in command_config:
            isasync = command_config['async']
        timeout = None
        if 'timeout' in command_config:
            timeout = command_config['timeout']
        return ActuatorCommand(command, isasync, timeout)