import math

class AX12Position:
    MINIMUM_ANGLE_INT = 0
    MAXIMUM_ANGLE_INT = 1023

    MINIMUM_ANGLE_DEGREES = 0.0
    MAXIMUM_ANGLE_DEGREES = 300.0

    def __init__(self, raw_angle):
        self.raw_angle = raw_angle

    @staticmethod
    def build_from_degrees(angle):
        if angle < AX12Position.MINIMUM_ANGLE_DEGREES or angle > AX12Position.MAXIMUM_ANGLE_DEGREES:
            raise ValueError(f"Angle value is not in the allowed range [{AX12Position.MINIMUM_ANGLE_DEGREES};{AX12Position.MAXIMUM_ANGLE_DEGREES}]")
        
        val = round((angle / AX12Position.MAXIMUM_ANGLE_DEGREES) * AX12Position.MAXIMUM_ANGLE_INT)
        return AX12Position(val)

    @staticmethod
    def build_from_int(angle):
        if angle < AX12Position.MINIMUM_ANGLE_INT or angle > AX12Position.MAXIMUM_ANGLE_INT:
            raise ValueError(f"Angle value is not in the allowed range [{AX12Position.MINIMUM_ANGLE_INT};{AX12Position.MAXIMUM_ANGLE_INT}]")
        
        return AX12Position(angle)

    def get_angle_as_degrees(self):
        return AX12Position.MAXIMUM_ANGLE_DEGREES * (self.raw_angle / AX12Position.MAXIMUM_ANGLE_INT)

    def get_raw_angle(self):
        return self.raw_angle

    def get_value_as_string(self):
        return f"{self.get_angle_as_degrees():.2f}°"