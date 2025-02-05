from enum import Enum

class AX12Address(Enum):
    AX12_ADDRESS_MIN = 0
    AX12_ADDRESS_MAX = 253
    AX12_ADDRESS_BROADCAST = 254 
    AX12_ADDRESS_BROADCAST_BYTE = AX12_ADDRESS_BROADCAST.to_bytes(1, byteorder='big', signed=False)