import logging
from typing import Dict, Optional

from ia.api.communication_socket import CommunicationSocket
from ia.manager.action_manager import ActionManager
from ia.manager.strategy_manager import StrategyManager
from ia.pathfinding.visibility_graph import VisibilityGraph


class CommunicationManager:
    """
    Manages communication with the server and handles pathfinding and actions.

    This class is responsible for sending and receiving data to and from the server,
    managing pathfinding operations, and executing actions based on the received data.
    """

    def __init__(self, action_manager: ActionManager, comm_config: Dict,
                 pathfinding: Optional[VisibilityGraph] = None,
                 strategy_manager: Optional[StrategyManager] = None) -> None:
        """
        Initializes the CommunicationManager with action manager, communication
        configuration and optionally pathfinding / strategy_manager instances.

        ``pathfinding`` et ``strategy_manager`` peuvent être ``None`` à la
        construction (pour ouvrir la socket très tôt, avant qu'ils n'existent)
        et seront renseignés ensuite via ``set_pathfinding`` /
        ``set_strategy_manager``.
        """
        self.pathfinding = pathfinding
        self.strategy_manager = strategy_manager
        self.action_manager = action_manager
        self.who = comm_config.get("who")
        self.communication_socket = CommunicationSocket(
            host=comm_config["host"],
            port=comm_config["port"],
            who=self.who,
        )
        self.logger = logging.getLogger(__name__)

    def set_pathfinding(self, pathfinding: VisibilityGraph) -> None:
        """Renseigne le pathfinding une fois construit (init différée)."""
        self.pathfinding = pathfinding

    def set_strategy_manager(self, strategy_manager: StrategyManager) -> None:
        """Renseigne le strategy_manager (init différée si besoin)."""
        self.strategy_manager = strategy_manager

    def send_color(self, color: str) -> None:
        """Annonce au serveur la couleur sélectionnée par le robot."""
        if not color:
            return
        self.send_hotspot_socket_data(f"color#{color}")

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

    def send_add_flag(self, flag: str) -> None:
        """Demande aux autres robots d'ajouter un action_flag à leur stratégie."""
        if not flag:
            return
        self.send_hotspot_socket_data(f"add-flag#{flag}")

    def send_delete_flag(self, flag: str) -> None:
        """Demande aux autres robots de retirer un action_flag de leur stratégie."""
        if not flag:
            return
        self.send_hotspot_socket_data(f"delete-flag#{flag}")

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
            if data_split[0] == "delete-zone" and self.pathfinding is not None:
                self.pathfinding.update_dynamic_zone(data_split[1], False)
            elif data_split[0] == "add-zone" and self.pathfinding is not None:
                self.pathfinding.update_dynamic_zone(data_split[1], True)
            elif data_split[0] == "action-data":
                self.action_manager.execute_command(data_split[1])
            elif data_split[0] == "add-flag" and self.strategy_manager is not None:
                self.strategy_manager.add_action_flag(data_split[1])
            elif data_split[0] == "delete-flag" and self.strategy_manager is not None:
                self.strategy_manager.remove_action_flag(data_split[1])