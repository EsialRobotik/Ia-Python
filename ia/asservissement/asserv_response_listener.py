import logging

import cbor2
import crc

logger = logging.getLogger(__name__)

class AsservResponseListener:
    def __init__(self):
        self.syncword = 0xDEADBEEF
        self.state = _CborState_synchroLoopkup()
        self.payloads = []

    def push_byte(self, byte: bytes):
        (new_state, payload) = self.state.push_byte(byte)
        logger.debug(f"Received byte: {byte}, new_state: {new_state}, payload: {payload}")
        if new_state == "state_decode":
            self.state = _CborState_decode()
        elif new_state == "state_synchroLookup":
            self.state = _CborState_synchroLoopkup()

        if payload != None:
            self.payloads.append(payload)

    def pop_payload(self) -> dict:
        payload = self.payloads.pop(0)
        cbor_msg = cbor2.loads(payload)
        res = {
            "x": cbor_msg[0],
            "y": cbor_msg[1],
            "theta": cbor_msg[2],
            "cmd_id": cbor_msg[3],
            "status": cbor_msg[4],
            "pending": cbor_msg[5],
            "motor_left": cbor_msg[6],
            "motor_right": cbor_msg[7]
        }
        return res

    def get_nb_payload(self) -> int:
        return len(self.payloads)


class _CborState_synchroLoopkup:
    def __init__(self):
        self.syncword = 0xDEADBEEF
        self.reset()

    def reset(self):
        self.nb_byte_of_syncword_found = 0

    def _byteInInt(self, number, i):
        return (number & (0xff << (i * 8))) >> (i * 8)

    def push_byte(self, byte):
        if byte == self._byteInInt(self.syncword, self.nb_byte_of_syncword_found):
            self.nb_byte_of_syncword_found = self.nb_byte_of_syncword_found + 1
        else:
            self.nb_byte_of_syncword_found = 0

        if self.nb_byte_of_syncword_found == 4:
            #  Synchro found
            self.reset()
            return ("state_decode", None)
        return (None, None)


class _CborState_decode:
    def __init__(self):
        self.reset()

    def reset(self):
        self.size = []
        self.size_decoded = 0
        self.crc = []
        self.crc_decoded = 0
        self.payload = bytearray()

    def push_byte(self, byte):
        if len(self.crc) < 4:
            self.crc.append(byte)
            if len(self.crc) == 4:
                self.crc_decoded = int.from_bytes(self.crc, byteorder='little')
        elif len(self.size) < 4:
            self.size.append(byte)
            if len(self.size) == 4:
                self.size_decoded = int.from_bytes(self.size, byteorder='little')
        elif len(self.payload) < self.size_decoded:
            self.payload.append(byte)
            if len(self.payload) == self.size_decoded:
                calculator = crc.Calculator(crc.Crc32.CRC32)
                crc_computed = calculator.checksum(self.payload)
                if crc_computed == self.crc_decoded:
                    return ("state_synchroLookup", self.payload)
                else:
                    return ("state_synchroLookup", None)
        return (None, None)
