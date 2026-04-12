import logging
import time

import serial


class SerialPort:
    """Wrapper minimal autour de pyserial pour communiquer avec un actionneur."""

    def __init__(self, port: str, baud_rate: int) -> None:
        self.logger = logging.getLogger(__name__)
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=0.05
            )
            self.serial.dtr = False
            self.serial.rts = False
            self.serial.open()
        except serial.SerialException as e:
            if str(e) == 'Port is already open.':
                self.serial.close()
                self.serial.open()
            else:
                raise Exception(f"Error initializing serial port: {e}")

    def send(self, command: str, wait_response: bool = False, timeout: float = None) -> str:
        """Envoie une commande texte sur le port serie, retourne la reponse si demandee."""
        response = bytearray()
        try:
            self.serial.write(command.encode())
            self.serial.write(b"\n")
            self.serial.flush()

            write_time = time.time()
            while wait_response:
                data = self.serial.read()
                if not data and (len(response) > 0 or time.time() - write_time > (timeout or 1.0)):
                    break
                response.extend(data)
        except serial.SerialException as e:
            raise Exception(f"Error sending command: {e}")
        return response.decode(errors='replace').strip() if response else ""