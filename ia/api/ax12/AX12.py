import logging

from ia.api.ax12 import AX12LinkSerial, AX12LinkException, AX12Exception
from ia.api.ax12.enums import AX12Register, AX12Instr, AX12Error, AX12Address


class AX12:
    """
    The AX12 class provides an interface to control AX12 servomotors.

    Attributes:
        address (int): The address of the AX12 servomotor.
        serial_link (AX12LinkSerial): The serial link used for communication with the servomotor.

    Methods:
        __init__(address: int, serialLink: AX12LinkSerial): Initializes the AX12 instance with the specified address and serial link.
        get_address() -> int: Returns the address of the servomotor.
        set_servo_speed(spd: int) -> None: Sets the speed of the servomotor.
        set_servo_position(pos: int) -> None: Sets the position of the servomotor.
        write(register: AX12Register, value: int) -> None: Writes a value to a specified register.
    """

    def __init__(self, address: int, serial_link: AX12LinkSerial) -> None:
        """
        Initializes the AX12 instance with the specified address and serial link.

        Args:
            address (int): The address of the AX12 servomotor.
            serialLink (AX12LinkSerial): The serial link used for communication with the servomotor.
        """
        self.address = address
        self.serial_link = serial_link
        self.logger =  logging.getLogger(__name__)

    def get_address(self) -> int:
        """
        Returns the address of the servomotor.

        Returns:
            int: The address of the servomotor.
        """
        return self.address
    
    def set_servo_speed(self, spd: int) -> None:
        """
        Sets the speed of the servomotor.

        Args:
            spd (int): The speed to set, must be between 0 and 2047.

        Raises:
            AX12LinkException: If the speed is out of the valid range (0-2047).
        """
        if spd < 0 or spd > 2047:
            raise AX12LinkException(f"Speed must be between 0 and 2047: {spd}")
        self.write(AX12Register.AX12_RAM_MOVING_SPEED, spd)

    def set_servo_position(self, pos: int) -> None:
        """
        Sets the position of the servomotor.

        Args:
            pos (int): The position to set, must be between 0 and 1023.

        Raises:
            AX12LinkException: If the position is out of the valid range (0-1023).
        """
        if pos < 0 or pos > 1023:
            raise AX12LinkException(f"Position must be between 0 and 1023: {pos}")
        self.write(AX12Register.AX12_RAM_GOAL_POSITION, pos)
    
    def write(self, register: AX12Register, value: int) -> None:
        """
        Writes a value to a specified register.

        Args:
            register (AX12Register): The register to write to.
            value (int): The value to write, must be between 0 and 65535.

        Raises:
            AX12LinkException: If the register is not writable or the value is out of the valid range (0-65535).
        """
        if not register.writable:
            raise AX12LinkException(f"The register {register} is not writable")
        if value < 0 or value > 65535:
            raise AX12LinkException(f"Value must be between 0 and 65535: {value}")
        
        params = bytearray(register.size + 1)
        params[0] = register.regi
        for i in range(register.size):
            params[i + 1] = (value >> (i * 8)) & 0xFF

        status = self.send_request(AX12Instr.AX12_INSTR_WRITE_DATA, params)
        if len(status) == 0 and self.address != self.AX12_ADDRESS_BROADCAST:
            raise AX12Exception("AX12_ERR_NO_RESPONSE")
        
    def send_request(self, instruction: AX12Instr, params: bytearray) -> bytearray:
        """
        Sends a request to the AX12 device with the specified instruction and parameters.
        Args:
            instruction (AX12Instr): The instruction to send to the AX12 device.
            *params (bytes): The parameters to include with the instruction.
        Returns:
            bytearray: The response from the AX12 device.
        Raises:
            AX12Exception: If the number of parameters is outside the allowed range,
                           if the response packet is invalid, or if there are errors
                           in the response from the AX12 device.
        """

        if instruction.min_param_count != -1 and len(params) < instruction.min_param_count:
            raise AX12Exception(f"{instruction} attend au moins {instruction.min_param_count} paramètre(s). {len(params)} reçu(s)")
        if instruction.max_param_count != -1 and len(params) > instruction.max_param_count:
            raise AX12Exception(f"{instruction} attend au plus {instruction.max_param_count} paramètre(s). {len(params)} reçu(s)")

        buffer = bytearray(len(params) + 6)
        pos = 0
        checksum = 0
        buffer[pos] = self.int_to_unsigned_byte(0xFF)[0]
        pos += 1
        buffer[pos] = self.int_to_unsigned_byte(0xFF)[0]
        pos += 1
        checksum += self.address
        buffer[pos] = self.address
        pos += 1
        checksum += self.int_to_unsigned_byte(len(params) + 2)[0]
        buffer[pos] = self.int_to_unsigned_byte(len(params) + 2)[0]
        pos += 1
        checksum += instruction.instr
        buffer[pos] = instruction.instr
        pos += 1
        for param in params:
            buffer[pos] = param
            checksum += param
            pos += 1
        checksum = (~checksum) & 0xFF
        buffer[pos] = self.int_to_unsigned_byte(checksum)[0]

        response = self.serial_link.send_command(buffer)
        if len(response) > 0:
            validation = self.validate_packet(response, self.address)
            if validation is not None:
                raise AX12Exception(validation)
            errors = self.extract_errors(response[4])
            if len(errors) > 0:
                raise AX12Exception("Erreur de l'AX12", errors)

        return response
    
    def read_servo_position(self) -> int:
        """
        Reads the current position of the servo.
        Returns:
            int: The current position of the servo as an integer.
        """

        return self.read(AX12Register.AX12_RAM_PRESENT_POSITION)

    def set_led(self, on: bool) -> None:
        """
        Sets the LED state on the AX12 device.
        Args:
            on (bool): If True, turns the LED on. If False, turns the LED off.
        Returns:
            None
        """

        self.write(AX12Register.AX12_RAM_LED, 1 if on else 0)

    def write_uart_speed(self, speed: int) -> None:
        """
        Sets the UART communication speed for the AX12 servo.
        Parameters:
        speed (int): The desired UART speed to set. This value is written to the AX12 EEPROM baud rate register.
        Returns:
        None
        """

        self.write(AX12Register.AX12_EEPROM_BAUD_RATE, speed)

    def write_address(self, address: int) -> None:
        """
        Writes a new address to the AX12 device.
        This method updates the address of the AX12 device by writing to the specified register.
        It first checks if the provided address is within the valid range.
        Args:
            address (int): The new address to be written to the AX12 device.
        Raises:
            ValueError: If the address is out of the valid range.
        """

        self.check_address_range(address)
        self.write(AX12Register.AX12_EEPROM_ID, address)
        self.address = address

    def set_cw_compliance_margin(self, compliance: int) -> None:
        """
        Set the clockwise compliance margin for the AX12 servo.
        The compliance margin is the error between the goal position and the 
        present position in which the servo will not exert torque. This function 
        sets the clockwise compliance margin.
        Parameters:
        compliance (int): The compliance margin value, must be between 0 and 254.
        Raises:
        AX12LinkException: If the compliance value is not within the range 0 to 254.
        """

        if compliance < 0 or compliance > 254:
            raise AX12LinkException(f"La marge de conformité CW doit être comprise entre 0 et 254 : {compliance}")
        self.write(AX12Register.AX12_RAM_CW_COMPLIANCE_MARGIN, compliance)

    def set_ccw_compliance_margin(self, compliance: int) -> None:
        """
        Sets the counter-clockwise (CCW) compliance margin for the AX-12 servo.
        The compliance margin is the error between the goal position and the 
        present position that is allowed before any action is taken. A higher 
        compliance margin means the servo will be less sensitive to small 
        positional errors.
        Args:
            compliance (int): The compliance margin value, which must be between 
                              0 and 254 inclusive.
        Raises:
            AX12LinkException: If the compliance value is not within the valid range.
        """

        if compliance < 0 or compliance > 254:
            raise AX12LinkException(f"La marge de conformité CCW doit être comprise entre 0 et 254 : {compliance}")
        self.write(AX12Register.AX12_RAM_CCW_COMPLIANCE_MARGIN, compliance)

    def set_cw_compliance_slope(self, value: int) -> None:
        """
        Sets the clockwise compliance slope of the AX-12 servo.
        The compliance slope is used to control the torque near the goal position.
        A higher value means a softer response, while a lower value means a stiffer response.
        Args:
            value (int): The compliance slope value, must be between 0 and 254 inclusive.
        Raises:
            AX12LinkException: If the value is not within the valid range (0-254).
        """

        if value < 0 or value > 254:
            raise AX12LinkException(f"La valeur doit être comprise entre 0 et 254 : {value}")
        self.write(AX12Register.AX12_RAM_CW_COMPLIANCE_SLOPE, value)

    def set_ccw_compliance_slope(self, value: int) -> None:
        """
        Set the counter-clockwise compliance slope for the AX-12 servo.
        The compliance slope is a parameter that determines the level of compliance
        (flexibility) of the servo when it encounters resistance. A higher value 
        means more compliance (more flexibility), while a lower value means less 
        compliance (more rigidity).
        Parameters:
        value (int): The compliance slope value to set, which must be between 0 and 254.
        Raises:
        AX12LinkException: If the provided value is not within the range of 0 to 254.
        """

        if value < 0 or value > 254:
            raise AX12LinkException(f"La valeur doit être comprise entre 0 et 254 : {value}")
        self.write(AX12Register.AX12_RAM_CCW_COMPLIANCE_SLOPE, value)

    def disable_torque(self) -> None:
        """
        Disables the torque of the AX12 servo motor.
        This method writes a value of 0 to the AX12_RAM_TORQUE_ENABLE register,
        effectively disabling the torque of the servo motor.
        """

        self.write(AX12Register.AX12_RAM_TORQUE_ENABLE, 0)

    @staticmethod
    def validate_packet(packet: bytearray, ax12_addr: int) -> (str | None):
        """
        Validates a packet for the AX12 protocol.
        Args:
            packet (bytearray): The packet to validate.
            ax12_addr (int): The expected AX12 address.
        Returns:
            str | None: An error message if the packet is invalid, otherwise None.
        Errors:
            - "La taille minimale du packet n'est pas valide ({len(packet)})": The packet is too short.
            - "Le header du paquet n'est pas valide": The packet header is invalid.
            - "Le paquet ne contient pas le bon id de l'actions": The packet does not contain the correct action ID.
            - "La taille de la charge utile mentionnée par le paquet ne correspond pas à la taille reelle": The payload size mentioned in the packet does not match the actual size.
            - "Le checksum n'est pas valide": The checksum is invalid.
        """

        if len(packet) < 6:
            return f"La taille minimale du packet n'est pas valide ({len(packet)})"

        if packet[0] != packet[1] or packet[0] != AX12.int_to_unsigned_byte(0xFF)[0]:
            return "Le header du paquet n'est pas valide"

        if packet[2] != ax12_addr:
            return "Le paquet ne contient pas le bon id de l'action"

        l = packet[3]
        if l < 2 or l > len(packet) - 2:
            return "La taille de la charge utile mentionnée par le paquet ne correspond pas à la taille reelle"

        l -= 3
        cc = packet[2]
        cc += packet[3]
        cc += packet[4]
        while l >= 0:
            cc += packet[5 + l]
            l -= 1

        if (~cc & 0xFF) != packet[-1]:
            return "Le checksum n'est pas valide"

        return None
    
    @staticmethod
    def extract_errors(register_value: int) -> list:
        """
        Extracts error codes from a given register value.
        This function takes an integer representing a register value and extracts
        individual error codes by checking each bit of the register value. If a bit
        is set (i.e., equals 1), it appends the corresponding error code to the list
        of errors.
        Args:
            register_value (int): The register value from which to extract error codes.
        Returns:
            list: A list of AX12Error objects representing the extracted error codes.
        """

        errors = []
        for i in range(7):
            if (register_value >> i) & 0x01 == 0x01:
                errors.append(AX12Error(i))
        return errors
    
    def read(self, register: AX12Register) -> int:
        """
        Reads data from a specified register of the AX12 device.
        Args:
            register (AX12Register): The register from which to read data. The register object should contain
                                     the register address (`regi`) and the size of the data to read (`size`).
        Returns:
            int: The value read from the specified register.
        Raises:
            AX12Exception: If there is no response from the device or if the payload size does not match the expected size.
        """

        params = bytearray(2)
        params[0] = register.regi
        params[1] = register.size
        status = self.send_request(AX12Instr.AX12_INSTR_READ_DATA, params)
        if len(status) == 0:
            raise AX12Exception(AX12Error.AX12_ERR_NO_RESPONSE.value)
        
        payload = self.extract_payload(status)
        if len(payload) != register.size:
            raise AX12Exception("La taille de la payload n'est pas celle attendue", AX12Error.AX12_ERR_INVALID_RESPONSE)
        
        value = 0
        for i in range(len(payload)):
            value += payload[i] << (i * 8)
        
        return value

    @staticmethod
    def extract_payload(packet: bytearray) -> bytearray:
        """
        Extracts the payload from a given packet.
        The payload is extracted by removing the header and checksum bytes from the packet.
        The length of the payload is determined by the third byte of the packet minus 2.
        Args:
            packet (bytearray): The packet from which to extract the payload.
        Returns:
            bytearray: The extracted payload. If the packet is empty, returns an empty bytearray.
        """

        if len(packet) == 0:
            return bytearray()
        
        taille = packet[3] - 2
        params = bytearray(taille)
        for i in range(taille):
            params[i] = packet[5 + i]
        
        return params
    
    @staticmethod
    def check_address_range(address: int) -> None:
        """
        Check if the given address is within the valid range for AX12 devices.
        Parameters:
        address (int): The address to check.
        Raises:
        ValueError: If the address is not within the valid range or is not the broadcast address.
        Valid address range:
        - AX12Address.AX12_ADDRESS_MIN to AX12Address.AX12_ADDRESS_MAX
        - AX12Address.AX12_ADDRESS_BROADCAST
        """

        if address == AX12Address.AX12_ADDRESS_BROADCAST.value:
            return
        if address < AX12Address.AX12_ADDRESS_MIN.value or address > AX12Address.AX12_ADDRESS_MAX.value:
            raise ValueError(f"L'adresse de l'AX12 doit être contenue dans la plage [{AX12Address.AX12_ADDRESS_MIN} ~ {AX12Address.AX12_ADDRESS_MAX}] ou correspondre à l'adresse de BroadCast {AX12Address.AX12_ADDRESS_BROADCAST}. Obtenu : {address}")

    @staticmethod
    def int_to_unsigned_byte(value: int) -> bytes:
        """
        Convert an integer to an unsigned byte.
        Args:
            value (int): The integer value to convert. Must be in the range 0-255.
        Returns:
            bytes: A bytes object representing the unsigned byte.
        Raises:
            OverflowError: If the integer is out of the range 0-255.
        """

        return value.to_bytes(1, byteorder='big', signed=False)
    
    @staticmethod
    def unsigned_byte_to_int(byte_val: bytes) -> int:
        """
        Convert an unsigned byte to an integer.
        Args:
            byte_val (bytes): A byte value to be converted.
        Returns:
            int: The integer representation of the unsigned byte.
        """

        return int.from_bytes(byte_val, byteorder='big', signed=False)