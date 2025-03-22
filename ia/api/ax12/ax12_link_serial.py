import logging
import threading

import serial

from ia.api.ax12.ax12_exception import AX12Exception
from ia.api.ax12.ax12_link_exception import AX12LinkException
from ia.api.ax12.ax12_servo import AX12Servo
from ia.api.ax12.enums.ax12_address import AX12Address


class AX12LinkSerial:
    """
    The AX12LinkSerial class manages serial communication with AX12 servomotors.

    Attributes:
        dtr_enabled (bool): Indicates if DTR (Data Terminal Ready) is enabled.
        rts_enabled (bool): Indicates if RTS (Request to Send) is enabled.
        lecture (bytearray): Buffer for data read from the serial port.
        serial (serial.Serial): Serial connection object.

    Methods:
        __init__(serialPort: str, baud_rate: int): Initializes the serial connection with the specified parameters.
        send_command(cmd: bytes) -> bytearray: Sends a command to the servomotor and returns the response.
        enable_dtr(enable: bool) -> None: Enables or disables the DTR (Data Terminal Ready) signal.
        enable_rts(enable: bool) -> None: Enables or disables the RTS (Request to Send) signal.
        is_dtr_enabled() -> bool: Checks if the DTR (Data Terminal Ready) signal is enabled.
        is_rts_enabled() -> bool: Checks if the RTS (Request to Send) signal is enabled.
    """

    def __init__(self, serial_port: str, baud_rate: int) -> None:
        """
        Initializes the serial connection with the specified parameters.

        Args:
            serial_port (str): The serial port to use for the connection.
            baud_rate (int): The baud rate for the serial communication.

        Raises:
            AX12Exception: If an error occurs during the initialization of the serial port.
        """
        self.dtr_enabled = False
        self.rts_enabled = False
        self.lecture = bytearray()
        self.logger = logging.getLogger(__name__)
        try:
            self.serial = serial.Serial(
                port=serial_port,
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
                raise AX12Exception("Error initializing serial port: " + str(e))
        
    def send_command(self, cmd: bytes) -> bytearray:
        """
        Sends a command to the servomotor and returns the response.

        Args:
            cmd (bytes): The command to send to the servomotor.

        Returns:
            bytearray: The response from the servomotor.

        Raises:
            AX12Exception: If an error occurs while sending the command or reading the response.
        """
        response = bytearray()
        try:
            self.serial.write(cmd)
            while True:
                # Read data from the serial port
                data = self.serial.read()
                if not data:
                    break
                response.extend(data)
        except serial.SerialException as e:
            raise AX12Exception("Error sending command: " + str(e))
        return response
    
    def enable_dtr(self, enable: bool) -> None:
        """
        Enables or disables the DTR (Data Terminal Ready) signal.

        Args:
            enable (bool): True to enable DTR, False to disable.
        """
        self.serial.dtr = enable
        self.dtr_enabled = enable

    def enable_rts(self, enable: bool) -> None:
        """
        Enables or disables the RTS (Request to Send) signal.

        Args:
            enable (bool): True to enable RTS, False to disable.
        """
        self.serial.rts = enable
        self.rts_enabled = enable

    def is_dtr_enabled(self) -> bool:
        """
        Checks if the DTR (Data Terminal Ready) signal is enabled.

        Returns:
            bool: True if DTR is enabled, False otherwise.
        """
        return self.dtr_enabled

    def is_rts_enabled(self) -> bool:
        """
        Checks if the RTS (Request to Send) signal is enabled.

        Returns:
            bool: True if RTS is enabled, False otherwise.
        """
        return self.rts_enabled

    def disable_ax12_and_shutdown_link(self) -> None:
        """
        Disables the AX12 torque and shuts down the link.

        Raises:
            AX12Exception: If an error occurs while disabling the torque or closing the link.
        """
        with threading.Lock():
            ax = AX12Servo(AX12Address.AX12_ADDRESS_BROADCAST.value, self)
            try:
                ax.disable_torque()
                self.serial.close()
            except (IOError, AX12LinkException, AX12Exception) as e:
                self.logger.error(f"Error disabling AX12 torque or shutting down link: {e}")