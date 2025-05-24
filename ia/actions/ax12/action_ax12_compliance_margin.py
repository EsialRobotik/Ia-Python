from typing import Optional

from ia.actions.abstract_action import AbstractAction
from ia.api.ax12.ax12_servo import AX12Servo


class ActionAX12ComplianceMargin(AbstractAction):
    """
    Class to represent an action that disables the torque of an AX12 actuator.
    """

    def __init__(self, ax12: AX12Servo, value: int) -> None:
        """
        Initialize the ActionAX12DisableTorque with an AX12 instance.

        :param ax12: The AX12 instance to disable torque on.
        :param value: The value of the compliance margin.
        """
        self.ax12 = ax12
        self.executed = False
        self.value = value

    def execute(self) -> None:
        """
        Initialize the ActionAX12DisableTorque with an AX12 instance.

        :param ax12: The AX12 instance to disable torque on.
        """
        self.ax12.set_cw_compliance_margin(self.value)
        self.ax12.set_ccw_compliance_margin(self.value)
        self.executed = True
        pass

    def finished(self) -> bool:
        """
        Check if the torque disable action has finished executing.

        :return: True if the torque disable action has finished executing, False otherwise.
        """
        return self.executed

    def stop(self) -> None:
        """
        Stop the torque disable action if it is currently running.
        """
        return None

    def reset(self) -> None:
        """
        Reset the torque disable action so it can be re-executed with execute().
        """
        self.executed = False

    def get_flag(self) -> Optional[str]:
        """
        Retrieve the flag associated with the torque disable action.

        :return: The flag associated with the torque disable action, or None if no flag is set.
        """
        return None