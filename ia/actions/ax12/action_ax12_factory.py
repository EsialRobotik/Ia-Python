import json

from ia.actions.abstract_action import AbstractAction
from ia.actions.ax12.action_ax12_disable_torque import ActionAX12DisableTorque
from ia.actions.ax12.action_ax12_position import ActionAX12Position
from ia.actions.ax12.action_ax12_compliance_margin import ActionAX12ComplianceMargin
from ia.actions.ax12.action_ax12_compliance_slope import ActionAX12ComplianceSlope
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.api.ax12.ax12_position import AX12Position
from ia.api.ax12.ax12_servo import AX12Servo


class ActionAX12Factory:
    """
    Factory class to create AX12 actions from JSON objects.
    """

    @staticmethod
    def action_ax12_from_json(json_object: json, ax12_link: AX12LinkSerial) -> AbstractAction:
        """
        Create an AX12 action from a JSON object.

        :param json_object: The JSON object containing the action configuration.
        :param ax12_link: The AX12LinkSerial instance to use for communication.
        :return: An instance of AbstractAction representing the AX12 action.
        """
        if "type" in json_object:
            ax12_action_type = json_object["type"]
            if ax12_action_type == "position":
                if "angleRaw" in json_object:
                    position = AX12Position(json_object["angleRaw"])
                elif "angleDegree" in json_object:
                    position = AX12Position.buildFromDegrees(json_object["angleDegree"])
                else:
                    raise Exception("No 'angleRaw' nor 'angleDegree' property found in AX12 json of type position")
                return ActionAX12Position(ActionAX12Factory.ax12_from_json(json_object, ax12_link), position)
            elif ax12_action_type == "disableTorque":
                return ActionAX12DisableTorque(ActionAX12Factory.ax12_from_json(json_object, ax12_link))
            elif ax12_action_type == "complianceSlope":
                if "value" not in json_object:
                    raise Exception("Property 'value' not found in AX12 compliance slope json")
                return ActionAX12ComplianceSlope(ActionAX12Factory.ax12_from_json(json_object, ax12_link), json_object["value"])
            elif ax12_action_type == "complianceMargin":
                if "value" not in json_object:
                    raise Exception("Property 'value' not found in AX12 compliance margin json")
                return ActionAX12ComplianceMargin(ActionAX12Factory.ax12_from_json(json_object, ax12_link), json_object["value"])
            raise Exception(f"Unhandled AX12 json type {ax12_action_type}")
        raise Exception("Property 'type' not found in AX12 json")

    @staticmethod
    def ax12_from_json(json_object: json, ax12_link: AX12LinkSerial) -> AX12Servo:
        """
        Create an AX12 instance from a JSON object.

        :param json_object: The JSON object containing the AX12 configuration.
        :param ax12_link: The AX12LinkSerial instance to use for communication.
        :return: An instance of AX12.
        """
        if "id" in json_object:
            return AX12Servo(json_object["id"], ax12_link)
        raise Exception("Property 'id' not found into AX12 action json config")