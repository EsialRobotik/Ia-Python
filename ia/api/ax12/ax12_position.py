class AX12Position:
    """
    Represents the angle of an AX12 with usefull methods to manipuilates its value
    """

    MINIMUM_ANGLE_RAW = 0
    MAXIMUM_ANGLE_RAW = 1023

    MINIMUM_ANGLE_DEGREES = 0.
    MAXIMUM_ANGLE_DEGREES = 300.

    def __init__(self, rawAngle: int = 0):
        """
        The raw value must be between [0; 1023] and is mapped over [0; 300] degrees
        """
        self.__setRawAngle(rawAngle)

    def __setRawAngle(self, rawAngle: int):
        if rawAngle > AX12Position.MAXIMUM_ANGLE_RAW:
            raise Exception(f"Raw angle is too high : {rawAngle} > {AX12Position.MAXIMUM_ANGLE_RAW}")
        if rawAngle < AX12Position.MINIMUM_ANGLE_RAW:
            raise Exception(f"Raw angle is too high : {rawAngle} < {AX12Position.MINIMUM_ANGLE_RAW}")
        self.rawAngle = rawAngle
    
    def getRawAngle(self) -> int:
        return self.rawAngle

    def getAngleAsDegrees(self) -> float:
        return (float(self.rawAngle) / float(AX12Position.MAXIMUM_ANGLE_RAW)) * AX12Position.MAXIMUM_ANGLE_DEGREES
    
    @staticmethod
    def buildFromDegrees(angle: float) -> 'AX12Position':
        if angle > AX12Position.MAXIMUM_ANGLE_DEGREES:
            raise Exception(f"Angle is too high : {angle}. Maximum is {AX12Position.MAXIMUM_ANGLE_DEGREES}")
        if angle < AX12Position.MINIMUM_ANGLE_DEGREES:
            raise Exception(f"Angle is too low : {angle}. Minimum is {AX12Position.MINIMUM_ANGLE_DEGREES}")
        return AX12Position(int(float(AX12Position.MAXIMUM_ANGLE_RAW) * angle / AX12Position.MAXIMUM_ANGLE_DEGREES))