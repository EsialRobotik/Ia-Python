from enum import Enum

class AX12Instr(Enum):
    AX12_INSTR_READ_DATA = (0x02, 2, 2)
    AX12_INSTR_WRITE_DATA = (0x03, 2, 100)

    def __init__(self, instr: int, min_param_count: int, max_param_count: int) -> None:
        self.instr = instr & 0xFF
        self.min_param_count = min_param_count
        self.max_param_count = max_param_count

# Example usage
# read_data_instr = AX12Instr(*AX12Instr.AX12_INSTR_READ_DATA)
# write_data_instr = AX12Instr(*AX12Instr.AX12_INSTR_WRITE_DATA)