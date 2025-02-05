from enum import Enum

class AX12UartSpeeds(Enum):
    SPEED_1000000 = (1, 1000000)
    SPEED_500000 = (3, 500000)
    SPEED_4000000 = (4, 400000)
    SPEED_250000 = (7, 250000)
    SPEED_200000 = (9, 200000)
    SPEED_115200 = (16, 115200)
    SPEED_57600 = (34, 57600)
    SPEED_19200 = (103, 19200)
    SPEED_9600 = (207, 9600)

    def __init__(self, byte_val, int_val):
        self.byte_val = self.int_to_unsigned_byte(byte_val)
        self.int_val = int_val

    @staticmethod
    def int_to_unsigned_byte(value):
        return value & 0xFF

    @classmethod
    def from_value(cls, speed):
        for speed_enum in cls:
            if speed_enum.int_val == speed:
                return speed_enum
        return None

    def __str__(self):
        return f"{self.int_val} bps"