from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.actions.registry import action_type
from ia.api.ax12.ax12_position import AX12Position
from ia.api.ax12.ax12_servo import AX12Servo


@action_type("AX12")
class ActionAX12(AbstractAction):
    """Pilote un servo AX12 : position, disableTorque, complianceSlope, complianceMargin."""

    def __init__(self, servo: AX12Servo, command: str, params: dict, flags: Optional[list[str]] = None) -> None:
        self.servo = servo
        self.command = command
        self.params = params
        self.flags = flags
        self._executed = False
        self._command_sent = False

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionAX12':
        if "type" not in payload:
            raise ValueError("Property 'type' not found in AX12 json")
        if "id" not in payload:
            raise ValueError("Property 'id' not found in AX12 action json config")
        ax12_link = deps.get("ax12_link")
        servo = AX12Servo(payload["id"], ax12_link)
        return cls(servo, payload["type"], payload)

    def execute(self) -> None:
        if self._executed:
            return
        match self.command:
            case "position":
                if not self._command_sent:
                    self._command_sent = True
                    angle = self._parse_angle()
                    self.servo.set_servo_position(angle.getRawAngle())
            case "disableTorque":
                self.servo.disable_torque()
                self._executed = True
            case "complianceSlope":
                value = self.params["value"]
                self.servo.set_cw_compliance_slope(value)
                self.servo.set_ccw_compliance_slope(value)
                self._executed = True
            case "complianceMargin":
                value = self.params["value"]
                self.servo.set_cw_compliance_margin(value)
                self.servo.set_ccw_compliance_margin(value)
                self._executed = True
            case _:
                raise ValueError(f"Unhandled AX12 command type: {self.command}")

    def finished(self) -> bool:
        if self._executed:
            return True
        if self.command == "position" and self._command_sent:
            self._executed = not self.servo.is_moving()
            return self._executed
        return False

    def stop(self) -> None:
        if self.command == "position":
            self.servo.disable_torque()

    def reset(self) -> None:
        self._executed = False
        self._command_sent = False

    def get_flags(self) -> Optional[list[str]]:
        return self.flags

    def _parse_angle(self) -> AX12Position:
        if "angleDegree" in self.params:
            return AX12Position.buildFromDegrees(self.params["angleDegree"])
        elif "angleRaw" in self.params:
            return AX12Position(self.params["angleRaw"])
        raise ValueError("No 'angleRaw' nor 'angleDegree' property found in AX12 json of type position")