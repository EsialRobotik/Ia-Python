import logging
import time

from smbus2 import SMBus

from ia.api.detection.ultrasound.srf import Srf

logger = logging.getLogger(__name__)

class Srf08(Srf):

    COMMAND_REGISTER = 0x00
    GAIN_REGISTER = 1
    RANGE_REGISTER = 2
    I2C_BUS = 1
    RANGING_US_COMMAND = 82
    FIRST_ECHO_HIGH_REGISTER = 2
    READ_TIMEOUT_S = 0.07
    POLL_INTERVAL_S = 0.001

    def __init__(self, desc: str, address: int, x: int, y: int, angle: int, threshold: int, window_size: int) -> None:
        super().__init__(desc, x, y, angle, threshold, window_size)
        # La datasheet SRF08 donne des adresses 8 bits (bit R/W inclus, ex: 0xE0).
        # smbus2 / Linux attendent une adresse 7 bits : on divise par 2.
        self.address = address >> 1 if address > 0x7F else address
        # Les adresses SRF08 >= 0x78 (7 bits) sont hors plage standard I2C : force requis.
        self._i2c_force = self.address > 0x77
        self.initalize()
        logger.info(
            f"Creating Srf08 object with address 0x{address:02X} -> 7-bit 0x{self.address:02X}, "
            f"x={x}, y={y}, angle={angle}, threshold={threshold}, force={self._i2c_force}."
        )

    def initalize(self) -> None:
        """
        Configure le SRF08 en I2C avec gain maximum et portée ~602 mm.
        """
        try:
            with SMBus(self.I2C_BUS) as bus:
                bus.write_byte_data(self.address, self.GAIN_REGISTER, 13, force=self._i2c_force)
                bus.write_byte_data(self.address, self.RANGE_REGISTER, 13, force=self._i2c_force)

            logger.info(
                "SRF08 initialise a l'adresse 0x%02X (gain=%d, range_reg=%d ~602mm)",
                self.address,
                0x1F,
                13,
            )
        except Exception as error:
            logger.exception("Echec d'initialisation du SRF08 a l'adresse 0x%02X", self.address)
            raise error

    def get_software_version(self) -> int:
        """
        Retourne la version du logiciel embarqué du SRF08.
        La lecture du registre 0x00 (COMMAND_REGISTER) renvoie le numéro de version.
        Returns:
            int: Numéro de version du firmware (ex: 2 pour SRF08, 6 pour SRF10).
        """
        with SMBus(self.I2C_BUS) as bus:
            version = bus.read_byte_data(self.address, self.COMMAND_REGISTER, force=self._i2c_force)
        logger.info("SRF08 0x%02X - version firmware : %d", self.address, version)
        return version

    def get_distance(self) -> int:
        """
        Lance une mesure SRF08 et renvoie la distance du 1er echo en mm.
        Utilise la mesure temporelle pour une conversion plus precise.
        """
        with SMBus(self.I2C_BUS) as bus:
            bus.write_byte_data(self.address, self.COMMAND_REGISTER, self.RANGING_US_COMMAND, force=self._i2c_force)
            time.sleep(0.065)  # Délai initial pour que le capteur commence la mesure

            timeout_at = time.monotonic() + self.READ_TIMEOUT_S
            while True:
                try:
                    # Pendant la mesure, le SRF08 NAK → OSError traitée comme "occupé"
                    if bus.read_byte_data(self.address, self.COMMAND_REGISTER, force=self._i2c_force) != 0xFF:
                        break
                except OSError:
                    pass
                if time.monotonic() >= timeout_at:
                    return 10000
                time.sleep(self.POLL_INTERVAL_S)

            tof_high = bus.read_byte_data(self.address, self.FIRST_ECHO_HIGH_REGISTER, force=self._i2c_force)
            tof_low = bus.read_byte_data(self.address, self.FIRST_ECHO_HIGH_REGISTER + 1, force=self._i2c_force)
            tof_us = (tof_high << 8) | tof_low

        tof_ms = tof_us / 1000.0
        logger.debug("SRF08 0x%02X - ToF: %d us -> %.3f ms - High = %d - Low = %d", self.address, tof_us, tof_ms, tof_high, tof_low)
        return int(round((tof_ms * 343.0) / 2.0))