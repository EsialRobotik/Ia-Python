import json
import logging

from ia.actions.actuators.actuator_link_repository import ActuatorLinkRepository
from ia.actions.actuators.serial_actuator_link import SerialActuatorLink


class ActuatorLinkRepositoryFactory:

    @staticmethod
    def serial_actuator_link_from_json(actuator_config: json):
        if not 'serialport' in actuator_config:
            raise "Missing 'serie' config key in serial actuator configuration"
        
        if not 'baudrate' in actuator_config:
            raise "Missing 'serie' config key in serial actuator configuration"
        
        return SerialActuatorLink(actuator_config['serialport'], actuator_config['baudrate'])

    @staticmethod
    def actuator_link_repository_from_json(actuators_links_config: json) -> ActuatorLinkRepository:
        logger = logging.getLogger(__name__)
        actuators_links = dict()
        index = -1
        for actuator_link_config in actuators_links_config:
            index += 1

            id = str(index)
            if not 'id' in actuator_link_config:
                 logger.warning(f'id is missing in actuator link config  #{index}, using default value "{id}"')
            else:
                id = actuator_link_config['id']

            actuator_type = actuator_link_config['type']
            try:
                if actuator_type == 'serial':
                    actuators_links[id] = ActuatorLinkRepositoryFactory.serial_actuator_link_from_json(actuator_link_config)
                else:
                    logger.warning(f'No factory found to handle actuator link of type "{actuator_type}"')
            except Exception as e:
                logger.warning(f"Error while building actuator link #{index}: {e}")
        return ActuatorLinkRepository(actuators_links)
