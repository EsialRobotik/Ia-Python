from ia.actions.actuators.AbstractActuatorLink import AbstractActuatorLink

class ActuatorLinkRepository:
    """
    Class to manage a repository of actuator links.
    """

    def __init__(self, actuator_link_list: dict[str, AbstractActuatorLink]):
        """
        Initialize the ActuatorLinkRepository with a dictionary of actuator links.

        :param actuator_link_list: A dictionary where the keys are actuator link IDs and the values are AbstractActuatorLink instances.
        """
        self.actuator_link_list = actuator_link_list
    
    def has_actuator_link(self, actuator_link_id: str) -> bool:
        """
        Check if the actuator links repository contains an actuator link with the given ID.

        :param actuator_link_id: The ID of the actuator link to check.
        :return: True if the actuator link exists in the repository, False otherwise.
        """
        return actuator_link_id in self.actuator_link_list

    def get_actuator_link(self, actuator_link_id: str) -> AbstractActuatorLink:
        """
        Retrieve an actuator link from the repository by its ID.

        :param actuator_link_id: The ID of the actuator link to retrieve.
        :return: The AbstractActuatorLink instance associated with the given ID.
        :raises KeyError: If the actuator link ID is not found in the repository.
        """
        if actuator_link_id in self.actuator_link_list:
            return self.actuator_link_list[actuator_link_id]
        else:
            raise f'Actuator link id {actuator_link_id} not found in actuators link collection'

    def register_actuator_link(self, actuator_link_id: str, actuator_link: AbstractActuatorLink) -> None:
        """
        Register a new actuator link in the repository.

        :param actuator_link_id: The ID of the actuator link to register.
        :param actuator_link: The AbstractActuatorLink instance to register.
        """
        self.actuator_link_list[actuator_link_id] = actuator_link