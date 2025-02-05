from enum import Enum

class AX12Register(Enum):
    AX12_EEPROM_ID = (0x03, 1, True)
    AX12_EEPROM_BAUD_RATE = (0x04, 1, True)
    # 0x13 reserved
    AX12_RAM_TORQUE_ENABLE = (0x18, 1, True)
    AX12_RAM_LED = (0x19, 1, True)
    AX12_RAM_CW_COMPLIANCE_MARGIN = (0x1A, 1, True)
    AX12_RAM_CCW_COMPLIANCE_MARGIN = (0x1B, 1, True)
    AX12_RAM_CW_COMPLIANCE_SLOPE = (0x1C, 1, True)
    AX12_RAM_CCW_COMPLIANCE_SLOPE = (0x1D, 1, True)
    AX12_RAM_GOAL_POSITION = (0x1E, 2, True)
    AX12_RAM_MOVING_SPEED = (0x20, 2, True)
    AX12_RAM_PRESENT_POSITION = (0x24, 2, False)

    def __init__(self, regi, size, writable):
        self.regi = self.int_to_unsigned_byte(regi)
        self.size = size
        self.writable = writable

    @staticmethod
    def int_to_unsigned_byte(value):
        return value & 0xFF