import logging
from typing import Dict

from ia.api.communication_socket import CommunicationSocket
from ia.manager.action_manager import ActionManager
from ia.pathfinding.astar import AStar


class CommunicationManager:
    """
    Manages communication with the server and handles pathfinding and actions.

    This class is responsible for sending and receiving data to and from the server,
    managing pathfinding operations, and executing actions based on the received data.
    """

    def __init__(self, pathfinding: AStar, action_manager: ActionManager, comm_config: Dict) -> None:
        """
        Initializes the CommunicationManager with pathfinding, action manager, and communication configuration.

        Parameters
        ----------
        pathfinding : astar
            An instance of the Pathfinding class used for pathfinding operations.
        action_manager : action_manager
            An instance of the ActionManager class used for managing actions.
        comm_config : Dict
            A dictionary containing the communication configuration with keys "host" and "port".
        """
        self.pathfinding = pathfinding
        self.action_manager = action_manager
        self.communication_socket = CommunicationSocket(host=comm_config["host"], port=comm_config["port"])
        self.logger = logging.getLogger(__name__)

    def send_delete_zone(self, zone_id: str) -> None:
        """
        Sends a delete zone command to the hotspot socket.

        Parameters
        ----------
        zone_id : str
            The ID of the zone to delete.
        """
        self.send_hotspot_socket_data(f"delete-zone#{zone_id}")

    def send_add_zone(self, zone_id: str) -> None:
        """
        Sends an add zone command to the hotspot socket.

        Parameters
        ----------
        zone_id : str
            The ID of the zone to add.
        """
        self.send_hotspot_socket_data(f"add-zone#{zone_id}")

    def send_action_data(self, action_id: int, data: str) -> None:
        """
        Sends action data to the hotspot socket.

        Parameters
        ----------
        action_id : int
            The ID of the action.
        data : str
            The data to send with the action.
        """
        self.send_hotspot_socket_data(f"action-data#{action_id}#{data}")

    def send_hotspot_socket_data(self, data: str) -> None:
        """
        Sends data to the hotspot socket.

        Parameters
        ----------
        data : str
            The data to send.
        """
        try:
            self.logger.info(f"Send socket data: {data}")
            self.communication_socket.send_message(data)
        except Exception as e:
            self.logger.error("Socket error")
            self.logger.error(e)

    def read_from_server(self) -> None:
        """
        Reads data from the server and processes it.
        """
        data = self.communication_socket.last_message
        if data:
            data_split = data.split("#")
            if data_split[0] == "delete-zone":
                self.pathfinding.update_dynamic_zone(data_split[1], False)
            elif data_split[0] == "add-zone":
                self.pathfinding.update_dynamic_zone(data_split[1], True)
            elif data_split[0] == "action-data":
                self.action_manager.execute_command(data_split[1])