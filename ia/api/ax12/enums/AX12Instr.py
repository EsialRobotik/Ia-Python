class AX12Instr:
    AX12_INSTR_READ_DATA = (0x02, 2, 2)
    AX12_INSTR_WRITE_DATA = (0x03, 2, 100)

    def __init__(self, instr, min_param_count, max_param_count):
        self.instr = self.int_to_unsigned_byte(instr)
        self.min_param_count = min_param_count
        self.max_param_count = max_param_count

    @staticmethod
    def int_to_unsigned_byte(value):
        return value & 0xFF

# Example usage
# read_data_instr = AX12Instr(*AX12Instr.AX12_INSTR_READ_DATA)
# write_data_instr = AX12Instr(*AX12Instr.AX12_INSTR_WRITE_DATA)