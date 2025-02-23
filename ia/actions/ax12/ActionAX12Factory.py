import json
from ia.actions.AbstractAction import AbstractAction
from ia.actions.ax12.ActionAX12DisableTorque import ActionAX12DisableTorque
from ia.actions.ax12.ActionAX12Position import ActionAX12Position
from ia.api.ax12.AX12 import AX12
from ia.api.ax12.AX12Position import AX12Position
from typing import Optional
from ia.api.ax12 import AX12LinkSerial

class ActionAX12Factory:
    @staticmethod
    def actionAx12FromJson(jsonObject: json, ax12Link: AX12LinkSerial) -> AbstractAction:
        if "type" in jsonObject:
            ax12ActionType = jsonObject["type"]
            if ax12ActionType == "position":
                if "angleRaw" in jsonObject:
                    position = AX12Position(jsonObject["angleRaw"])
                elif "angleDegree" in jsonObject:
                    position = AX12Position.buildFromDegrees(jsonObject["angleRaw"])
                else:
                    raise Exception("No 'angleRaw' nor 'angleDegree' property found in AX12 json of type position")
                return ActionAX12Position(ActionAX12Factory.ax12FromJson(jsonObject, ax12Link), position)
            elif ax12ActionType == "disableTorque":
                return ActionAX12DisableTorque(ActionAX12Factory.ax12FromJson(jsonObject, ax12Link))
            raise Exception(f"Unhandled AX12 json type {ax12ActionType}")
        raise Exception("Property 'type' not found in AX12 json")

    def ax12FromJson(jsonObject: json, ax12Link: AX12LinkSerial) -> AX12:
        if "id" in jsonObject:
            return AX12(jsonObject["id"], ax12Link)
        raise Exception("Property 'id' not found into AX12 action json config")