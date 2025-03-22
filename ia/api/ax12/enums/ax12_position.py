class AX12Position:
    """
    Represents the position of an AX12 servo motor.

    Attributes:
        MINIMUM_ANGLE_INT (int): The minimum angle in integer representation.
        MAXIMUM_ANGLE_INT (int): The maximum angle in integer representation.
        MINIMUM_ANGLE_DEGREES (float): The minimum angle in degrees.
        MAXIMUM_ANGLE_DEGREES (float): The maximum angle in degrees.

    Methods:
        __init__(raw_angle: int) -> None:
            Initializes the AX12Position object with a raw angle.

        build_from_degrees(angle: float) -> 'AX12Position':
            Creates an AX12Position object from an angle in degrees.

        build_from_int(angle: int) -> 'AX12Position':
            Creates an AX12Position object from an angle in integer representation.

        get_angle_as_degrees() -> float:
            Returns the angle in degrees.

        get_raw_angle() -> int:
            Returns the raw angle.

        get_value_as_string() -> str:
            Returns the angle as a string in degrees.
    """
    MINIMUM_ANGLE_INT = 0
    MAXIMUM_ANGLE_INT = 1023

    MINIMUM_ANGLE_DEGREES = 0.0
    MAXIMUM_ANGLE_DEGREES = 300.0

    def __init__(self, raw_angle: int) -> None:
        """
        Initializes the AX12Position object with a raw angle.

        Args:
            raw_angle (int): The raw angle to set.
        """
        self.raw_angle = raw_angle

    @staticmethod
    def build_from_degrees(angle: int) -> 'AX12Position':
        """
        Creates an AX12Position object from an angle in degrees.

        Args:
            angle (float): The angle in degrees to convert to an AX12Position object.

        Returns:
            AX12Position: The created AX12Position object.

        Raises:
            ValueError: If the angle is not within the valid range.
        """
        if angle < AX12Position.MINIMUM_ANGLE_DEGREES or angle > AX12Position.MAXIMUM_ANGLE_DEGREES:
            raise ValueError(f"Angle value is not in the allowed range [{AX12Position.MINIMUM_ANGLE_DEGREES};{AX12Position.MAXIMUM_ANGLE_DEGREES}]")

        val = round((angle / AX12Position.MAXIMUM_ANGLE_DEGREES) * AX12Position.MAXIMUM_ANGLE_INT)
        return AX12Position(val)

    @staticmethod
    def build_from_int(angle: int) -> 'AX12Position':
        """
        Creates an AX12Position object from an angle in integer representation.

        Args:
            angle (int): The angle in integer representation to convert to an AX12Position object.

        Returns:
            AX12Position: The created AX12Position object.

        Raises:
            ValueError: If the angle is not within the valid range.
        """
        if angle < AX12Position.MINIMUM_ANGLE_INT or angle > AX12Position.MAXIMUM_ANGLE_INT:
            raise ValueError(f"Angle value is not in the allowed range [{AX12Position.MINIMUM_ANGLE_INT};{AX12Position.MAXIMUM_ANGLE_INT}]")

        return AX12Position(angle)

    def get_angle_as_degrees(self) -> float:
        """
        Returns the angle in degrees.

        Returns:
            float: The angle in degrees.
        """
        return AX12Position.MAXIMUM_ANGLE_DEGREES * (self.raw_angle / AX12Position.MAXIMUM_ANGLE_INT)

    def get_raw_angle(self) -> int:
        """
        Returns the raw angle.

        Returns:
            int: The raw angle.
        """
        return self.raw_angle

    def get_value_as_string(self) -> str:
        """
        Returns the angle as a string in degrees.

        Returns:
            str: The angle as a string in degrees.
        """
        return f"{self.get_angle_as_degrees():.2f}°"