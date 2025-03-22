from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.api.ax12.ax12_position import AX12Position
from ia.api.ax12.ax12_servo import AX12Servo


class ActionAX12Position(AbstractAction):
    """
    Class to represent an action that sets the position of an AX12 actuator.
    """

    def __init__(self, ax12: AX12Servo, angle: AX12Position) -> None:
        """
        Initialize the ActionAX12Position with an AX12 instance and a target angle.

        :param ax12: The AX12 instance to control.
        :param angle: The target angle for the AX12 actuator.
        """
        self.ax12 = ax12
        self.angle = angle
        self.executed = False
        self.command_sent = False

    def execute(self) -> None:
        """
        Execute the action by sending the position command to the AX12 actuator.
        """
        if self.finished():
            return None
        if not self.command_sent:
            self.command_sent = True
            self.ax12.set_servo_position(self.angle.getRawAngle())


    def finished(self) -> bool:
        """
        Check if the position action has finished executing.

        :return: True if the position action has finished executing, False otherwise.
        """
        if self.executed:
            return True
        if not self.command_sent:
            return False
        self.executed = self.ax12.is_moving() == False
        return self.executed

    def stop(self) -> None:
        """
        Stop the position action by disabling the torque of the AX12 actuator.
        """
        self.ax12.disable_torque()
        return None

    def reset(self) -> None:
        """
        Reset the position action so it can be re-executed with execute().
        """
        self.executed = False
        self.command_sent = False

    def get_flag(self) -> Optional[str]:
        """
        Retrieve the flag associated with the position action.

        :return: The flag associated with the position action, or None if no flag is set.
        """
        return None