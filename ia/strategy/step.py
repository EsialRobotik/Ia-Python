from typing import Dict

from ia.strategy.step_sub_type import StepSubType
from ia.strategy.step_type import StepType
from ia.utils.position import Position


class Step:
    """
    Represents a strategy in a process with various attributes and configurations.

    Attributes
    ----------
    description : str
        Description of the strategy.
    id_action : int
        Identifier of the action associated with the strategy.
    action_type : StepType
        Type of the action.
    sub_type : StepSubType, optional
        Subtype of the action, if applicable.
    distance : int, optional
        Distance associated with the strategy, default is 0.
    timeout : int, optional
        Timeout for the strategy, default is 0.
    position : Position, optional
        Position associated with the strategy, default is (0, 0).
    item_id : int, optional
        Identifier of the item, if applicable.
    skip_flag : str, optional
            Flag indicating if the strategy should be skipped, default is None.
    needed_flag : str, optional
        Flag needed to execute the strategy, default is None.
    """

    def __init__(self, config_node: Dict):
        """
        Represents a strategy in a process with various attributes and configurations.

        Attributes
        ----------
        config_node : Dict
            Dictionary containing the configuration for the objective.
        """

        self.description = config_node["desc"]
        self.id_action = config_node["action_id"]

        self.action_type = config_node["type"].upper()
        if not self.action_type in StepType._value2member_map_:
            raise ValueError(f"Unknown action type: {self.action_type}")

        if "subtype" in config_node:
            self.sub_type = config_node["subtype"].upper()
            if not self.sub_type in StepSubType._value2member_map_:
                raise ValueError(f"Unknown subtype: {self.sub_type}")
        else:
            self.sub_type = None
        self.distance = config_node.get("dist", 0)
        self.timeout = config_node.get("timeout", 0)
        self.position = Position(config_node.get("position_x", 0), config_node.get("position_y", 0))
        self.distance = config_node.get("dist", 0)
        self.item_id = config_node.get("item_id", None)

        self.skip_flag = config_node.get("skip_flag", None)
        self.needed_flag = config_node.get("needed_flag", None)

    def __str__(self):
        return (f"Step{{desc='{self.description}', id_action={self.id_action}, "
                f"position={self.position}, action_type={self.action_type}, sub_type={self.sub_type}, "
                f"distance={self.distance}}}")