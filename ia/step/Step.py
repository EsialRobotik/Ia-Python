from typing import Dict

from ia.step.StepSubType import StepSubType
from ia.step.StepType import StepType
from ia.utils import Position


class Step:
    """
    Represents a step in a process with various attributes and configurations.

    Attributes
    ----------
    description : str
        Description of the step.
    step_id : int
        Identifier of the step.
    id_action : int
        Identifier of the action associated with the step.
    action_type : StepType
        Type of the action.
    sub_type : StepSubType, optional
        Subtype of the action, if applicable.
    distance : int, optional
        Distance associated with the step, default is 0.
    timeout : int, optional
        Timeout for the step, default is 0.
    position : Position, optional
        Position associated with the step, default is (0, 0).
    item_id : int, optional
        Identifier of the item, if applicable.
    y_positive_exclusive : bool, optional
        Flag indicating if the step is exclusive to positive Y coordinates, default is False.
    y_negative_exclusive : bool, optional
        Flag indicating if the step is exclusive to negative Y coordinates, default is False.
    skip_flag : str, optional
            Flag indicating if the step should be skipped, default is None.
    needed_flag : str, optional
        Flag needed to execute the step, default is None.
    action_flag : str, optional
        Flag raised when step is finished, default is None.
    """

    def __init__(self, config_node: Dict):
        """
        Represents a step in a process with various attributes and configurations.

        Attributes
        ----------
        config_node : Dict
            Dictionary containing the configuration for the objective.
        """

        self.description = config_node["description"]
        self.step_id = config_node["id"]
        self.id_action = config_node["actionId"]

        self.action_type = config_node["type"].upper()
        if not self.action_type in StepType:
            raise ValueError(f"Unknown action type: {self.action_type}")

        if "subtype" in config_node:
            self.sub_type = config_node["subtype"].upper()
            if not self.sub_type in StepSubType:
                raise ValueError(f"Unknown subtype: {self.sub_type}")
        else:
            self.sub_type = None
        self.distance = config_node.get("dist", 0)
        self.timeout = config_node.get("timeout", 0)
        self.position = Position(config_node.get("positionX", 0), config_node.get("positionY", 0))
        self.distance = config_node.get("dist", 0)
        self.item_id = config_node.get("itemId", None)
        self.y_positive_exclusive = config_node.get("yPositiveExclusive", None)
        self.y_negative_exclusive = config_node.get("yNegativeExclusive", None)

        self.skip_flag = config_node.get("skipFlag", None)
        self.needed_flag = config_node.get("neededFlag", None)
        self.action_flag = config_node.get("actionFlag", None)

    def __str__(self):
        return (f"Step{{desc='{self.description}', step_id={self.step_id}, id_action={self.id_action}, "
                f"position={self.position}, action_type={self.action_type}, sub_type={self.sub_type}, "
                f"distance={self.distance}, y_positive_exclusive={self.y_positive_exclusive}, "
                f"y_negative_exclusive={self.y_negative_exclusive}}}")